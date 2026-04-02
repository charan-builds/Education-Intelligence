#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import time
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:8000").rstrip("/")


@dataclass(frozen=True)
class Account:
    label: str
    email: str
    password: str
    tenant_id: int


STUDENT = Account("student", "student@example.com", "Student123!", 2)
TEACHER = Account("teacher", "teacher@example.com", "Teacher123!", 2)
MENTOR = Account("mentor", "mentor@example.com", "Mentor123!", 2)
ADMIN = Account("admin", "admin@example.com", "admin123", 2)
SUPER_ADMIN = Account("super_admin", "superadmin@platform.example.com", "SuperAdmin123!", 1)


class SmokeFailure(RuntimeError):
    pass


def log(message: str) -> None:
    print(f"[role-smoke] {message}")


def request_json(
    method: str,
    path: str,
    *,
    data: dict[str, Any] | None = None,
    token: str | None = None,
    params: dict[str, Any] | None = None,
) -> Any:
    url = f"{BASE_URL}{path}"
    if params:
        encoded = urllib.parse.urlencode(params)
        url = f"{url}?{encoded}"

    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    body = None if data is None else json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            payload = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SmokeFailure(f"{method} {path} failed with HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise SmokeFailure(f"{method} {path} failed: {exc.reason}") from exc

    return json.loads(payload) if payload else None


def login(account: Account) -> str:
    payload = request_json(
        "POST",
        "/auth/login",
        data={"email": account.email, "password": account.password, "tenant_id": account.tenant_id},
    )
    token = payload.get("access_token")
    if not token:
        raise SmokeFailure(f"login for {account.label} did not return an access token")
    log(f"{account.label}: login ok")
    return token


def unwrap_items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("items", "data", "results"):
            value = payload.get(key)
            if isinstance(value, list):
                return value
    return []


def assert_truthy(value: Any, label: str) -> Any:
    if not value:
        raise SmokeFailure(f"expected truthy value for {label}, got {value!r}")
    return value


def run() -> None:
    request_json("GET", "/health")
    log(f"api health ok at {BASE_URL}")

    student_token = login(STUDENT)
    teacher_token = login(TEACHER)
    mentor_token = login(MENTOR)
    admin_token = login(ADMIN)
    super_admin_token = login(SUPER_ADMIN)

    me = request_json("GET", "/users/me", token=student_token)
    assert_truthy(me.get("id"), "student profile id")
    log("student: profile ok")

    goals_payload = request_json("GET", "/goals", token=student_token)
    goals = unwrap_items(goals_payload)
    goal = assert_truthy(goals[0] if goals else None, "student goals[0]")
    goal_id = int(goal["id"])
    log(f"student: goals ok (goal_id={goal_id})")

    diagnostic = request_json("POST", "/diagnostic/start", token=student_token, data={"goal_id": goal_id})
    test_id = int(assert_truthy(diagnostic.get("id"), "diagnostic id"))
    log(f"student: diagnostic start ok (test_id={test_id})")

    answered_questions = 0
    seen_question_ids: set[int] = set()
    for _ in range(200):
        next_question = request_json(
            "GET",
            f"/diagnostic/next/{test_id}",
            token=student_token,
        )
        if next_question is None:
            break
        question_id = int(assert_truthy(next_question.get("id"), "next question id"))
        if question_id in seen_question_ids:
            raise SmokeFailure(f"diagnostic repeated question_id={question_id} before completion")
        seen_question_ids.add(question_id)
        options = next_question.get("answer_options") or []
        user_answer = options[1] if len(options) > 1 else "3"
        log(f"student: next question ok (question_id={question_id})")

        request_json(
            "POST",
            "/diagnostic/answer",
            token=student_token,
            data={
                "test_id": test_id,
                "question_id": question_id,
                "user_answer": user_answer,
                "time_taken": 12.5,
            },
        )
        answered_questions += 1
        time.sleep(1.3)

    assert_truthy(answered_questions, "student answered diagnostic questions")
    log(f"student: diagnostic answers ok ({answered_questions} questions)")

    request_json(
        "POST",
        "/diagnostic/submit",
        token=student_token,
        data={"test_id": test_id},
    )
    log("student: diagnostic submit ok")

    result = request_json("GET", "/diagnostic/result", token=student_token, params={"test_id": test_id})
    assert_truthy(result.get("topic_scores"), "diagnostic result topic_scores")
    log("student: diagnostic result ok")

    roadmap = request_json(
        "POST",
        "/roadmap/generate",
        token=student_token,
        data={"goal_id": goal_id, "test_id": test_id},
    )
    steps = roadmap.get("steps") or []
    if not steps:
        for _ in range(90):
            time.sleep(1.0)
            roadmap_page = request_json("GET", "/roadmap/view", token=student_token)
            items = roadmap_page.get("items") or []
            matching = [
                item for item in items
                if int(item.get("goal_id", 0)) == goal_id and int(item.get("test_id", 0)) == test_id
            ]
            if matching:
                roadmap = matching[0]
                steps = roadmap.get("steps") or []
                if roadmap.get("status") == "ready" and steps:
                    break
    assert_truthy(steps, "roadmap steps")
    log(f"student: roadmap generate ok ({len(steps)} steps)")

    mentor_chat = request_json(
        "POST",
        "/mentor/chat",
        token=student_token,
        data={
            "user_id": me["id"],
            "tenant_id": me["tenant_id"],
            "message": "How should I improve this week?",
        },
    )
    assert_truthy(mentor_chat.get("reply"), "mentor chat reply")
    log("student: mentor chat ok")

    teacher_overview = request_json("GET", "/analytics/overview", token=teacher_token)
    assert_truthy(teacher_overview.get("tenant_id"), "teacher analytics tenant_id")
    request_json("GET", "/analytics/topic-mastery", token=teacher_token)
    log("teacher: analytics ok")

    mentor_overview = request_json("GET", "/analytics/overview", token=mentor_token)
    assert_truthy(mentor_overview.get("tenant_id"), "mentor analytics tenant_id")
    mentor_suggestions = request_json("GET", "/mentor/suggestions", token=mentor_token)
    assert_truthy(mentor_suggestions.get("suggestions"), "mentor suggestions")
    log("mentor: analytics and suggestions ok")

    admin_users = request_json("GET", "/users", token=admin_token)
    assert_truthy(unwrap_items(admin_users), "admin users")
    request_json("GET", "/analytics/overview", token=admin_token)
    log("admin: users and analytics ok")

    platform = request_json("GET", "/analytics/platform-overview", token=super_admin_token)
    assert_truthy(platform.get("tenant_breakdown"), "platform tenant breakdown")
    request_json("GET", "/ops/outbox/stats", token=super_admin_token)
    log("super_admin: platform overview and outbox ok")

    log("all role panel checks passed")


if __name__ == "__main__":
    try:
        run()
    except SmokeFailure as exc:
        print(f"[role-smoke] FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
