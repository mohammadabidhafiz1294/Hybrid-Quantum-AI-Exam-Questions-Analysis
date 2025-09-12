"""Integration tests for quantum prediction workflow."""

import pytest
import time
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from src.api.main import app
from src.services.vqe_predictor import VQEPredictor
from src.services.data_loader import DataLoader


class TestQuantumPredictionIntegration:
    """Integration tests for quantum prediction workflow."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)
        self.mock_predictor = MagicMock(spec=VQEPredictor)
        self.mock_data_loader = MagicMock(spec=DataLoader)

        # Mock quantum availability
        self.mock_predictor.quantum_available = True

        # Patch the services in the API
        self.predictor_patch = patch('src.api.main.predictor', self.mock_predictor)
        self.data_loader_patch = patch('src.api.main.data_loader', self.mock_data_loader)
        self.predictor_patch.start()
        self.data_loader_patch.start()

    def teardown_method(self):
        """Clean up patches."""
        self.predictor_patch.stop()
        self.data_loader_patch.stop()

    def test_full_quantum_prediction_workflow(self):
        """Test complete quantum prediction workflow from request to response."""
        # Mock historical data
        mock_historical_data = {
            "quantum-mechanics": [15.0, 18.0, 22.0, 25.0, 28.0],
            "linear-algebra": [20.0, 19.0, 21.0, 20.0, 22.0],
        }

        # Mock predictor response
        mock_prediction_response = {
            "predictions": [
                {
                    "topic": "quantum-mechanics",
                    "importance": 0.28,
                    "confidence_interval": [0.23, 0.33],
                    "trend": "increasing",
                    "method": "quantum"
                }
            ],
            "execution_time_ms": 1500,
            "method_used": "quantum"
        }

        self.mock_predictor.predict_topics.return_value = mock_prediction_response

        # Test request
        request_data = {
            "topics": ["quantum-mechanics"],
            "historical_years": 5,
            "confidence_level": 0.95,
            "force_classical": False
        }

        start_time = time.time()
        response = self.client.post("/api/v1/predict", json=request_data)
        end_time = time.time()

        # Validate response
        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "predictions" in data
        assert "execution_time_ms" in data
        assert "fallback_used" in data

        # Check prediction content
        assert len(data["predictions"]) == 1
        prediction = data["predictions"][0]
        assert prediction["topic"] == "quantum-mechanics"
        assert "importance" in prediction
        assert "confidence_interval" in prediction
        assert prediction["method"] == "quantum"

        # Check timing (should be reasonable for quantum computation)
        assert data["execution_time_ms"] > 0
        assert end_time - start_time < 10.0  # Should complete within 10 seconds

        # Verify quantum predictor was called
        self.mock_predictor.predict_topics.assert_called_once()

    def test_quantum_prediction_with_multiple_topics(self):
        """Test quantum prediction with multiple topics."""
        mock_prediction_response = {
            "predictions": [
                {
                    "topic": "quantum-mechanics",
                    "importance": 0.28,
                    "confidence_interval": [0.23, 0.33],
                    "trend": "increasing",
                    "method": "quantum"
                },
                {
                    "topic": "linear-algebra",
                    "importance": 0.22,
                    "confidence_interval": [0.17, 0.27],
                    "trend": "stable",
                    "method": "quantum"
                }
            ],
            "execution_time_ms": 2200,
            "method_used": "quantum"
        }

        self.mock_predictor.predict_topics.return_value = mock_prediction_response

        request_data = {
            "topics": ["quantum-mechanics", "linear-algebra"],
            "force_classical": False
        }

        response = self.client.post("/api/v1/predict", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert len(data["predictions"]) == 2
        assert data["execution_time_ms"] >= 2000  # Should take longer for multiple topics
        assert data["fallback_used"] is False

    def test_quantum_prediction_error_handling(self):
        """Test quantum prediction error handling."""
        # Mock quantum predictor to raise an exception
        self.mock_predictor.predict_topics.side_effect = Exception("Quantum simulation failed")

        request_data = {
            "topics": ["quantum-mechanics"],
            "force_classical": False
        }

        response = self.client.post("/api/v1/predict", json=request_data)

        # Should gracefully fall back to classical when quantum fails
        assert response.status_code == 200
        data = response.json()
        assert data["fallback_used"] is True
        assert data["method_used"] == "classical"
        assert len(data["predictions"]) == 1
        assert data["predictions"][0]["method"] == "classical"

    def test_quantum_availability_check(self):
        """Test that quantum availability is properly checked."""
        # Mock quantum as unavailable
        self.mock_predictor.quantum_available = False

        request_data = {
            "topics": ["quantum-mechanics"],
            "force_classical": False
        }

        response = self.client.post("/api/v1/predict", json=request_data)

        # Should still work but use classical fallback
        assert response.status_code == 200
        data = response.json()
        assert len(data["predictions"]) == 1
        assert data["predictions"][0]["method"] == "classical"

    def test_quantum_prediction_data_consistency(self):
        """Test that quantum predictions are consistent with input data."""
        # Make multiple calls with same data and verify consistency
        request_data = {
            "topics": ["quantum-mechanics"],
            "historical_years": 5,
            "force_classical": False
        }

        responses = []
        for _ in range(3):
            response = self.client.post("/api/v1/predict", json=request_data)
            assert response.status_code == 200
            responses.append(response.json())

        # All responses should have same structure and reasonable values
        for data in responses:
            assert len(data["predictions"]) == 1
            prediction = data["predictions"][0]
            assert 0.0 <= prediction["importance"] <= 1.0
            assert len(prediction["confidence_interval"]) == 2
            assert prediction["confidence_interval"][0] <= prediction["importance"] <= prediction["confidence_interval"][1]

    def test_quantum_prediction_with_health_check(self):
        """Test quantum prediction workflow with health check integration."""
        # First check health
        health_response = self.client.get("/api/v1/health")
        assert health_response.status_code == 200
        health_data = health_response.json()
        assert health_data["quantum_available"] is True

        # Then make prediction with high confidence to trigger quantum
        request_data = {"topics": ["quantum-mechanics"], "confidence_level": 0.99}
        predict_response = self.client.post("/api/v1/predict", json=request_data)
        assert predict_response.status_code == 200

        # Verify quantum was used
        predict_data = predict_response.json()
        assert predict_data["predictions"][0]["method"] == "quantum"
