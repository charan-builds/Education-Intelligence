from locust import HttpUser, between, task


class PlatformUser(HttpUser):
    wait_time = between(1, 3)

    @task(4)
    def health(self):
        self.client.get("/health")

    @task(2)
    def student_dashboard(self):
        self.client.get("/dashboard/student", name="/dashboard/student")

    @task(1)
    def analytics_overview(self):
        self.client.get("/analytics/overview", name="/analytics/overview")
