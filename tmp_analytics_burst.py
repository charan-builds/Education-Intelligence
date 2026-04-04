import asyncio
import json
import statistics
import subprocess
import sys
import time
from collections import Counter

import httpx
import redis

sys.path.insert(0, "backend")

from app.core.security import create_access_token  # noqa: E402


API_BASE = "http://127.0.0.1:8000"
REDIS_HOST = "127.0.0.1"
REDIS_PORT = 6380
SESSION_ID = "639e204f781e480fad0280012820d18a"
USER_ID = 3
TENANT_ID = 2
TOKEN_VERSION = 31
REQUEST_COUNT = 1000
QUEUE_NAMES = ("analytics", "critical", "ops", "ai", "celery")


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(len(ordered) - 1, max(0, int(round((pct / 100.0) * (len(ordered) - 1)))))
    return ordered[idx]


def build_token() -> str:
    return create_access_token(
        {
            "sub": str(USER_ID),
            "tenant_id": TENANT_ID,
            "jti": SESSION_ID,
            "tv": TOKEN_VERSION,
            "scope": "full_access",
        }
    )


def queue_depths(r: redis.Redis) -> dict[str, int]:
    return {name: int(r.llen(name)) if r.exists(name) else 0 for name in QUEUE_NAMES}


def run_psql(sql: str) -> str:
    cmd = [
        "docker",
        "exec",
        "learning_platform_postgres",
        "psql",
        "-U",
        "postgres",
        "-d",
        "learning_platform",
        "-t",
        "-A",
        "-F",
        "|",
        "-c",
        sql,
    ]
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def pg_database_stats() -> dict[str, int]:
    raw = run_psql(
        "select numbackends, xact_commit, tup_returned, tup_fetched, blks_read, blks_hit "
        "from pg_stat_database where datname='learning_platform';"
    )
    parts = [part.strip() for part in raw.split("|")]
    keys = ["numbackends", "xact_commit", "tup_returned", "tup_fetched", "blks_read", "blks_hit"]
    return {key: int(value) for key, value in zip(keys, parts, strict=False)}


def active_queries() -> list[str]:
    raw = run_psql(
        """
        select regexp_replace(query, '\s+', ' ', 'g')
        from pg_stat_activity
        where datname='learning_platform'
          and state='active'
          and query not ilike '%pg_stat_activity%'
        ;
        """
    )
    return [line.strip() for line in raw.splitlines() if line.strip()]


async def sample_active_queries(stop_event: asyncio.Event, samples: list[dict]) -> None:
    while not stop_event.is_set():
        try:
            queries = active_queries()
        except Exception as exc:  # pragma: no cover
            queries = [f"sampler_error: {exc}"]
        if queries:
            samples.append({"ts": time.perf_counter(), "queries": queries})
        await asyncio.sleep(0.1)


async def hit_once(client: httpx.AsyncClient, token: str) -> dict:
    started = time.perf_counter()
    try:
        response = await client.get("/analytics/overview", headers={"Authorization": f"Bearer {token}"})
        elapsed_ms = (time.perf_counter() - started) * 1000
        payload = {}
        content_type = response.headers.get("content-type", "")
        if response.content and "application/json" in content_type:
            try:
                payload = response.json()
            except json.JSONDecodeError:
                payload = {}
        meta = payload.get("meta") or {}
        return {
            "status_code": response.status_code,
            "elapsed_ms": elapsed_ms,
            "meta_status": meta.get("status"),
            "content_type": content_type,
            "body_sample": response.text[:200],
        }
    except Exception as exc:
        return {
            "status_code": "exception",
            "elapsed_ms": (time.perf_counter() - started) * 1000,
            "meta_status": "exception",
            "content_type": "",
            "body_sample": str(exc),
        }


async def main() -> None:
    token = build_token()
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)

    baseline_response = httpx.get(
        f"{API_BASE}/analytics/overview",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10.0,
    )
    baseline_payload = baseline_response.json()

    queue_before = queue_depths(redis_client)
    db_before = pg_database_stats()

    active_query_samples: list[dict] = []
    stop_event = asyncio.Event()
    sampler = asyncio.create_task(sample_active_queries(stop_event, active_query_samples))

    async with httpx.AsyncClient(base_url=API_BASE, timeout=30.0) as client:
        started = time.perf_counter()
        results = await asyncio.gather(*[hit_once(client, token) for _ in range(REQUEST_COUNT)])
        total_elapsed_s = time.perf_counter() - started

    stop_event.set()
    await sampler

    queue_after = queue_depths(redis_client)
    db_after = pg_database_stats()

    latencies = [item["elapsed_ms"] for item in results]
    statuses = Counter(item["status_code"] for item in results)
    meta_statuses = Counter(item["meta_status"] or "missing" for item in results)
    content_types = Counter(item["content_type"] or "missing" for item in results)
    failure_samples = [item for item in results if item["status_code"] != 200][:10]

    observed_queries = Counter()
    max_active_queries = 0
    for sample in active_query_samples:
        max_active_queries = max(max_active_queries, len(sample["queries"]))
        for query in sample["queries"]:
            observed_queries[query] += 1

    heavy_queries = [
        query
        for query in observed_queries
        if any(token in query.lower() for token in ("join roadmap", "join diagnostic_tests", "join user_answers", "refresh materialized view"))
    ]
    snapshot_queries = [query for query in observed_queries if "analytics_snapshots" in query.lower()]
    auth_queries = [query for query in observed_queries if any(token in query.lower() for token in ("from sessions", "from users", "from user_tenant_roles"))]

    summary = {
        "request_count": REQUEST_COUNT,
        "total_elapsed_s": round(total_elapsed_s, 3),
        "throughput_rps": round(REQUEST_COUNT / total_elapsed_s, 2) if total_elapsed_s > 0 else 0.0,
        "status_counts": dict(statuses),
        "response_time_ms": {
            "min": round(min(latencies), 2),
            "avg": round(statistics.mean(latencies), 2),
            "median": round(statistics.median(latencies), 2),
            "p95": round(percentile(latencies, 95), 2),
            "p99": round(percentile(latencies, 99), 2),
            "max": round(max(latencies), 2),
        },
        "baseline_meta_status": (baseline_payload.get("meta") or {}).get("status"),
        "meta_status_counts": dict(meta_statuses),
        "content_type_counts": dict(content_types),
        "queue_before": queue_before,
        "queue_after": queue_after,
        "queue_growth": {name: queue_after[name] - queue_before[name] for name in QUEUE_NAMES},
        "db_delta": {key: int(db_after[key]) - int(db_before[key]) for key in db_before},
        "max_active_queries_seen": max_active_queries,
        "observed_query_count": len(observed_queries),
        "observed_snapshot_queries": snapshot_queries[:10],
        "observed_auth_queries": auth_queries[:10],
        "observed_heavy_queries": heavy_queries[:10],
        "failure_samples": failure_samples,
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
