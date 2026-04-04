import time
from collections import defaultdict

metrics = defaultdict(dict)


def record_job(queue, status, duration):
    if "count" not in metrics[queue]:
        metrics[queue]["count"] = 0
    metrics[queue]["count"] += 1

    if status == "failed":
        metrics[queue]["failed"] = metrics[queue].get("failed", 0) + 1

    metrics[queue]["last_duration"] = duration


def get_metrics():
    return metrics
