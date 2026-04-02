from __future__ import annotations

import re
from pathlib import Path


MODEL_ROOT = Path("backend/app/domain/models")
RLS_SQL_FILES = [
    Path("backend/sql/postgres_tenant_rls.sql"),
    Path("backend/sql/postgres_tenant_rls_phase2.sql"),
]

# These are intentionally tenant-aware operational/global tables that are not yet
# enforced through the business-table RLS rollout. They require separate worker
# and ops-path review before DB policies are mandated.
ALLOWED_MISSING_TABLES = {
    "dead_letter_events",
    "event_consumer_states",
    "outbox_events",
    "processed_stream_events",
    "stream_consumer_offsets",
}

# `tenants` is the parent partition of tenant ownership, not a tenant-scoped table.
NON_TENANT_SCOPED_TABLES = {"tenants"}

# Join/association tables inherit tenant scope from parent tables.
DERIVED_TENANT_TABLES = {
    "diagnostic_tests",
    "experiment_variants",
    "goal_topics",
    "job_role_skills",
    "questions",
    "refresh_sessions",
    "roadmaps",
    "roadmap_steps",
    "topic_prerequisites",
    "topic_skills",
    "user_answers",
}


def _model_tables() -> dict[str, bool]:
    tables: dict[str, bool] = {}
    for path in MODEL_ROOT.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        table_match = re.search(r'__tablename__\s*=\s*"([^"]+)"', text)
        if not table_match:
            continue
        table_name = table_match.group(1)
        has_direct_tenant = "tenant_id:" in text
        tables[table_name] = has_direct_tenant
    return tables


def _rls_tables() -> set[str]:
    tables: set[str] = set()
    for path in RLS_SQL_FILES:
        text = path.read_text(encoding="utf-8")
        tables.update(re.findall(r"alter table\s+(\w+)\s+enable row level security", text, flags=re.IGNORECASE))
        tables.update(re.findall(r"apply_simple_tenant_rls\('(\w+)'\)", text))
        tables.update(re.findall(r"apply_tenant_or_global_rls\('(\w+)'\)", text))
    return tables


def test_all_tenant_scoped_business_tables_have_rls_coverage() -> None:
    model_tables = _model_tables()
    rls_tables = _rls_tables()

    expected = {
        table_name
        for table_name, has_direct_tenant in model_tables.items()
        if has_direct_tenant or table_name in DERIVED_TENANT_TABLES
    }
    expected -= ALLOWED_MISSING_TABLES
    expected -= NON_TENANT_SCOPED_TABLES

    missing = sorted(expected - rls_tables)
    assert missing == [], f"Tenant-scoped tables missing RLS coverage: {missing}"
