import os
import random
from collections.abc import Sequence

from locust import HttpUser, between, task


TENANT_ID = int(os.getenv("LOAD_TEST_TENANT_ID", "2"))
STUDENT_CREDENTIALS: Sequence[tuple[str, str]] = (
    ("maya.chen@demo.example.com", "Student123!"),
    ("jordan.rivera@demo.example.com", "Student123!"),
    ("aisha.patel@demo.example.com", "Student123!"),
)
MENTOR_CREDENTIALS = (os.getenv("LOAD_TEST_MENTOR_EMAIL", "mentor@example.com"), os.getenv("LOAD_TEST_MENTOR_PASSWORD", "Mentor123!"))
TEACHER_CREDENTIALS = (os.getenv("LOAD_TEST_TEACHER_EMAIL", "teacher@example.com"), os.getenv("LOAD_TEST_TEACHER_PASSWORD", "Teacher123!"))


class AuthenticatedUser(HttpUser):
    wait_time = between(1, 3)
    abstract = True

    credentials: tuple[str, str] | None = None

    def on_start(self):
        if self.credentials is None:
            raise RuntimeError("credentials must be configured")
        self.csrf_headers: dict[str, str] = {}
        self.current_user_id: int | None = None
        self.goal_id: int | None = None
        self.current_test_id: int | None = None
        self._login(*self.credentials)

    def _login(self, email: str, password: str) -> None:
        with self.client.post(
            "/auth/login",
            json={"email": email, "password": password, "tenant_id": TENANT_ID},
            name="/auth/login",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"login failed: {response.status_code}")
                return
            payload = response.json()
            self.current_user_id = int(payload["user"]["id"])
            csrf = self.client.cookies.get("csrf_token")
            self.csrf_headers = {"X-CSRF-Token": csrf} if csrf else {}

    def _ensure_goal(self) -> int | None:
        if self.goal_id is not None:
            return self.goal_id
        with self.client.get("/goals?limit=5&offset=0", name="/goals", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"goals failed: {response.status_code}")
                return None
            items = response.json().get("items") or []
            if not items:
                response.failure("no goals available")
                return None
            self.goal_id = int(items[0]["id"])
            return self.goal_id


class StudentJourneyUser(AuthenticatedUser):
    weight = 5

    def on_start(self):
        self.credentials = random.choice(STUDENT_CREDENTIALS)
        super().on_start()
        self._ensure_goal()

    def _ensure_test(self) -> int | None:
        goal_id = self._ensure_goal()
        if goal_id is None:
            return None
        with self.client.post(
            "/diagnostic/start",
            json={"goal_id": goal_id},
            headers=self.csrf_headers,
            name="/diagnostic/start",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"diagnostic start failed: {response.status_code}")
                return None
            self.current_test_id = int(response.json()["id"])
            return self.current_test_id

    @task(4)
    def student_reads(self):
        self.client.get("/analytics/student-insights", name="/analytics/student-insights")
        if self.current_user_id is not None:
            self.client.get(
                f"/roadmap/{self.current_user_id}?limit=5&offset=0",
                name="/roadmap/{user_id}",
            )

    @task(2)
    def student_dashboard(self):
        self.client.get("/dashboard/student", name="/dashboard/student")

    @task(2)
    def roadmap_generate(self):
        test_id = self._ensure_test()
        goal_id = self._ensure_goal()
        if test_id is None or goal_id is None:
            return
        with self.client.post(
            "/roadmap/generate",
            json={"goal_id": goal_id, "test_id": test_id},
            headers=self.csrf_headers,
            name="/roadmap/generate",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"roadmap generate failed: {response.status_code}")

    @task(1)
    def diagnostic_step(self):
        test_id = self._ensure_test()
        if test_id is None:
            return
        with self.client.get(
            f"/diagnostic/next/{test_id}",
            name="/diagnostic/next/{test_id}",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"diagnostic next failed: {response.status_code}")
                return
            if response.text == "null":
                response.success()
                self.current_test_id = None
                return
            question = response.json()
        answer_text = random.choice(["A", "B", "C", "benchmark", "practice"])
        with self.client.post(
            "/diagnostic/answer",
            json={
                "test_id": test_id,
                "question_id": int(question["id"]),
                "user_answer": answer_text,
                "time_taken": random.randint(2, 12),
            },
            headers=self.csrf_headers,
            name="/diagnostic/answer",
            catch_response=True,
        ) as response:
            if response.status_code not in {200, 400, 409, 429}:
                response.failure(f"diagnostic answer unexpected: {response.status_code}")


class TeacherAnalyticsUser(AuthenticatedUser):
    weight = 3
    credentials = TEACHER_CREDENTIALS

    @task(4)
    def analytics_overview(self):
        self.client.get("/analytics/overview", name="/analytics/overview")

    @task(3)
    def roadmap_progress(self):
        self.client.get("/analytics/roadmap-progress?limit=10&offset=0", name="/analytics/roadmap-progress")

    @task(2)
    def weak_topics(self):
        self.client.get("/analytics/weak-topics", name="/analytics/weak-topics")

    @task(1)
    def teacher_dashboard(self):
        self.client.get("/dashboard/teacher", name="/dashboard/teacher")


class MentorAdvisoryUser(AuthenticatedUser):
    weight = 1
    credentials = MENTOR_CREDENTIALS

    @task(3)
    def mentor_learners(self):
        self.client.get("/mentor/learners", name="/mentor/learners")

    @task(2)
    def mentor_fallback_chat(self):
        request_id = f"locust-{self.environment.runner.user_count}-{random.randint(1000, 999999)}"
        with self.client.post(
            "/mentor/chat/fallback",
            json={
                "message": "What should this learner focus on next?",
                "chat_history": [],
                "request_id": request_id,
            },
            headers=self.csrf_headers,
            name="/mentor/chat/fallback",
            catch_response=True,
        ) as response:
            if response.status_code not in {200, 202, 429}:
                response.failure(f"mentor fallback unexpected: {response.status_code}")
