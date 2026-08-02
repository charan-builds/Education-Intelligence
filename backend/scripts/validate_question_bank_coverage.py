from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import asdict, dataclass
from typing import Any

from sqlalchemy import text

from app.core.config import get_settings
from app.infrastructure.database import open_tenant_session


REQUIRED_PER_DIFFICULTY = 10
DIFFICULTIES = ("easy", "medium", "hard")


@dataclass(frozen=True)
class CoverageGap:
    topic_id: int
    topic_name: str
    subtopic_path: str
    depth: int | None
    easy: int
    medium: int
    hard: int
    missing_easy: int
    missing_medium: int
    missing_hard: int

    @property
    def total_missing(self) -> int:
        return self.missing_easy + self.missing_medium + self.missing_hard


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate question bank coverage. Each topic/subtopic must have at "
            f"least {REQUIRED_PER_DIFFICULTY} active questions per difficulty."
        )
    )
    parser.add_argument("--tenant-id", type=int, default=get_settings().default_tenant_id)
    parser.add_argument("--minimum", type=int, default=REQUIRED_PER_DIFFICULTY)
    parser.add_argument("--include-inactive", action="store_true", help="count inactive question versions too")
    parser.add_argument("--all", action="store_true", help="print passing topics as well as failing topics")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    return parser


async def _column_exists(session: Any, *, table_name: str, column_name: str) -> bool:
    result = await session.execute(
        text(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = ANY (current_schemas(false))
                  AND table_name = :table_name
                  AND column_name = :column_name
            )
            """
        ),
        {"table_name": table_name, "column_name": column_name},
    )
    return bool(result.scalar_one())


async def _coverage_rows(
    session: Any,
    *,
    tenant_id: int,
    minimum: int,
    include_inactive: bool,
) -> list[CoverageGap]:
    has_is_active = await _column_exists(session, table_name="questions", column_name="is_active")
    has_difficulty_label = await _column_exists(session, table_name="questions", column_name="difficulty_label")

    active_predicate = ""
    if has_is_active and not include_inactive:
        active_predicate = "AND q.is_active = true"

    difficulty_expr = "q.difficulty_label"
    if not has_difficulty_label:
        difficulty_expr = (
            "CASE q.difficulty::text "
            "WHEN '1' THEN 'easy' "
            "WHEN '2' THEN 'medium' "
            "WHEN '3' THEN 'hard' "
            "ELSE q.difficulty::text END"
        )

    stmt = text(
        f"""
        WITH coverage AS (
            SELECT
                t.id AS topic_id,
                t.name AS topic_name,
                COALESCE(NULLIF(t.graph_path, ''), t.name) AS subtopic_path,
                t.depth AS depth,
                COUNT(q.id) FILTER (WHERE {difficulty_expr} = 'easy') AS easy,
                COUNT(q.id) FILTER (WHERE {difficulty_expr} = 'medium') AS medium,
                COUNT(q.id) FILTER (WHERE {difficulty_expr} = 'hard') AS hard
            FROM topics t
            LEFT JOIN questions q
                ON q.topic_id = t.id
                {active_predicate}
            WHERE t.tenant_id = :tenant_id
            GROUP BY t.id, t.name, t.graph_path, t.depth
        )
        SELECT
            topic_id,
            topic_name,
            subtopic_path,
            depth,
            easy,
            medium,
            hard,
            GREATEST(:minimum - easy, 0) AS missing_easy,
            GREATEST(:minimum - medium, 0) AS missing_medium,
            GREATEST(:minimum - hard, 0) AS missing_hard
        FROM coverage
        ORDER BY subtopic_path ASC, topic_id ASC
        """
    )
    result = await session.execute(stmt, {"tenant_id": tenant_id, "minimum": minimum})
    rows = result.mappings().all()
    return [
        CoverageGap(
            topic_id=int(row["topic_id"]),
            topic_name=str(row["topic_name"]),
            subtopic_path=str(row["subtopic_path"]),
            depth=int(row["depth"]) if row["depth"] is not None else None,
            easy=int(row["easy"] or 0),
            medium=int(row["medium"] or 0),
            hard=int(row["hard"] or 0),
            missing_easy=int(row["missing_easy"] or 0),
            missing_medium=int(row["missing_medium"] or 0),
            missing_hard=int(row["missing_hard"] or 0),
        )
        for row in rows
    ]


def _print_json(*, tenant_id: int, minimum: int, rows: list[CoverageGap], gaps: list[CoverageGap]) -> None:
    print(
        json.dumps(
            {
                "tenant_id": tenant_id,
                "minimum_per_difficulty": minimum,
                "topic_count": len(rows),
                "missing_topic_count": len(gaps),
                "missing_topics": [asdict(row) | {"total_missing": row.total_missing} for row in gaps],
            },
            indent=2,
        )
    )


def _print_table(*, tenant_id: int, minimum: int, rows: list[CoverageGap], gaps: list[CoverageGap], show_all: bool) -> None:
    visible_rows = rows if show_all else gaps
    print(f"Question bank coverage tenant_id={tenant_id} minimum_per_difficulty={minimum}")
    print(f"topics_checked={len(rows)} missing_topics={len(gaps)}")
    if not visible_rows:
        print("OK: every topic/subtopic meets coverage.")
        return

    header = (
        "topic_id  depth  easy  medium  hard  "
        "missing_easy  missing_medium  missing_hard  subtopic_path"
    )
    print(header)
    print("-" * len(header))
    for row in visible_rows:
        print(
            f"{row.topic_id:<8}  "
            f"{'' if row.depth is None else row.depth:<5}  "
            f"{row.easy:<4}  "
            f"{row.medium:<6}  "
            f"{row.hard:<4}  "
            f"{row.missing_easy:<12}  "
            f"{row.missing_medium:<14}  "
            f"{row.missing_hard:<12}  "
            f"{row.subtopic_path}"
        )


async def _run(args: argparse.Namespace) -> int:
    if args.minimum < 1:
        raise SystemExit("--minimum must be at least 1")

    async with open_tenant_session(tenant_id=args.tenant_id, role="admin") as session:
        rows = await _coverage_rows(
            session,
            tenant_id=args.tenant_id,
            minimum=args.minimum,
            include_inactive=args.include_inactive,
        )

    gaps = [row for row in rows if row.total_missing > 0]
    if args.json:
        _print_json(tenant_id=args.tenant_id, minimum=args.minimum, rows=rows, gaps=gaps)
    else:
        _print_table(tenant_id=args.tenant_id, minimum=args.minimum, rows=rows, gaps=gaps, show_all=args.all)
    return 1 if gaps else 0


def main() -> None:
    args = _build_parser().parse_args()
    raise SystemExit(asyncio.run(_run(args)))


if __name__ == "__main__":
    main()
