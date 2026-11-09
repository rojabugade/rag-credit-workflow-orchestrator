from locust import HttpUser, between, task


class AnalystUser(HttpUser):
    wait_time = between(0.5, 2)

    @task(5)
    def list_cases(self) -> None:
        self.client.get("/api/v1/cases?limit=20")

    @task(2)
    def policy_search(self) -> None:
        self.client.post(
            "/api/v1/policies/search",
            json={"query": "financial statements", "effective_on": "2026-06-01"},
        )

    @task(1)
    def health(self) -> None:
        self.client.get("/health/ready")
