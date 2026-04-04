CRITICAL_QUEUE = "critical"
ANALYTICS_QUEUE = "analytics"
AI_QUEUE = "ai"
OPS_QUEUE = "ops"


def get_queue_for_job(job_type: str) -> str:
    mapping = {
        "diagnostic": CRITICAL_QUEUE,
        "roadmap": CRITICAL_QUEUE,
        "analytics": ANALYTICS_QUEUE,
        "ai": AI_QUEUE,
        "maintenance": OPS_QUEUE,
    }
    return mapping.get(job_type, CRITICAL_QUEUE)
