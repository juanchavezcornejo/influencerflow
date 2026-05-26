"""Preview generation library."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from app.config import settings

# Preview tier configs (mirror of web/src/config/preview.config.ts)
PREVIEW_TIERS = {
    "thumbnail": {"longest_side": 384, "quality": 85},
    "preview": {"longest_side": 1024, "quality": 85},
    "hi_preview": {"longest_side": 1536, "quality": 85},
}


def generate(source_path: str, tier: str = "preview", dest_path: str | None = None) -> str:
    """
    Generate a preview image at a given tier.

    Args:
        source_path: Path to original image
        tier: "thumbnail", "preview", or "hi_preview"
        dest_path: Output path (optional; generates in /data/previews if not specified)

    Returns:
        Path to generated preview
    """
    source = Path(source_path)
    if not source.exists():
        raise FileNotFoundError(f"Source image not found: {source}")

    config = PREVIEW_TIERS.get(tier)
    if not config:
        raise ValueError(f"Unknown preview tier: {tier}")

    # Open image
    try:
        img = Image.open(source)
        # Correct orientation from EXIF
        try:
            from PIL import ImageOps

            img = ImageOps.exif_transpose(img)
        except Exception:
            pass  # EXIF correction is optional
    except Exception as e:
        raise ValueError(f"Cannot open image: {e}") from e

    # Calculate new dimensions preserving aspect ratio
    longest_side = config["longest_side"]
    w, h = img.size
    if w > h:
        new_w = min(w, longest_side)
        new_h = int(h * (new_w / w))
    else:
        new_h = min(h, longest_side)
        new_w = int(w * (new_h / h))

    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # Strip EXIF on thumbnails, keep on preview
    if tier == "thumbnail":
        data = list(img.getdata())
        img_without_exif = Image.new(img.mode, img.size)
        img_without_exif.putdata(data)
        img = img_without_exif

    # Determine output path
    if not dest_path:
        dest_path = str(settings.data_dir / "previews" / f"{source.stem}_{tier}.jpg")

    Path(dest_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(dest_path, "JPEG", quality=config["quality"])

    return dest_path
