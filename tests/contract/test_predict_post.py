"""Contract test for POST /api/v1/predict endpoint."""

import pytest
from httpx import AsyncClient
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.main import app


class TestPredictPostContract:
    """Contract tests for prediction endpoint."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

    def test_predict_endpoint_exists(self):
        """Test that the predict endpoint exists and is accessible."""
        response = self.client.post("/api/v1/predict")
        # Should return 422 for missing required fields, not 404
        assert response.status_code != 404

    def test_predict_with_valid_data(self):
        """Test prediction with valid request data."""
        request_data = {
            "topics": ["quantum-mechanics", "linear-algebra"],
            "historical_years": 5,
            "confidence_level": 0.95,
            "force_classical": False
        }

        response = self.client.post(
            "/api/v1/predict",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )

        # Should return 200 with prediction results
        assert response.status_code == 200

        data = response.json()
        assert "predictions" in data
        assert "execution_time_ms" in data
        assert "fallback_used" in data
        assert isinstance(data["predictions"], list)
        assert len(data["predictions"]) == 2

        # Check prediction structure
        prediction = data["predictions"][0]
        assert "topic" in prediction
        assert "importance" in prediction
        assert "confidence_interval" in prediction
        assert "trend" in prediction
        assert "method" in prediction

        # Check confidence interval structure
        ci = prediction["confidence_interval"]
        assert isinstance(ci, list)
        assert len(ci) == 2
        assert ci[0] <= prediction["importance"] <= ci[1]

    def test_predict_with_minimal_data(self):
        """Test prediction with minimal required data."""
        request_data = {
            "topics": ["calculus"]
        }

        response = self.client.post(
            "/api/v1/predict",
            json=request_data
        )

        assert response.status_code == 200

        data = response.json()
        assert len(data["predictions"]) == 1
        assert data["predictions"][0]["topic"] == "calculus"

    def test_predict_force_classical(self):
        """Test prediction with forced classical method."""
        request_data = {
            "topics": ["physics"],
            "force_classical": True
        }

        response = self.client.post(
            "/api/v1/predict",
            json=request_data
        )

        assert response.status_code == 200

        data = response.json()
        prediction = data["predictions"][0]
        assert prediction["method"] in ["classical", "classical_fallback"]

    def test_predict_invalid_topic(self):
        """Test prediction with invalid topic."""
        request_data = {
            "topics": ["non-existent-topic"]
        }

        response = self.client.post(
            "/api/v1/predict",
            json=request_data
        )

        # Should handle gracefully, possibly with empty predictions or error
        assert response.status_code in [200, 400, 422]

    def test_predict_empty_topics(self):
        """Test prediction with empty topics list."""
        request_data = {
            "topics": []
        }

        response = self.client.post(
            "/api/v1/predict",
            json=request_data
        )

        # Should return validation error
        assert response.status_code == 422

    def test_predict_invalid_confidence_level(self):
        """Test prediction with invalid confidence level."""
        request_data = {
            "topics": ["math"],
            "confidence_level": 1.5  # Invalid: should be 0-1
        }

        response = self.client.post(
            "/api/v1/predict",
            json=request_data
        )

        # Should return validation error
        assert response.status_code == 422

    def test_predict_response_time(self):
        """Test that prediction response is reasonably fast."""
        import time

        request_data = {
            "topics": ["test-topic"]
        }

        start_time = time.time()
        response = self.client.post(
            "/api/v1/predict",
            json=request_data
        )
        end_time = time.time()

        # Should respond within reasonable time (30 seconds for quantum)
        assert end_time - start_time < 30.0
        assert response.status_code == 200

    def test_predict_execution_time_reported(self):
        """Test that execution time is properly reported."""
        request_data = {
            "topics": ["test-topic"]
        }

        response = self.client.post(
            "/api/v1/predict",
            json=request_data
        )

        assert response.status_code == 200
        data = response.json()

        # Execution time should be reasonable
        assert isinstance(data["execution_time_ms"], (int, float))
        assert data["execution_time_ms"] > 0
        assert data["execution_time_ms"] < 30000  # Less than 30 seconds
