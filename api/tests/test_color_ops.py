"""Tests for lib/color_ops.py"""

import pytest
from PIL import Image

from app.lib.color_ops import (
    apply_contrast,
    apply_corrections,
    apply_exposure,
    apply_highlights_shadows,
    apply_saturation,
    apply_white_balance,
)


@pytest.fixture
def test_image():
    """Create a test image."""
    return Image.new("RGB", (100, 100), color=(128, 128, 128))


def test_apply_exposure_zero(test_image):
    """Test exposure=0 returns unchanged image."""
    result = apply_exposure(test_image, 0)
    assert result.getpixel((50, 50)) == test_image.getpixel((50, 50))


def test_apply_exposure_positive(test_image):
    """Test positive exposure brightens the image."""
    result = apply_exposure(test_image, 0.5)
    # Should be brighter (higher values)
    assert result.getpixel((50, 50))[0] > test_image.getpixel((50, 50))[0]


def test_apply_contrast_zero(test_image):
    """Test contrast=0 returns unchanged image."""
    result = apply_contrast(test_image, 0)
    assert result.getpixel((50, 50)) == test_image.getpixel((50, 50))


def test_apply_saturation_zero(test_image):
    """Test saturation=0 returns unchanged image."""
    result = apply_saturation(test_image, 0)
    assert result.getpixel((50, 50)) == test_image.getpixel((50, 50))


def test_apply_white_balance_zero(test_image):
    """Test white balance with zero temp and tint returns unchanged."""
    result = apply_white_balance(test_image, temp=0, tint=0)
    assert result.getpixel((50, 50)) == test_image.getpixel((50, 50))


def test_apply_highlights_shadows_zero(test_image):
    """Test highlights/shadows with zero values returns unchanged."""
    result = apply_highlights_shadows(test_image, highlights=0, shadows=0)
    assert result.getpixel((50, 50)) == test_image.getpixel((50, 50))


def test_apply_corrections_empty_dict(test_image):
    """Test applying empty corrections dict returns copy."""
    result = apply_corrections(test_image, {})
    assert result.getpixel((50, 50)) == test_image.getpixel((50, 50))


def test_apply_corrections_multiple(test_image):
    """Test applying multiple corrections."""
    corrections = {
        "exposure": 0.2,
        "contrast": 0.1,
        "saturation": -0.05,
    }
    result = apply_corrections(test_image, corrections)
    # Should have been modified
    assert result.size == test_image.size
    assert result.mode == "RGB"
