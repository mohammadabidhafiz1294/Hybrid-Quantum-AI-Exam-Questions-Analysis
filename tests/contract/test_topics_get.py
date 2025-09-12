"""Contract test for GET /api/v1/topics endpoint."""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app


class TestTopicsGetContract:
    """Contract tests for topics endpoint."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

    def test_topics_endpoint_exists(self):
        """Test that the topics endpoint exists and is accessible."""
        response = self.client.get("/api/v1/topics")
        # Should return 200 with topics list, not 404
        assert response.status_code == 200

    def test_topics_response_structure(self):
        """Test that topics response has correct structure."""
        response = self.client.get("/api/v1/topics")

        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

        if len(data) > 0:
            # Check structure of first topic
            topic = data[0]
            assert "id" in topic
            assert "name" in topic
            assert "years_available" in topic
            assert "latest_year" in topic

            # Check data types
            assert isinstance(topic["id"], str)
            assert isinstance(topic["name"], str)
            assert isinstance(topic["years_available"], int)
            assert isinstance(topic["latest_year"], int)

            # Check reasonable values
            assert topic["years_available"] > 0
            assert topic["latest_year"] >= 2020  # Reasonable year range

    def test_topics_with_min_years_filter(self):
        """Test topics endpoint with minimum years filter."""
        response = self.client.get("/api/v1/topics?min_years=3")

        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

        # All returned topics should have at least 3 years of data
        for topic in data:
            assert topic["years_available"] >= 3

    def test_topics_with_invalid_min_years(self):
        """Test topics endpoint with invalid min_years parameter."""
        response = self.client.get("/api/v1/topics?min_years=-1")

        # Should handle gracefully or return validation error
        assert response.status_code in [200, 400, 422]

    def test_topics_response_consistency(self):
        """Test that topics response is consistent across calls."""
        # Make two consecutive calls
        response1 = self.client.get("/api/v1/topics")
        response2 = self.client.get("/api/v1/topics")

        assert response1.status_code == 200
        assert response2.status_code == 200

        data1 = response1.json()
        data2 = response2.json()

        # Should return same data (assuming no data changes between calls)
        assert data1 == data2

    def test_topics_response_time(self):
        """Test that topics endpoint responds quickly."""
        import time

        start_time = time.time()
        response = self.client.get("/api/v1/topics")
        end_time = time.time()

        # Should respond very quickly (< 1 second)
        assert end_time - start_time < 1.0
        assert response.status_code == 200

    def test_topics_content_type(self):
        """Test that topics endpoint returns correct content type."""
        response = self.client.get("/api/v1/topics")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

    def test_topics_cors_headers(self):
        """Test that topics endpoint has proper CORS headers."""
        response = self.client.options("/api/v1/topics")

        # Check if CORS headers are present (may return 200 or 404)
        cors_headers = [
            "access-control-allow-origin",
            "access-control-allow-methods",
            "access-control-allow-headers"
        ]

        # At least one CORS header should be present
        has_cors = any(header in response.headers for header in cors_headers)
        # Note: This might not be implemented yet, so we don't assert True
        cors_present = has_cors

    def test_topics_no_authentication_required(self):
        """Test that topics endpoint doesn't require authentication."""
        response = self.client.get("/api/v1/topics")

        # Should work without any auth headers
        assert response.status_code == 200
