"""Load testing with Locust.
Usage: locust -f backend/tests/locustfile.py --host http://localhost:8000
"""
from locust import HttpUser, task, between, tag


class HealthCheckUser(HttpUser):
    """Simulates health check monitoring."""
    wait_time = between(1, 3)

    @tag("health")
    @task(3)
    def health(self):
        self.client.get("/api/v1/health/live")

    @tag("health")
    @task(1)
    def readiness(self):
        self.client.get("/api/v1/health/ready")

    @tag("health")
    @task(1)
    def full_health(self):
        self.client.get("/api/v1/health")


class AuthUser(HttpUser):
    """Simulates authentication flows."""
    wait_time = between(2, 5)

    def on_start(self):
        import uuid
        self.username = f"loadtest_{uuid.uuid4().hex[:8]}"
        self.password = "LoadTest123!"
        self.client.post("/api/v1/auth/register", json={
            "email": f"{self.username}@loadtest.dev",
            "username": self.username,
            "password": self.password,
        })
        resp = self.client.post("/api/v1/auth/login", json={
            "username": self.username,
            "password": self.password,
        })
        if resp.status_code == 200:
            data = resp.json()
            self.token = data.get("access_token", "")
            self.refresh = data.get("refresh_token", "")
        else:
            self.token = ""
            self.refresh = ""

    @tag("auth")
    @task(5)
    def get_me(self):
        if self.token:
            self.client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {self.token}"})

    @tag("auth")
    @task(1)
    def refresh_token(self):
        if self.refresh:
            resp = self.client.post("/api/v1/auth/refresh", json={"refresh_token": self.refresh})
            if resp.status_code == 200:
                data = resp.json()
                self.token = data.get("access_token", self.token)
                self.refresh = data.get("refresh_token", self.refresh)


class APIUser(HttpUser):
    """Simulates typical API usage patterns."""
    wait_time = between(1, 5)

    @tag("api")
    @task(3)
    def root(self):
        self.client.get("/")

    @tag("api")
    @task(2)
    def api_info(self):
        self.client.get("/api")

    @tag("api")
    @task(5)
    def list_repositories(self):
        self.client.get("/api/v1/repositories")

    @tag("api")
    @task(2)
    def search(self):
        self.client.post("/api/v1/search/semantic", json={
            "query": "authentication handler",
            "repository_id": 1,
            "top_k": 10,
        })

    @tag("api")
    @task(1)
    def graph_stats(self):
        self.client.get("/api/v1/graph/stats")
