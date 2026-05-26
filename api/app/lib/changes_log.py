"""Render color correction parameters as human-readable bullet points."""

from __future__ import annotations


def render_changes_log(corrections_json: dict[str, object]) -> str:
    """
    Render corrections_applied_json as bullet-point text.

    Example output:
    - Color: LUT "Golden Hour" (temp +300K, saturation +8%)
    - Exposure: +0.15 EV
    """
    if not corrections_json:
        return "- Original (unedited)"

    bullets: list[str] = []

    # Determine if this is the original (no actual corrections)
    if corrections_json.get("preset") == "original":
        return "- Original (unedited)"

    # Handle preset/display name
    preset = corrections_json.get("preset", "")
    display_name = corrections_json.get("display_name", preset)
    if preset and preset != "original":
        bullets.append(f'- Color: LUT "{display_name}"')

    # Exposure
    exposure = corrections_json.get("exposure")
    if exposure and exposure != 0:
        ev_str = f"+{exposure:.2f}" if exposure > 0 else f"{exposure:.2f}"
        bullets.append(f"  • Exposure: {ev_str} EV")

    # Contrast
    contrast = corrections_json.get("contrast")
    if contrast and contrast != 1.0:
        pct = (float(contrast) - 1.0) * 100
        pct_str = f"+{pct:.0f}%" if pct > 0 else f"{pct:.0f}%"
        bullets.append(f"  • Contrast: {pct_str}")

    # White balance (temperature and tint)
    temp = corrections_json.get("temp")
    tint = corrections_json.get("tint")
    if temp or tint:
        wb_parts = []
        if temp and temp != 0:
            temp_str = f"+{temp:.0f}K" if temp > 0 else f"{temp:.0f}K"
            wb_parts.append(f"temp {temp_str}")
        if tint and tint != 0:
            tint_str = f"+{tint:.0f}" if tint > 0 else f"{tint:.0f}"
            wb_parts.append(f"tint {tint_str}")

        if wb_parts:
            bullets.append(f"  • White balance: {', '.join(wb_parts)}")

    # HSL adjustments
    saturation = corrections_json.get("saturation")
    hue = corrections_json.get("hue")
    lightness = corrections_json.get("lightness")

    hsl_parts = []
    if saturation and saturation != 1.0:
        sat_pct = (float(saturation) - 1.0) * 100
        sat_str = f"+{sat_pct:.0f}%" if sat_pct > 0 else f"{sat_pct:.0f}%"
        hsl_parts.append(f"saturation {sat_str}")

    if hue and hue != 0:
        hue_str = f"+{hue:.0f}°" if hue > 0 else f"{hue:.0f}°"
        hsl_parts.append(f"hue {hue_str}")

    if lightness and lightness != 0:
        light_str = f"+{lightness:.2f}" if lightness > 0 else f"{lightness:.2f}"
        hsl_parts.append(f"luminosity {light_str}")

    if hsl_parts:
        bullets.append(f"  • HSL: {', '.join(hsl_parts)}")

    # Highlights and shadows
    highlights = corrections_json.get("highlights")
    shadows = corrections_json.get("shadows")

    if highlights or shadows:
        hl_parts = []
        if highlights and highlights != 0:
            hl_str = f"+{highlights:.2f}" if highlights > 0 else f"{highlights:.2f}"
            hl_parts.append(f"highlights {hl_str}")

        if shadows and shadows != 0:
            sh_str = f"+{shadows:.2f}" if shadows > 0 else f"{shadows:.2f}"
            hl_parts.append(f"shadows {sh_str}")

        if hl_parts:
            bullets.append(f"  • Tones: {', '.join(hl_parts)}")

    # If no bullets were added (shouldn't happen), return a default
    if not bullets:
        bullets.append("- Original (unedited)")

    return "\n".join(bullets)
