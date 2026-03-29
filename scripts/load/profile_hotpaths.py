from __future__ import annotations

import argparse
import asyncio
import cProfile
import io
import pstats
import time
from collections import defaultdict
from collections.abc import Awaitable, Callable

from sqlalchemy import event

from app.application.services.analytics_service import AnalyticsService
from app.application.services.roadmap_service import RoadmapService
from app.infrastructure.database import AsyncSessionLocal, engine


ProfilerTarget = Callable[[], Awaitable[object]]


class QueryTrace:
    def __init__(self) -> None:
        self.durations_ms: list[tuple[float, str]] = []

    def install(self) -> None:
        @event.listens_for(engine.sync_engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            conn.info.setdefault("_profile_query_start_time", []).append((time.perf_counter(), statement or ""))

        @event.listens_for(engine.sync_engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            start_time, sql = conn.info.get("_profile_query_start_time", []).pop(-1)
            elapsed_ms = max((time.perf_counter() - start_time) * 1000, 0.0)
            self.durations_ms.append((elapsed_ms, sql))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Profile analytics and roadmap hot paths against the configured database.")
    parser.add_argument("target", choices=["analytics-overview", "roadmap-progress", "roadmap-generate"])
    parser.add_argument("--tenant-id", type=int, default=2)
    parser.add_argument("--user-id", type=int)
    parser.add_argument("--goal-id", type=int)
    parser.add_argument("--test-id", type=int)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--stats", type=int, default=25, help="number of cProfile rows to print")
    return parser


async def _run_profile(args: argparse.Namespace) -> None:
    query_trace = QueryTrace()
    query_trace.install()

    async with AsyncSessionLocal() as session:
        analytics_service = AnalyticsService(session)
        roadmap_service = RoadmapService(session)

        if args.target == "analytics-overview":
            target: ProfilerTarget = lambda: analytics_service.aggregated_metrics(args.tenant_id)
        elif args.target == "roadmap-progress":
            target = lambda: analytics_service.roadmap_progress_summary(
                tenant_id=args.tenant_id,
                limit=args.limit,
                offset=args.offset,
            )
        else:
            if args.user_id is None or args.goal_id is None or args.test_id is None:
                raise SystemExit("--user-id, --goal-id, and --test-id are required for roadmap-generate")
            target = lambda: roadmap_service.generate(
                user_id=args.user_id,
                tenant_id=args.tenant_id,
                goal_id=args.goal_id,
                test_id=args.test_id,
            )

        profile = cProfile.Profile()
        started = time.perf_counter()
        profile.enable()
        result = await target()
        profile.disable()
        elapsed_ms = (time.perf_counter() - started) * 1000

        output = io.StringIO()
        stats = pstats.Stats(profile, stream=output).sort_stats("cumulative")
        stats.print_stats(args.stats)

        print(f"target={args.target}")
        print(f"elapsed_ms={elapsed_ms:.2f}")
        if isinstance(result, dict):
            print(f"result_keys={sorted(result.keys())}")
        else:
            print(f"result_type={type(result).__name__}")

        print("\nTop cProfile frames")
        print(output.getvalue().rstrip())

    print("\nTop SQL statements")
    grouped: dict[str, list[float]] = defaultdict(list)
    for elapsed, sql in query_trace.durations_ms:
        preview = " ".join(sql.split())[:220]
        grouped[preview].append(elapsed)
    ranked = sorted(
        grouped.items(),
        key=lambda item: (sum(item[1]), max(item[1]), len(item[1])),
        reverse=True,
    )
    for index, (preview, timings) in enumerate(ranked[:10], start=1):
        print(
            f"{index}. total_ms={sum(timings):.2f} calls={len(timings)} max_ms={max(timings):.2f} sql={preview}"
        )


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    asyncio.run(_run_profile(args))


if __name__ == "__main__":
    main()
