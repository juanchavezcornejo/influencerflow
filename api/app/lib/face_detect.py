"""Face detection using local HOG model."""

from __future__ import annotations

from pathlib import Path


def _import_face_recognition():
    """Lazy import face_recognition so missing models don't crash at import time."""
    import warnings

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=".*face_recognition_models.*")
        import face_recognition

    return face_recognition


def detect_faces(image_path: str) -> list[dict]:
    """
    Detect faces in an image using HOG model.

    Args:
        image_path: Path to image file

    Returns:
        List of dicts with keys: top, right, bottom, left, confidence
    """
    face_recognition = _import_face_recognition()
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")

    # Load image
    try:
        image = face_recognition.load_image_file(str(path))
    except Exception as e:
        raise ValueError(f"Cannot load image: {e}") from e

    # Detect faces with HOG model (fast, local, no network)
    face_locations = face_recognition.face_locations(image, model="hog")

    # Convert to standard format with bbox coordinates
    faces = []
    for top, right, bottom, left in face_locations:
        faces.append(
            {
                "top": top,
                "right": right,
                "bottom": bottom,
                "left": left,
                "confidence": 1.0,  # HOG model doesn't return confidence
            }
        )

    return faces


def has_faces(image_path: str) -> bool:
    """Check if image contains any faces."""
    try:
        faces = detect_faces(image_path)
        return len(faces) > 0
    except Exception:
        return False
