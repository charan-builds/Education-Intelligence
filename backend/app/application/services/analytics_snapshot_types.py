USER_DASHBOARD_SNAPSHOT = "user_dashboard"
TEACHER_DASHBOARD_SNAPSHOT = "teacher_dashboard"
INSTITUTION_DASHBOARD_SNAPSHOT = "institution_dashboard"
SYSTEM_SUMMARY_SNAPSHOT = "system_summary"

# Backward-compatible aliases for existing projections.
TENANT_DASHBOARD_SNAPSHOT = "tenant_dashboard"
PLATFORM_OVERVIEW_SNAPSHOT = "platform_overview"
USER_LEARNING_SUMMARY_SNAPSHOT = "user_learning_summary"


def normalize_snapshot_type(snapshot_type: str) -> str:
    normalized = str(snapshot_type or "").strip().lower()
    if normalized == USER_LEARNING_SUMMARY_SNAPSHOT:
        return USER_DASHBOARD_SNAPSHOT
    if normalized == TENANT_DASHBOARD_SNAPSHOT:
        return INSTITUTION_DASHBOARD_SNAPSHOT
    if normalized == PLATFORM_OVERVIEW_SNAPSHOT:
        return SYSTEM_SUMMARY_SNAPSHOT
    return normalized
