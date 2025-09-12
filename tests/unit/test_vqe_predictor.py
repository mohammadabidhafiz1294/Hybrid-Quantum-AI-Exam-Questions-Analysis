"""Unit tests for VQE predictor service."""

import pytest
from unittest.mock import patch

from src.services.vqe_predictor import (
    VQEPredictor,
    PredictionRequest,
    PredictionResult,
    VQEPredictionResponse,
)


class TestVQEPredictor:
    """Test cases for VQE predictor."""

    def setup_method(self):
        """Setup test fixtures."""
        self.predictor = VQEPredictor()
        self.sample_data = {
            "quantum-mechanics": [15.0, 18.0, 22.0, 25.0, 28.0],
            "linear-algebra": [20.0, 19.0, 21.0, 20.0, 22.0],
        }

    def test_initialization(self):
        """Test predictor initialization."""
        assert self.predictor.max_qubits == 6
        assert self.predictor.max_iterations == 100
        assert isinstance(self.predictor.quantum_available, bool)

    def test_classical_prediction(self):
        """Test classical prediction method."""
        request = PredictionRequest(topics=["quantum-mechanics"], force_classical=True)

        response = self.predictor.predict_topics(request, self.sample_data)

        assert isinstance(response, VQEPredictionResponse)
        assert len(response.predictions) == 1
        assert response.predictions[0].topic == "quantum-mechanics"
        assert 0.0 <= response.predictions[0].importance <= 1.0
        assert response.predictions[0].method == "classical"
        assert response.execution_time_ms >= 0

    def test_multiple_topics_prediction(self):
        """Test prediction for multiple topics."""
        request = PredictionRequest(
            topics=["quantum-mechanics", "linear-algebra"], force_classical=True
        )

        response = self.predictor.predict_topics(request, self.sample_data)

        assert len(response.predictions) == 2
        topic_names = [p.topic for p in response.predictions]
        assert "quantum-mechanics" in topic_names
        assert "linear-algebra" in topic_names

    def test_insufficient_data_handling(self):
        """Test handling of topics with insufficient data."""
        insufficient_data = {
            "topic1": [10.0],  # Only 1 data point
            "topic2": [10.0, 12.0],  # Only 2 data points
        }

        request = PredictionRequest(topics=["topic1", "topic2"], force_classical=True)

        response = self.predictor.predict_topics(request, insufficient_data)

        # Should handle gracefully (either skip or use available data)
        assert isinstance(response, VQEPredictionResponse)

    def test_missing_topic_handling(self):
        """Test handling of topics not in historical data."""
        request = PredictionRequest(topics=["non-existent-topic"], force_classical=True)

        response = self.predictor.predict_topics(request, self.sample_data)

        # Should skip topics not in data
        assert len(response.predictions) == 0

    @patch("src.services.vqe_predictor.QISKIT_AVAILABLE", False)
    def test_quantum_unavailable_fallback(self):
        """Test fallback to classical when quantum is unavailable."""
        with patch("src.services.vqe_predictor.QISKIT_AVAILABLE", False):
            predictor = VQEPredictor()
            request = PredictionRequest(topics=["quantum-mechanics"])

            response = predictor.predict_topics(request, self.sample_data)

            assert len(response.predictions) == 1
            assert response.predictions[0].method == "classical"
            assert response.fallback_used is True

    def test_prediction_result_structure(self):
        """Test prediction result data structure."""
        request = PredictionRequest(topics=["quantum-mechanics"], force_classical=True)

        response = self.predictor.predict_topics(request, self.sample_data)
        prediction = response.predictions[0]

        assert isinstance(prediction, PredictionResult)
        assert isinstance(prediction.topic, str)
        assert isinstance(prediction.importance, float)
        assert isinstance(prediction.confidence_interval, tuple)
        assert len(prediction.confidence_interval) == 2
        assert isinstance(prediction.trend, str)
        assert isinstance(prediction.method, str)

        # Validate value ranges
        assert 0.0 <= prediction.importance <= 1.0
        assert 0.0 <= prediction.confidence_interval[0] <= 1.0
        assert 0.0 <= prediction.confidence_interval[1] <= 1.0
        assert (
            prediction.confidence_interval[0]
            <= prediction.importance
            <= prediction.confidence_interval[1]
        )


if __name__ == "__main__":
    pytest.main([__file__])
