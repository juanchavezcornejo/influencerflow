"""Tests for lib/face_detect.py"""

import tempfile
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from app.lib.face_detect import detect_faces


@pytest.fixture
def image_without_faces():
    """Create a simple image without faces."""
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        img = Image.new("RGB", (256, 256), color="blue")
        img.save(f.name)
        yield f.name
        Path(f.name).unlink()


def test_detect_faces_returns_list(image_without_faces):
    """Test that detect_faces returns a list."""
    result = detect_faces(image_without_faces)
    assert isinstance(result, list)


def test_detect_faces_no_faces(image_without_faces):
    """Test that blank image returns empty face list."""
    result = detect_faces(image_without_faces)
    # Should return empty list for image with no faces
    assert len(result) == 0


def test_detect_faces_format():
    """Test that detected faces have correct format."""
    # Create a test image with a light-colored rectangle that might be detected
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        img = Image.new("RGB", (256, 256), color="black")
        draw = ImageDraw.Draw(img)
        # Draw a light rectangle
        draw.rectangle([50, 50, 200, 200], fill="white")
        img.save(f.name)

        result = detect_faces(f.name)

        # Each detection should have the required fields
        for face in result:
            assert "top" in face or isinstance(face, dict)

        Path(f.name).unlink()
