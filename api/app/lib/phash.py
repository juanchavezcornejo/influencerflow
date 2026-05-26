"""Perceptual hash computation for near-duplicate detection."""

from __future__ import annotations

from pathlib import Path

from PIL import Image


def compute_phash(image_path: str, hash_size: int = 8) -> str:
    """
    Compute a perceptual hash of an image.

    Returns a 64-bit hash as a hex string. Same image always produces same hash.
    Similar images have small Hamming distance.

    Args:
        image_path: Path to image file
        hash_size: Size of hash grid (default 8 = 64 bits)

    Returns:
        Hex string representation of hash
    """
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")

    # Open image and convert to grayscale
    img = Image.open(path).convert("L")

    # Resize to hash_size x hash_size
    img = img.resize((hash_size, hash_size), Image.Resampling.LANCZOS)

    # Compute average pixel value
    pixels = list(img.getdata())
    avg = sum(pixels) / len(pixels)

    # Create hash: 1 if pixel > avg, 0 otherwise
    hash_bits = "".join("1" if pixel > avg else "0" for pixel in pixels)

    # Convert to hex
    hash_int = int(hash_bits, 2)
    return format(hash_int, f"0{hash_size * hash_size // 4}x")


def hamming_distance(hash1: str, hash2: str) -> int:
    """Compute Hamming distance between two hashes."""
    if len(hash1) != len(hash2):
        raise ValueError("Hashes must be the same length")

    # Convert hex to binary and count differing bits
    bits1 = bin(int(hash1, 16))[2:].zfill(len(hash1) * 4)
    bits2 = bin(int(hash2, 16))[2:].zfill(len(hash2) * 4)

    return sum(b1 != b2 for b1, b2 in zip(bits1, bits2, strict=False))
