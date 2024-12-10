from locust import HttpUser, TaskSet, task, between
from dotenv import load_dotenv
import os

load_dotenv()

ADMIN = os.getenv("ADMIN")
ADMIN_PWORD = os.getenv("ADMIN_PWORD")
TEST_USER = os.getenv("TEST_USER")
TEST_USER_PWORD = os.getenv("TEST_USER_PWORD")

class UserBehavior(TaskSet):
    # ---------------- Healthchecks ----------------
    @task
    def auth_healthcheck(self):
        self.client.get("/auth/healthcheck")

    @task
    def profile_healthcheck(self):
        self.client.get("/profile/healthcheck")

    @task
    def messaging_healthcheck(self):
        self.client.get("/messaging/healthcheck")

    @task
    def friendship_healthcheck(self):
        self.client.get("/friendship/healthcheck")

    @task
    def api_healthcheck(self):
        self.client.get("/api/healthcheck")

    @task
    def commands_healthcheck(self):
        self.client.get("/commands/healthcheck")

    # ---------------- Admin Routes ----------------
    @task
    def admin_status(self):
        self.client.get("/admin/status", auth=(ADMIN, ADMIN_PWORD))

    @task
    def database_health(self):
        self.client.get("/admin/database", auth=(ADMIN, ADMIN_PWORD))

    #@task
    #def system_metrics(self):
    #    self.client.get("/admin/system/metrics", auth=(ADMIN, ADMIN_PWORD))

    @task
    def list_logs(self):
        self.client.get("/admin/logs", auth=(ADMIN, ADMIN_PWORD))

    @task
    def view_log_file(self):
        self.client.get("/admin/logs/test.log", auth=(ADMIN, ADMIN_PWORD))

    # ---------------- API Routes ----------------
    @task
    def fetch_table_records(self):
        self.client.get(
            "/api/table/users", 
            auth=(ADMIN, ADMIN_PWORD)
        )

class WebsiteUser(HttpUser):
    # Change the host to point to the load balancer
    host = "http://127.0.0.1:8080"  # Replace with your load balancer's address

    tasks = [UserBehavior]
    wait_time = between(1, 2)  # Random wait time between requests (1-2 seconds)
