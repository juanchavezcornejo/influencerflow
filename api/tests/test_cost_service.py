"""Tests for cost_service.py"""

from app.services.cost_service import CostEstimator


def test_estimate_object_removal():
    """Test cost estimation for object removal."""
    estimate = CostEstimator.estimate("object_removal", {})
    assert estimate["dollars"] == CostEstimator.REPLICATE_LAMA
    assert estimate["model"] == "lama"


def test_estimate_color_ai():
    """Test cost estimation for AI color adjustment."""
    estimate = CostEstimator.estimate("color_ai", {})
    assert estimate["model"] == "claude-opus-4-7"
    assert estimate["dollars"] > 0
    assert estimate["tokens_in"] > 0
    assert estimate["tokens_out"] > 0


def test_estimate_description():
    """Test cost estimation for caption generation."""
    estimate = CostEstimator.estimate("description", {})
    assert estimate["model"] == "claude-opus-4-7"
    assert estimate["dollars"] > 0


def test_estimate_nima():
    """Test cost estimation for NIMA scoring."""
    estimate = CostEstimator.estimate("nima", {"num_images": 5})
    assert estimate["dollars"] == 0.005
    assert estimate["model"] == "nima"


def test_estimate_unknown_operation():
    """Test cost estimation for unknown operation."""
    estimate = CostEstimator.estimate("unknown_op", {})
    assert estimate["dollars"] == 0.0
    assert estimate["model"] == "unknown"
