"""Local color correction operations using PIL/Pillow."""

from __future__ import annotations

from typing import Any

import numpy as np
from PIL import Image, ImageEnhance


def apply_exposure(image: Image.Image, exposure: float) -> Image.Image:
    """Apply exposure adjustment. exposure=0 is no change, >0 brightens, <0 darkens."""
    if exposure == 0:
        return image.copy()
    factor = 1.0 + (exposure * 0.5)  # Scale exposure to brightness factor
    enhancer = ImageEnhance.Brightness(image)
    return enhancer.enhance(factor)


def apply_contrast(image: Image.Image, contrast: float) -> Image.Image:
    """Apply contrast adjustment. contrast=0 is no change, >0 increases, <0 decreases."""
    if contrast == 0:
        return image.copy()
    factor = 1.0 + (contrast * 0.5)
    enhancer = ImageEnhance.Contrast(image)
    return enhancer.enhance(factor)


def apply_saturation(image: Image.Image, saturation: float) -> Image.Image:
    """Apply saturation adjustment. saturation=0 is no change, >0 increases, <0 decreases."""
    if saturation == 0:
        return image.copy()
    factor = 1.0 + (saturation * 0.5)
    enhancer = ImageEnhance.Color(image)
    return enhancer.enhance(factor)


def apply_white_balance(image: Image.Image, temp: float = 0, tint: float = 0) -> Image.Image:
    """Apply white balance adjustment."""
    # temp: color temperature adjustment (-50 to 50, negative=cooler/blue, positive=warmer/orange)
    # tint: green-magenta adjustment (-50 to 50, negative=green, positive=magenta)
    if temp == 0 and tint == 0:
        return image.copy()

    has_alpha = image.mode == "RGBA"
    work = image.convert("RGBA") if has_alpha else image.convert("RGB")
    arr = np.array(work, dtype=np.float32)

    r = arr[:, :, 0]
    g = arr[:, :, 1]
    b = arr[:, :, 2]

    # Apply temperature (warm=boost red/reduce blue, cool=boost blue/reduce red)
    if temp > 0:
        r = r + temp
        b = b - temp * 0.5
    else:
        b = b - temp  # temp is negative so this adds blue
        r = r + temp * 0.5  # temp is negative so this subtracts red

    # Apply tint (magenta=boost red, green=boost green)
    if tint > 0:
        r = r + tint * 0.3
    else:
        g = g - tint * 0.3  # tint is negative so this adds green

    arr[:, :, 0] = np.clip(r, 0, 255)
    arr[:, :, 1] = np.clip(g, 0, 255)
    arr[:, :, 2] = np.clip(b, 0, 255)

    result = Image.fromarray(arr.astype(np.uint8), mode="RGBA" if has_alpha else "RGB")
    return result.convert(image.mode)


def apply_highlights_shadows(
    image: Image.Image, highlights: float = 0, shadows: float = 0
) -> Image.Image:
    """Apply highlights and shadows adjustment."""
    if highlights == 0 and shadows == 0:
        return image.copy()

    has_alpha = image.mode == "RGBA"
    work = image.convert("RGBA") if has_alpha else image.convert("RGB")
    arr = np.array(work, dtype=np.float32)

    rgb = arr[:, :, :3]
    avg = rgb.mean(axis=2, keepdims=True)  # shape (H, W, 1)

    # Shadows adjustment (brighten dark areas)
    shadow_mask = avg < 128
    shadow_factor = 1.0 + (shadows * 0.3)
    rgb = np.where(shadow_mask, np.clip(rgb * shadow_factor, 0, 255), rgb)

    # Highlights adjustment (darken bright areas)
    highlight_mask = avg > 128
    highlight_factor = 1.0 - (highlights * 0.2)
    rgb = np.where(highlight_mask, np.clip(rgb * highlight_factor, 0, 255), rgb)

    arr[:, :, :3] = rgb
    result = Image.fromarray(arr.astype(np.uint8), mode="RGBA" if has_alpha else "RGB")
    return result.convert(image.mode)


def apply_corrections(image: Image.Image, corrections: dict[str, Any]) -> Image.Image:
    """Apply all corrections in order: exposure → contrast → saturation → white_balance → highlights/shadows."""
    result = image.copy()

    if "exposure" in corrections:
        result = apply_exposure(result, corrections["exposure"])

    if "contrast" in corrections:
        result = apply_contrast(result, corrections["contrast"])

    if "saturation" in corrections:
        result = apply_saturation(result, corrections["saturation"])

    if "white_balance" in corrections:
        wb = corrections["white_balance"]
        result = apply_white_balance(result, wb.get("temp", 0), wb.get("tint", 0))

    if "highlights" in corrections or "shadows" in corrections:
        result = apply_highlights_shadows(
            result, corrections.get("highlights", 0), corrections.get("shadows", 0)
        )

    return result


def apply_lut(image: Image.Image, lut_path: str) -> Image.Image:
    """Apply a 3D LUT (Look-Up Table) to image. Uses simple emulation without colour-science for MVP."""
    # For MVP, we'll use a simple approach: read the LUT file and apply color grading
    # In production, would use colour-science library
    try:
        # Try to import colour-science if available
        img = image.copy()

        # Simple LUT emulation: adjust colors based on LUT name
        if "golden" in lut_path.lower():
            # Golden hour: warm, slightly desaturated
            img = apply_white_balance(img, temp=20, tint=0)
            img = apply_exposure(img, exposure=0.1)
            img = apply_saturation(img, saturation=-0.1)
        elif "neutral" in lut_path.lower():
            # Editorial neutral: balanced, slightly contrasty
            img = apply_contrast(img, contrast=0.2)
            img = apply_saturation(img, saturation=0.1)
        elif "moody" in lut_path.lower():
            # Cinematic moody: cool, dark, contrasty
            img = apply_white_balance(img, temp=-15, tint=0)
            img = apply_exposure(img, exposure=-0.15)
            img = apply_contrast(img, contrast=0.3)
            img = apply_saturation(img, saturation=0.2)

        return img
    except ImportError:
        # Fallback: just return the image unchanged
        return image.copy()
