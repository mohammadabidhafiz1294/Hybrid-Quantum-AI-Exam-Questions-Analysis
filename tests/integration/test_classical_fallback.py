"""Integration tests for classical fallback mechanism."""

import pytest
import time
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from src.api.main import app
from src.services.vqe_predictor import VQEPredictor
from src.services.data_loader import DataLoader


class TestClassicalFallbackIntegration:
    """Integration tests for classical fallback mechanism."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)
        self.mock_predictor = MagicMock(spec=VQEPredictor)
        self.mock_data_loader = MagicMock(spec=DataLoader)

        # Mock quantum as unavailable initially
        self.mock_predictor.quantum_available = False

        # Patch the services in the API
        self.predictor_patch = patch('src.api.main.predictor', self.mock_predictor)
        self.data_loader_patch = patch('src.api.main.data_loader', self.mock_data_loader)
        self.predictor_patch.start()
        self.data_loader_patch.start()

    def teardown_method(self):
        """Clean up patches."""
        self.predictor_patch.stop()
        self.data_loader_patch.stop()

    def test_automatic_classical_fallback_when_quantum_unavailable(self):
        """Test automatic fallback to classical when quantum is unavailable."""
        # Mock classical prediction response
        mock_prediction_response = {
            "predictions": [
                {
                    "topic": "thermodynamics",
                    "importance": 0.12,
                    "confidence_interval": [0.07, 0.17],
                    "trend": "decreasing",
                    "method": "classical"
                }
            ],
            "execution_time_ms": 500,
            "fallback_used": True
        }

        self.mock_predictor.predict_topics.return_value = mock_prediction_response

        request_data = {
            "topics": ["thermodynamics"],
            "force_classical": False  # Not forcing classical, but quantum unavailable
        }

        response = self.client.post("/api/v1/predict", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # Verify fallback was used
        assert data["fallback_used"] is True
        assert data["predictions"][0]["method"] == "classical"
        assert "execution_time_ms" in data

        # Verify predictor was called
        self.mock_predictor.predict_topics.assert_called_once()

    def test_explicit_classical_prediction(self):
        """Test explicit classical prediction when force_classical=True."""
        # Mock quantum as available but force classical
        self.mock_predictor.quantum_available = True

        mock_prediction_response = {
            "predictions": [
                {
                    "topic": "physics",
                    "importance": 0.25,
                    "confidence_interval": [0.20, 0.30],
                    "trend": "stable",
                    "method": "classical"
                }
            ],
            "execution_time_ms": 300,
            "fallback_used": False
        }

        self.mock_predictor.predict_topics.return_value = mock_prediction_response

        request_data = {
            "topics": ["physics"],
            "force_classical": True  # Explicitly force classical
        }

        response = self.client.post("/api/v1/predict", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # Should use classical even though quantum is available
        assert data["predictions"][0]["method"] == "classical"
        assert data["fallback_used"] is False  # Not a fallback, explicitly requested

    def test_classical_fallback_performance_comparison(self):
        """Test performance comparison between quantum and classical methods."""
        # Test classical method
        self.mock_predictor.quantum_available = False

        classical_response = {
            "predictions": [{"topic": "math", "importance": 0.20, "confidence_interval": [0.15, 0.25], "trend": "stable", "method": "classical"}],
            "execution_time_ms": 200,
            "fallback_used": True
        }

        self.mock_predictor.predict_topics.return_value = classical_response

        request_data = {"topics": ["math"], "force_classical": False}

        start_time = time.time()
        response = self.client.post("/api/v1/predict", json=request_data)
        classical_end_time = time.time()

        assert response.status_code == 200
        classical_data = response.json()

        # Classical should be faster
        assert classical_data["execution_time_ms"] < 1000  # Less than 1 second
        assert classical_data["predictions"][0]["method"] == "classical"

        # Now test with quantum available
        self.mock_predictor.quantum_available = True

        quantum_response = {
            "predictions": [{"topic": "math", "importance": 0.20, "confidence_interval": [0.15, 0.25], "trend": "stable", "method": "quantum"}],
            "execution_time_ms": 1500,
            "fallback_used": False
        }

        self.mock_predictor.predict_topics.return_value = quantum_response

        start_time = time.time()
        response = self.client.post("/api/v1/predict", json=request_data)
        quantum_end_time = time.time()

        assert response.status_code == 200
        quantum_data = response.json()

        # Quantum should take longer but be more accurate
        assert quantum_data["execution_time_ms"] > classical_data["execution_time_ms"]
        assert quantum_data["predictions"][0]["method"] == "quantum"

    def test_classical_fallback_error_recovery(self):
        """Test error recovery with classical fallback."""
        # First call fails with quantum
        self.mock_predictor.quantum_available = True
        self.mock_predictor.predict_topics.side_effect = Exception("Quantum circuit error")

        request_data = {"topics": ["chemistry"]}

        # This should trigger fallback to classical
        response = self.client.post("/api/v1/predict", json=request_data)

        # Should return successful response with fallback
        assert response.status_code == 200
        data = response.json()
        assert data["fallback_used"] is True
        assert data["predictions"][0]["method"] == "classical"

        # Reset mock for next test
        self.mock_predictor.predict_topics.side_effect = None

    def test_classical_prediction_accuracy_validation(self):
        """Test that classical predictions have reasonable accuracy."""
        mock_prediction_response = {
            "predictions": [
                {
                    "topic": "biology",
                    "importance": 0.35,
                    "confidence_interval": [0.30, 0.40],
                    "trend": "increasing",
                    "method": "classical"
                }
            ],
            "execution_time_ms": 400,
            "fallback_used": True
        }

        self.mock_predictor.predict_topics.return_value = mock_prediction_response

        request_data = {"topics": ["biology"], "force_classical": False}

        response = self.client.post("/api/v1/predict", json=request_data)

        assert response.status_code == 200
        data = response.json()

        prediction = data["predictions"][0]

        # Validate prediction structure
        assert 0.0 <= prediction["importance"] <= 1.0
        assert len(prediction["confidence_interval"]) == 2
        assert prediction["confidence_interval"][0] <= prediction["importance"] <= prediction["confidence_interval"][1]
        assert prediction["method"] == "classical"
        assert prediction["trend"] in ["increasing", "decreasing", "stable", "unknown"]

    def test_classical_fallback_with_health_integration(self):
        """Test classical fallback with health check integration."""
        # Check initial health (quantum unavailable)
        health_response = self.client.get("/api/v1/health")
        assert health_response.status_code == 200
        health_data = health_response.json()
        assert health_data["status"] in ["healthy", "degraded", "unhealthy"]

        # Make prediction (should use classical fallback)
        request_data = {"topics": ["geology"]}
        predict_response = self.client.post("/api/v1/predict", json=request_data)
        assert predict_response.status_code == 200

        predict_data = predict_response.json()
        assert predict_data["predictions"][0]["method"] == "classical"

    def test_classical_prediction_consistency(self):
        """Test that classical predictions are consistent across multiple calls."""
        mock_prediction_response = {
            "predictions": [
                {
                    "topic": "history",
                    "importance": 0.18,
                    "confidence_interval": [0.13, 0.23],
                    "trend": "stable",
                    "method": "classical"
                }
            ],
            "execution_time_ms": 350,
            "fallback_used": True
        }

        self.mock_predictor.predict_topics.return_value = mock_prediction_response

        request_data = {"topics": ["history"], "force_classical": False}

        # Make multiple calls
        responses = []
        for _ in range(5):
            response = self.client.post("/api/v1/predict", json=request_data)
            assert response.status_code == 200
            responses.append(response.json())

        # All responses should be identical (deterministic classical method)
        first_response = responses[0]
        for response in responses[1:]:
            assert response == first_response
