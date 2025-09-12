"""Contract test for POST /api/v1/train endpoint."""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app


class TestTrainPostContract:
    """Contract tests for training endpoint."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

    def test_train_endpoint_exists(self):
        """Test that the train endpoint exists and is accessible."""
        response = self.client.post("/api/v1/train")
        # Should return 422 for missing required fields, not 404
        assert response.status_code != 404

    def test_train_with_valid_data(self):
        """Test training with valid request data."""
        request_data = {
            "topics": ["quantum-mechanics", "linear-algebra"],
            "data_source": "csv",
            "file_path": "data/exam_data.csv",
            "validation_split": 0.2,
            "force_retrain": False
        }

        response = self.client.post(
            "/api/v1/train",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )

        # Should return 200 or 202 (accepted for async processing)
        assert response.status_code in [200, 202]

        data = response.json()
        assert "status" in data
        assert "message" in data
        assert data["status"] in ["success", "accepted", "running"]

        if response.status_code == 200:
            # Synchronous response
            assert "training_id" in data
            assert "metrics" in data

    def test_train_minimal_data(self):
        """Test training with minimal required data."""
        request_data = {
            "topics": ["calculus"],
            "data_source": "json",
            "file_path": "data/training_data.json"
        }

        response = self.client.post(
            "/api/v1/train",
            json=request_data
        )

        assert response.status_code in [200, 202]

        data = response.json()
        assert "status" in data
        assert "message" in data

    def test_train_force_retrain(self):
        """Test training with force retrain option."""
        request_data = {
            "topics": ["physics"],
            "force_retrain": True
        }

        response = self.client.post(
            "/api/v1/train",
            json=request_data
        )

        assert response.status_code in [200, 202]

        data = response.json()
        # Should indicate that retraining is happening
        assert "retraining" in data.get("message", "").lower() or data["status"] == "running"

    def test_train_invalid_data_source(self):
        """Test training with invalid data source."""
        request_data = {
            "topics": ["math"],
            "data_source": "invalid_format"
        }

        response = self.client.post(
            "/api/v1/train",
            json=request_data
        )

        # Should return validation error
        assert response.status_code == 422

    def test_train_missing_file(self):
        """Test training with missing file."""
        request_data = {
            "topics": ["chemistry"],
            "data_source": "csv",
            "file_path": "nonexistent/file.csv"
        }

        response = self.client.post(
            "/api/v1/train",
            json=request_data
        )

        # Should return error for missing file
        assert response.status_code in [400, 404, 422]

    def test_train_empty_topics(self):
        """Test training with empty topics list."""
        request_data = {
            "topics": [],
            "data_source": "csv",
            "file_path": "data/exam_data.csv"
        }

        response = self.client.post(
            "/api/v1/train",
            json=request_data
        )

        # Should return validation error
        assert response.status_code == 422

    def test_train_invalid_validation_split(self):
        """Test training with invalid validation split."""
        request_data = {
            "topics": ["biology"],
            "validation_split": 1.5  # Invalid: should be 0-1
        }

        response = self.client.post(
            "/api/v1/train",
            json=request_data
        )

        # Should return validation error
        assert response.status_code == 422

    def test_train_response_time(self):
        """Test that training initiation is reasonably fast."""
        import time

        request_data = {
            "topics": ["test-topic"],
            "data_source": "csv",
            "file_path": "data/test_data.csv"
        }

        start_time = time.time()
        response = self.client.post(
            "/api/v1/train",
            json=request_data
        )
        end_time = time.time()

        # Should respond quickly (< 5 seconds for initiation)
        assert end_time - start_time < 5.0
        assert response.status_code in [200, 202, 400, 404, 422]

    def test_train_async_processing(self):
        """Test that training supports async processing."""
        request_data = {
            "topics": ["async-test"],
            "async_processing": True
        }

        response = self.client.post(
            "/api/v1/train",
            json=request_data
        )

        # Should return 202 Accepted for async processing
        if "async_processing" in request_data and request_data["async_processing"]:
            assert response.status_code == 202

            data = response.json()
            assert "training_id" in data
            assert "status" in data
            assert data["status"] == "accepted"
