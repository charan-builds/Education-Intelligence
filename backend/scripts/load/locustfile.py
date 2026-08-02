from __future__ import annotations

import itertools
import os
import random
from collections.abc import Sequence

from locust import HttpUser, between, task
from locust.exception import StopUser


TENANT_ID = int(os.getenv("LOAD_TEST_TENANT_ID", "2"))
QUESTION_COUNT = int(os.getenv("LOAD_TEST_QUESTION_COUNT", "20"))
START_USER_COUNT = int(os.getenv("LOAD_TEST_START_USERS", "100"))
SUBMIT_USER_COUNT = int(os.getenv("LOAD_TEST_SUBMIT_USERS", "100"))
DEFAULT_WAIT_MIN_SECONDS = float(os.getenv("LOAD_TEST_WAIT_MIN_SECONDS", "0.25"))
DEFAULT_WAIT_MAX_SECONDS = float(os.getenv("LOAD_TEST_WAIT_MAX_SECONDS", "1.25"))

DEFAULT_STUDENT_CREDENTIALS: Sequence[tuple[str, str]] = (
    ("maya.chen@demo.learnova.ai", "Student123!"),
    ("jordan.rivera@demo.learnova.ai", "Student123!"),
    ("aisha.patel@demo.learnova.ai", "Student123!"),
)


def _student_credentials() -> list[tuple[str, str]]:
    raw_credentials = os.getenv("LOAD_TEST_STUDENT_CREDENTIALS", "").strip()
    if not raw_credentials:
        return list(DEFAULT_STUDENT_CREDENTIALS)

    credentials: list[tuple[str, str]] = []
    for raw_item in raw_credentials.split(","):
        item = raw_item.strip()
        if not item:
            continue
        if ":" not in item:
            raise RuntimeError("LOAD_TEST_STUDENT_CREDENTIALS entries must use email:password")
        email, password = item.split(":", 1)
        credentials.append((email.strip(), password.strip()))
    if not credentials:
        raise RuntimeError("LOAD_TEST_STUDENT_CREDENTIALS did not contain any usable credentials")
    return credentials


STUDENT_CREDENTIALS = _student_credentials()
_CREDENTIAL_ROTATION = itertools.cycle(STUDENT_CREDENTIALS)


def _answer_for_question(question: dict) -> str:
    options = question.get("options") or question.get("answer_options") or []
    if options:
        preferred = options[1] if len(options) > 1 else options[0]
        if isinstance(preferred, dict):
            return str(
                preferred.get("text")
                or preferred.get("option_text")
                or preferred.get("label")
                or preferred.get("value")
                or preferred.get("key")
                or "A"
            )
        return str(preferred)
    return random.choice(("A", "B", "C", "practice", "benchmark"))


class DiagnosticLoadUser(HttpUser):
    abstract = True
    wait_time = between(DEFAULT_WAIT_MIN_SECONDS, DEFAULT_WAIT_MAX_SECONDS)

    def on_start(self) -> None:
        self.auth_headers: dict[str, str] = {}
        self.csrf_headers: dict[str, str] = {}
        self.goal_id = int(os.getenv("LOAD_TEST_GOAL_ID", "0")) or None
        email, password = next(_CREDENTIAL_ROTATION)
        self._login(email=email, password=password)
        self._ensure_goal()

    def _headers(self, *, unsafe: bool = False) -> dict[str, str]:
        headers = dict(self.auth_headers)
        if unsafe:
            headers.update(self.csrf_headers)
        return headers

    def _login(self, *, email: str, password: str) -> None:
        with self.client.post(
            "/auth/login",
            json={"email": email, "password": password, "tenant_id": TENANT_ID},
            name="/auth/login",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"login failed: {response.status_code}")
                raise StopUser()
            payload = response.json()
            access_token = payload.get("access_token")
            if access_token:
                self.auth_headers = {"Authorization": f"Bearer {access_token}"}
            csrf = self.client.cookies.get("csrf_token")
            self.csrf_headers = {"X-CSRF-Token": csrf} if csrf else {}

    def _ensure_goal(self) -> int:
        if self.goal_id is not None:
            return self.goal_id
        with self.client.get(
            "/goals?limit=5&offset=0",
            headers=self._headers(),
            name="/goals",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"goals failed: {response.status_code}")
                raise StopUser()
            items = response.json().get("items") or []
            if not items:
                response.failure("no goals available")
                raise StopUser()
            self.goal_id = int(items[0]["id"])
            return self.goal_id

    def _start_diagnostic(self, *, request_name: str) -> dict | None:
        with self.client.post(
            "/diagnostic/start",
            json={"goal_id": self._ensure_goal(), "question_count": QUESTION_COUNT},
            headers=self._headers(unsafe=True),
            name=request_name,
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"diagnostic start failed: {response.status_code}")
                return None
            payload = response.json()
            if not payload.get("id"):
                response.failure("diagnostic start response missing id")
                return None
            if "questions" in payload and not payload.get("questions"):
                response.failure("diagnostic start response returned no questions")
                return None
            return payload


class StartDiagnosticUser(DiagnosticLoadUser):
    fixed_count = START_USER_COUNT

    @task
    def start_test(self) -> None:
        self._start_diagnostic(request_name="/diagnostic/start [100 start users]")


class SubmitDiagnosticAnswersUser(DiagnosticLoadUser):
    fixed_count = SUBMIT_USER_COUNT

    @task
    def submit_answers(self) -> None:
        diagnostic = self._start_diagnostic(request_name="/diagnostic/start [submit setup]")
        if diagnostic is None:
            return

        questions = diagnostic.get("questions") or []
        answers = [
            {
                "question_id": int(question["id"]),
                "selected_answer": _answer_for_question(question),
                "time_taken": random.uniform(3.0, 18.0),
            }
            for question in questions
            if question.get("id") is not None
        ]
        if not answers:
            return

        with self.client.post(
            "/diagnostic/submit",
            json={"test_id": int(diagnostic["id"]), "answers": answers},
            headers=self._headers(unsafe=True),
            name="/diagnostic/submit [100 submit users]",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"diagnostic submit failed: {response.status_code} {response.text[:300]}")
                return
            payload = response.json()
            if int(payload.get("id") or payload.get("test_id") or 0) != int(diagnostic["id"]):
                response.failure("diagnostic submit response test_id mismatch")
