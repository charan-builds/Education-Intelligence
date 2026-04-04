"""postgres rls phase 2 tenant coverage

Revision ID: 20260402_0018
Revises: 20260402_0017
Create Date: 2026-04-02 02:30:00.000000
"""

from pathlib import Path

from alembic import op


revision = "20260402_0018"
down_revision = "20260402_0017"
branch_labels = None
depends_on = None


def _split_sql_statements(sql: str) -> list[str]:
    statements: list[str] = []
    current: list[str] = []
    in_single_quote = False
    in_double_quote = False
    dollar_tag: str | None = None
    i = 0

    while i < len(sql):
        chunk = sql[i:]

        if not in_single_quote and not in_double_quote and chunk.startswith("--"):
            newline_index = chunk.find("\n")
            if newline_index == -1:
                break
            current.append(chunk[: newline_index + 1])
            i += newline_index + 1
            continue

        if not in_single_quote and not in_double_quote and chunk.startswith("/*"):
            comment_end = chunk.find("*/", 2)
            if comment_end == -1:
                current.append(chunk)
                break
            current.append(chunk[: comment_end + 2])
            i += comment_end + 2
            continue

        if not in_single_quote and not in_double_quote and chunk.startswith("$"):
            closing_tag = chunk.find("$", 1)
            if closing_tag != -1:
                candidate = chunk[: closing_tag + 1]
                is_valid_dollar_tag = candidate == "$$" or (
                    candidate.count("$") == 2 and candidate.replace("$", "").replace("_", "").isalnum()
                )
                if is_valid_dollar_tag:
                    if dollar_tag is None:
                        dollar_tag = candidate
                    elif candidate == dollar_tag:
                        dollar_tag = None
                    current.append(candidate)
                    i += len(candidate)
                    continue

        char = sql[i]
        current.append(char)

        if dollar_tag is None:
            if char == "'" and not in_double_quote:
                previous = sql[i - 1] if i > 0 else ""
                if previous != "\\":
                    in_single_quote = not in_single_quote
            elif char == '"' and not in_single_quote:
                previous = sql[i - 1] if i > 0 else ""
                if previous != "\\":
                    in_double_quote = not in_double_quote
            elif char == ";" and not in_single_quote and not in_double_quote:
                statement = "".join(current).strip()
                if statement:
                    statements.append(statement)
                current = []
        i += 1

    trailing = "".join(current).strip()
    if trailing:
        statements.append(trailing)
    return statements


def upgrade() -> None:
    sql_path = Path(__file__).resolve().parents[2] / "sql" / "postgres_tenant_rls_phase2.sql"
    for statement in _split_sql_statements(sql_path.read_text(encoding="utf-8")):
        op.execute(statement)


def downgrade() -> None:
    # Intentional no-op downgrade. Removing RLS policies should be explicit and manual.
    pass
