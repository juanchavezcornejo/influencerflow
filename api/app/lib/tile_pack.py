"""Tile-pack library for bundling thumbnails into a single image."""

import hashlib

from PIL import Image, ImageDraw, ImageFont


def pack_thumbnails(thumbnail_paths: list[str], cols: int = 3, padding: int = 8) -> bytes:
    """
    Pack thumbnails into a grid image.

    Args:
        thumbnail_paths: List of paths to thumbnail images.
        cols: Number of columns in the grid.
        padding: Padding between tiles in pixels.

    Returns:
        PNG bytes of the packed image.
    """
    if not thumbnail_paths:
        return b""

    # Load all thumbnails
    images = []
    max_width = 0
    max_height = 0

    for path in thumbnail_paths:
        try:
            img = Image.open(path).convert("RGB")
            images.append(img)
            max_width = max(max_width, img.width)
            max_height = max(max_height, img.height)
        except OSError:
            # Skip invalid images
            continue

    if not images:
        return b""

    # Normalize all to same size (keeping aspect ratio)
    normalized = []
    for img in images:
        if img.width != max_width or img.height != max_height:
            # Resize to fit within max bounds, preserving aspect
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        normalized.append(img)

    # Calculate grid dimensions
    rows = (len(normalized) + cols - 1) // cols
    tile_width = max_width
    tile_height = max_height

    # Create output image
    grid_width = cols * tile_width + (cols + 1) * padding
    grid_height = rows * tile_height + (rows + 1) * padding
    grid = Image.new("RGB", (grid_width, grid_height), color=(255, 255, 255))

    # Try to load a font for numbering
    font = None
    _font_candidates = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for _font_path in _font_candidates:
        try:
            font = ImageFont.truetype(_font_path, 24)
            break
        except OSError:
            continue
    if font is None:
        font = ImageFont.load_default()

    draw = ImageDraw.Draw(grid)

    # Paste tiles and add numbers
    for idx, img in enumerate(normalized):
        row = idx // cols
        col = idx % cols
        x = padding + col * (tile_width + padding)
        y = padding + row * (tile_height + padding)

        # Paste image
        grid.paste(img, (x, y))

        # Draw number
        num_text = str(idx + 1)
        draw.text((x + 8, y + 8), num_text, fill=(0, 0, 0), font=font)

    # Convert to PNG bytes
    from io import BytesIO

    buf = BytesIO()
    grid.save(buf, format="PNG")
    return buf.getvalue()


def hash_pack_input(thumbnail_paths: list[str], cols: int, padding: int) -> str:
    """Generate a deterministic hash of the packing inputs."""
    content = f"{','.join(sorted(thumbnail_paths))}:{cols}:{padding}"
    return hashlib.sha256(content.encode()).hexdigest()
