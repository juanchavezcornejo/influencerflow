"""Tests for tile-pack library."""

import tempfile
from pathlib import Path

import pytest
from PIL import Image

from app.lib.tile_pack import hash_pack_input, pack_thumbnails


@pytest.fixture
def sample_images():
    """Create sample test images."""
    temp_dir = tempfile.mkdtemp()
    images = []

    for i in range(6):
        img = Image.new("RGB", (512, 384), color=(100 + i * 20, 150, 200))
        path = Path(temp_dir) / f"img_{i}.jpg"
        img.save(path)
        images.append(str(path))

    yield images

    # Cleanup
    import shutil

    shutil.rmtree(temp_dir)


def test_pack_thumbnails_creates_png(sample_images):
    """Test that pack_thumbnails returns valid PNG bytes."""
    result = pack_thumbnails(sample_images, cols=3, padding=8)

    assert isinstance(result, bytes)
    assert result[:4] == b"\x89PNG"  # PNG magic number


def test_pack_empty_list():
    """Test packing empty list returns empty bytes."""
    result = pack_thumbnails([], cols=3, padding=8)
    assert result == b""


def test_pack_with_different_cols(sample_images):
    """Test packing with different column counts."""
    result_2cols = pack_thumbnails(sample_images, cols=2, padding=8)
    result_3cols = pack_thumbnails(sample_images, cols=3, padding=8)

    assert isinstance(result_2cols, bytes)
    assert isinstance(result_3cols, bytes)
    assert result_2cols != result_3cols


def test_hash_pack_input_deterministic():
    """Test that hash is deterministic."""
    paths = ["a.jpg", "b.jpg", "c.jpg"]
    hash1 = hash_pack_input(paths, 3, 8)
    hash2 = hash_pack_input(paths, 3, 8)

    assert hash1 == hash2


def test_hash_pack_input_changes_with_params():
    """Test that hash changes with different params."""
    paths = ["a.jpg", "b.jpg"]
    hash_3cols = hash_pack_input(paths, 3, 8)
    hash_2cols = hash_pack_input(paths, 2, 8)

    assert hash_3cols != hash_2cols
