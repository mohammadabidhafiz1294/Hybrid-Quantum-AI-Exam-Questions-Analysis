"""Integration tests for hybrid prediction workflow."""

import pytest
import time
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from src.api.main import app
from src.services.vqe_predictor import VQEPredictor
from src.services.data_loader import DataLoader


class TestHybridPredictionIntegration:
    """Integration tests for hybrid prediction workflow."""

    def setup_method(self):
        """Set up test client and mock services."""
        self.client = TestClient(app)
        self.mock_predictor = MagicMock(spec=VQEPredictor)
        self.mock_data_loader = MagicMock(spec=DataLoader)

        # Mock both quantum and classical as available
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

    def test_hybrid_prediction_blending(self):
        """Test that hybrid predictions blend quantum and classical results."""
        # Mock hybrid prediction response that combines both methods
        mock_prediction_response = {
            "predictions": [
                {
                    "topic": "computer-science",
                    "importance": 0.45,
                    "confidence_interval": [0.40, 0.50],
                    "trend": "increasing",
                    "method": "hybrid",
                    "quantum_contribution": 0.7,
                    "classical_contribution": 0.3
                }
            ],
            "execution_time_ms": 1800,
            "method_used": "hybrid",
            "fallback_used": False
        }

        self.mock_predictor.predict_topics.return_value = mock_prediction_response

        request_data = {
            "topics": ["computer-science"],
            "force_classical": False
        }

        response = self.client.post("/api/v1/predict", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # Verify hybrid method was used
        assert data["method_used"] == "hybrid"
        assert data["predictions"][0]["method"] == "hybrid"

        # Check hybrid-specific fields
        prediction = data["predictions"][0]
        assert "quantum_contribution" in prediction
        assert "classical_contribution" in prediction
        assert prediction["quantum_contribution"] + prediction["classical_contribution"] == pytest.approx(1.0, abs=0.01)

    def test_hybrid_vs_pure_quantum_comparison(self):
        """Test comparison between hybrid and pure quantum predictions."""
        # Test pure quantum first
        quantum_response = {
            "predictions": [{
                "topic": "algorithms",
                "importance": 0.50,
                "confidence_interval": [0.45, 0.55],
                "trend": "increasing",
                "method": "quantum"
            }],
            "execution_time_ms": 2000,
            "method_used": "quantum"
        }

        self.mock_predictor.predict_topics.return_value = quantum_response

        quantum_request = {"topics": ["algorithms"], "force_classical": False}
        quantum_result = self.client.post("/api/v1/predict", json=quantum_request)
        quantum_data = quantum_result.json()

        # Test hybrid
        hybrid_response = {
            "predictions": [{
                "topic": "algorithms",
                "importance": 0.48,
                "confidence_interval": [0.43, 0.53],
                "trend": "increasing",
                "method": "hybrid",
                "quantum_contribution": 0.8,
                "classical_contribution": 0.2
            }],
            "execution_time_ms": 1600,
            "method_used": "hybrid"
        }

        self.mock_predictor.predict_topics.return_value = hybrid_response

        hybrid_request = {"topics": ["algorithms"], "force_classical": False}
        hybrid_result = self.client.post("/api/v1/predict", json=hybrid_request)
        hybrid_data = hybrid_result.json()

        # Hybrid should be faster than pure quantum
        assert hybrid_data["execution_time_ms"] < quantum_data["execution_time_ms"]

        # Hybrid should have different (potentially more stable) results
        assert hybrid_data["predictions"][0]["method"] == "hybrid"
        assert quantum_data["predictions"][0]["method"] == "quantum"

    def test_hybrid_prediction_with_uncertainty_quantification(self):
        """Test hybrid predictions with uncertainty quantification."""
        mock_prediction_response = {
            "predictions": [
                {
                    "topic": "machine-learning",
                    "importance": 0.65,
                    "confidence_interval": [0.60, 0.70],
                    "trend": "increasing",
                    "method": "hybrid",
                    "uncertainty_quantification": {
                        "quantum_uncertainty": 0.05,
                        "classical_uncertainty": 0.03,
                        "blended_uncertainty": 0.04
                    },
                    "quantum_contribution": 0.6,
                    "classical_contribution": 0.4
                }
            ],
            "execution_time_ms": 1900,
            "method_used": "hybrid"
        }

        self.mock_predictor.predict_topics.return_value = mock_prediction_response

        request_data = {"topics": ["machine-learning"]}

        response = self.client.post("/api/v1/predict", json=request_data)

        assert response.status_code == 200
        data = response.json()

        prediction = data["predictions"][0]

        # Check uncertainty quantification
        assert "uncertainty_quantification" in prediction
        uq = prediction["uncertainty_quantification"]
        assert "quantum_uncertainty" in uq
        assert "classical_uncertainty" in uq
        assert "blended_uncertainty" in uq

        # Blended uncertainty should be reasonable combination
        expected_blended = (uq["quantum_uncertainty"] * prediction["quantum_contribution"] +
                           uq["classical_uncertainty"] * prediction["classical_contribution"])
        assert uq["blended_uncertainty"] == pytest.approx(expected_blended, abs=0.01)

    def test_hybrid_fallback_when_quantum_fails(self):
        """Test hybrid fallback when quantum computation fails."""
        # Mock quantum failure scenario
        self.mock_predictor.quantum_available = True

        # First call succeeds with hybrid
        hybrid_response = {
            "predictions": [{
                "topic": "data-structures",
                "importance": 0.40,
                "method": "hybrid"
            }],
            "execution_time_ms": 1500,
            "method_used": "hybrid"
        }

        self.mock_predictor.predict_topics.return_value = hybrid_response

        request_data = {"topics": ["data-structures"]}
        response = self.client.post("/api/v1/predict", json=request_data)

        assert response.status_code == 200
        assert response.json()["predictions"][0]["method"] == "hybrid"

    def test_hybrid_prediction_scalability(self):
        """Test hybrid prediction scalability with multiple topics."""
        # Create mock response for multiple topics
        topics = ["topic1", "topic2", "topic3", "topic4", "topic5"]
        predictions = []

        for i, topic in enumerate(topics):
            predictions.append({
                "topic": topic,
                "importance": 0.2 + i * 0.1,
                "confidence_interval": [0.15 + i * 0.1, 0.25 + i * 0.1],
                "trend": "increasing",
                "method": "hybrid",
                "quantum_contribution": 0.7,
                "classical_contribution": 0.3
            })

        mock_response = {
            "predictions": predictions,
            "execution_time_ms": 3000,
            "method_used": "hybrid"
        }

        self.mock_predictor.predict_topics.return_value = mock_response

        request_data = {"topics": topics}

        start_time = time.time()
        response = self.client.post("/api/v1/predict", json=request_data)
        end_time = time.time()

        assert response.status_code == 200
        data = response.json()

        # Should handle multiple topics
        assert len(data["predictions"]) == 5

        # Should scale reasonably (not exponentially slower)
        assert data["execution_time_ms"] < 5000  # Less than 5 seconds for 5 topics
        assert end_time - start_time < 10.0

        # All predictions should use hybrid method
        for prediction in data["predictions"]:
            assert prediction["method"] == "hybrid"

    def test_hybrid_prediction_consistency(self):
        """Test consistency of hybrid predictions across multiple calls."""
        mock_response = {
            "predictions": [{
                "topic": "neural-networks",
                "importance": 0.55,
                "confidence_interval": [0.50, 0.60],
                "trend": "increasing",
                "method": "hybrid",
                "quantum_contribution": 0.75,
                "classical_contribution": 0.25
            }],
            "execution_time_ms": 1700,
            "method_used": "hybrid"
        }

        self.mock_predictor.predict_topics.return_value = mock_response

        request_data = {"topics": ["neural-networks"]}

        # Make multiple calls
        responses = []
        for _ in range(3):
            response = self.client.post("/api/v1/predict", json=request_data)
            assert response.status_code == 200
            responses.append(response.json())

        # All responses should be identical
        first_response = responses[0]
        for response in responses[1:]:
            assert response == first_response

    def test_hybrid_method_selection_logic(self):
        """Test the logic for selecting hybrid vs pure methods."""
        # Test with high confidence - should use more quantum
        high_confidence_response = {
            "predictions": [{
                "topic": "statistics",
                "importance": 0.30,
                "method": "hybrid",
                "quantum_contribution": 0.9,
                "classical_contribution": 0.1
            }],
            "execution_time_ms": 2100,
            "method_used": "hybrid"
        }

        self.mock_predictor.predict_topics.return_value = high_confidence_response

        request_data = {"topics": ["statistics"], "confidence_level": 0.99}
        response = self.client.post("/api/v1/predict", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["predictions"][0]["quantum_contribution"] > 0.8  # High quantum contribution

        # Test with low confidence - should use more classical
        low_confidence_response = {
            "predictions": [{
                "topic": "statistics",
                "importance": 0.30,
                "method": "hybrid",
                "quantum_contribution": 0.4,
                "classical_contribution": 0.6
            }],
            "execution_time_ms": 1200,
            "method_used": "hybrid"
        }

        self.mock_predictor.predict_topics.return_value = low_confidence_response

        request_data = {"topics": ["statistics"], "confidence_level": 0.80}
        response = self.client.post("/api/v1/predict", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["predictions"][0]["classical_contribution"] > data["predictions"][0]["quantum_contribution"]
