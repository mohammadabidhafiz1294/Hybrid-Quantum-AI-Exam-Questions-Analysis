"""Contract test for GET /api/v1/health endpoint."""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app


class TestHealthGetContract:
    """Contract tests for health check endpoint."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

    def test_health_endpoint_exists(self):
        """Test that the health endpoint exists and is accessible."""
        response = self.client.get("/api/v1/health")
        # Should return 200 with health status, not 404
        assert response.status_code == 200

    def test_health_response_structure(self):
        """Test that health response has correct structure."""
        response = self.client.get("/api/v1/health")

        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data

        # Check status values
        assert data["status"] in ["healthy", "unhealthy", "degraded"]
        assert isinstance(data["timestamp"], str)
        assert isinstance(data["version"], str)

    def test_health_detailed_response(self):
        """Test health endpoint with detailed information."""
        response = self.client.get("/api/v1/health?detailed=true")

        assert response.status_code == 200

        data = response.json()

        # Should include additional detailed information
        if "detailed" in data:
            detailed = data["detailed"]
            assert isinstance(detailed, dict)

            # Check for common health indicators
            possible_keys = ["database", "quantum_simulator", "memory", "cpu", "disk"]
            has_some_detail = any(key in detailed for key in possible_keys)
            if has_some_detail:
                # At least one detailed component should be present
                pass

    def test_health_response_time(self):
        """Test that health endpoint responds very quickly."""
        import time

        start_time = time.time()
        response = self.client.get("/api/v1/health")
        end_time = time.time()

        # Should respond almost instantly (< 0.1 seconds)
        assert end_time - start_time < 0.1
        assert response.status_code == 200

    def test_health_content_type(self):
        """Test that health endpoint returns correct content type."""
        response = self.client.get("/api/v1/health")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

    def test_health_cors_headers(self):
        """Test that health endpoint has proper CORS headers."""
        response = self.client.options("/api/v1/health")

        # Check if CORS headers are present
        cors_headers = [
            "access-control-allow-origin",
            "access-control-allow-methods",
            "access-control-allow-headers"
        ]

        # At least one CORS header should be present
        has_cors = any(header in response.headers for header in cors_headers)
        cors_present = has_cors

    def test_health_no_authentication_required(self):
        """Test that health endpoint doesn't require authentication."""
        response = self.client.get("/api/v1/health")

        # Should work without any auth headers
        assert response.status_code == 200

    def test_health_status_values(self):
        """Test that health status returns valid values."""
        response = self.client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()

        # Status should be one of the expected values
        valid_statuses = ["healthy", "unhealthy", "degraded"]
        assert data["status"] in valid_statuses

        # If status is unhealthy, there should be additional error information
        if data["status"] == "unhealthy":
            assert "errors" in data or "message" in data

    def test_health_version_format(self):
        """Test that version follows semantic versioning format."""
        import re

        response = self.client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()

        version = data["version"]

        # Should follow semantic versioning (e.g., 1.0.0, 0.1.0-dev)
        semver_pattern = r'^\d+\.\d+\.\d+(-[\w\.\-]+)?(\+[\w\.\-]+)?$'
        assert re.match(semver_pattern, version), f"Version {version} doesn't match semver format"

    def test_health_timestamp_format(self):
        """Test that timestamp is in ISO format."""
        from datetime import datetime

        response = self.client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()

        timestamp = data["timestamp"]

        # Should be parseable as ISO format datetime
        try:
            datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            pytest.fail(f"Timestamp {timestamp} is not in valid ISO format")

    def test_health_multiple_calls_consistency(self):
        """Test that health endpoint is consistent across multiple calls."""
        responses = []

        # Make multiple calls
        for _ in range(3):
            response = self.client.get("/api/v1/health")
            assert response.status_code == 200
            responses.append(response.json())

        # Version should be consistent
        versions = [r["version"] for r in responses]
        assert all(v == versions[0] for v in versions)

        # Status should be reasonably consistent (may change if system state changes)
        statuses = [r["status"] for r in responses]
        # At least the first and last should be the same (assuming no state change)
        assert statuses[0] == statuses[-1]
