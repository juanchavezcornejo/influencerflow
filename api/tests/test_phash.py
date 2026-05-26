"""Tests for lib/phash.py"""

import tempfile
from pathlib import Path

import pytest
from PIL import Image

from app.lib.phash import compute_phash, hamming_distance


@pytest.fixture
def temp_image():
    """Create a temporary test image."""
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        # Create a simple 256x256 image with a pattern
        img = Image.new("RGB", (256, 256), color="red")
        img.save(f.name)
        yield f.name
        Path(f.name).unlink()


def test_compute_phash_returns_hex_string(temp_image):
    """Test that compute_phash returns a 16-char hex string."""
    result = compute_phash(temp_image)
    assert isinstance(result, str)
    assert len(result) == 16
    assert all(c in "0123456789abcdef" for c in result)


def test_identical_images_same_hash(temp_image):
    """Test that identical images produce identical hashes."""
    hash1 = compute_phash(temp_image)
    hash2 = compute_phash(temp_image)
    assert hash1 == hash2


def test_hamming_distance_same_string():
    """Test Hamming distance between identical strings is 0."""
    hash1 = "aaaaaaaaaaaaaaaa"
    hash2 = "aaaaaaaaaaaaaaaa"
    assert hamming_distance(hash1, hash2) == 0


def test_hamming_distance_different_bits():
    """Test Hamming distance calculation."""
    hash1 = "0000000000000000"
    hash2 = "1111111111111111"
    # Each hex digit is 4 bits, so 16 * 4 = 64 bits differ
    distance = hamming_distance(hash1, hash2)
    assert distance == 64


def test_hamming_distance_partial_difference():
    """Test Hamming distance with partial difference."""
    hash1 = "ffffffffffffffff"
    hash2 = "fffffffffffffff0"  # Last digit differs by 1 bit
    distance = hamming_distance(hash1, hash2)
    assert distance == 1
