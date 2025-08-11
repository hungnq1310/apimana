"""
Static Locust test scenarios for API Gateway performance testing.

This file contains pre-configured test scenarios for traditional load testing
without dynamic discovery features.
"""

from locust import HttpUser, task, between
import random
import json


class GatewayUser(HttpUser):
    """Base user class for gateway testing."""
    
    wait_time = between(1, 3)
    
    def on_start(self):
        """Setup method called when a user starts."""
        self.session_id = None
    
    @task(10)
    def health_check(self):
        """Test the health endpoint."""
        self.client.get("/health")
    
    @task(5)
    def root_endpoint(self):
        """Test the root endpoint."""
        self.client.get("/")
    
    @task(3)
    def gateway_status(self):
        """Test gateway status endpoint."""
        self.client.get("/gateway/status")
    
    @task(2)
    def gateway_services(self):
        """Test gateway services endpoint."""
        self.client.get("/gateway/services")


class DocumentUser(HttpUser):
    """User class for testing document service endpoints."""
    
    wait_time = between(2, 5)
    
    def on_start(self):
        """Setup method called when a user starts."""
        self.session_id = None
        self.created_sessions = []
    
    def on_stop(self):
        """Cleanup method called when a user stops."""
        # Clean up any created sessions
        for session_id in self.created_sessions:
            try:
                self.client.delete(f"/api/v1/documents/sessions/{session_id}")
            except:
                pass
    
    @task(5)
    def documents_health(self):
        """Test document service health."""
        self.client.get("/api/v1/documents/health")
    
    @task(3)
    def documents_info(self):
        """Test document service info."""
        self.client.get("/api/v1/documents/info")
    
    @task(8)
    def create_session(self):
        """Test session creation."""
        response = self.client.post(
            "/api/v1/documents/sessions",
            json={
                "name": f"test_session_{random.randint(1000, 9999)}",
                "description": "Load test session"
            }
        )
        if response.status_code == 201:
            try:
                data = response.json()
                if "id" in data:
                    self.session_id = data["id"]
                    self.created_sessions.append(self.session_id)
            except:
                pass
    
    @task(2)
    def list_documents(self):
        """Test document listing."""
        params = {
            "limit": random.randint(10, 50),
            "offset": random.randint(0, 100)
        }
        self.client.get("/api/v1/documents/", params=params)
    
    @task(1)
    def upload_document(self):
        """Test document upload (if session exists)."""
        if self.session_id:
            # Simulate a small file upload
            files = {
                'file': ('test_document.txt', 'This is a test document content', 'text/plain')
            }
            data = {
                'description': 'Test document upload'
            }
            self.client.post(
                f"/api/v1/documents/sessions/{self.session_id}/upload",
                files=files,
                data=data
            )


class LightUser(GatewayUser):
    """Light load user - basic functionality testing."""
    wait_time = between(2, 5)


class MediumUser(GatewayUser):
    """Medium load user - balanced testing."""
    wait_time = between(1, 3)


class HeavyUser(HttpUser):
    """Heavy load user - intensive testing."""
    wait_time = between(0.5, 2)
    
    @task(15)
    def rapid_health_checks(self):
        """Rapid health check requests."""
        self.client.get("/health")
    
    @task(10)
    def rapid_gateway_calls(self):
        """Rapid gateway API calls."""
        endpoints = ["/", "/gateway/status", "/gateway/services"]
        endpoint = random.choice(endpoints)
        self.client.get(endpoint)
    
    @task(5)
    def document_operations(self):
        """Rapid document operations."""
        self.client.get("/api/v1/documents/health")


class SpikeUser(HttpUser):
    """Spike load user - burst testing."""
    wait_time = between(0.1, 1)
    
    @task(20)
    def burst_requests(self):
        """Burst of requests to test spike handling."""
        endpoints = [
            "/health",
            "/",
            "/gateway/status",
            "/api/v1/documents/health"
        ]
        endpoint = random.choice(endpoints)
        self.client.get(endpoint)


# Default user classes for different test types
# These can be selected with --user-classes parameter
__all__ = [
    'GatewayUser',
    'DocumentUser', 
    'LightUser',
    'MediumUser',
    'HeavyUser',
    'SpikeUser'
]
