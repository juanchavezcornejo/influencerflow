#!/usr/bin/env python3
"""Generate sample 3D LUT files for color correction presets."""

from __future__ import annotations

from pathlib import Path


def generate_lut(
    output_path: str, title: str, red_shift: float, green_shift: float, blue_shift: float
) -> None:
    """
    Generate a simple 3D LUT file.

    red_shift, green_shift, blue_shift: values in range [0.0, 2.0] where 1.0 is identity
    """
    size = 17
    lines = [f'TITLE "{title}"', f"LUT_3D_SIZE {size}"]

    for r_idx in range(size):
        for g_idx in range(size):
            for b_idx in range(size):
                r_in = r_idx / (size - 1)
                g_in = g_idx / (size - 1)
                b_in = b_idx / (size - 1)

                # Apply shifts
                r_out = min(1.0, r_in * red_shift)
                g_out = min(1.0, g_in * green_shift)
                b_out = min(1.0, b_in * blue_shift)

                lines.append(f"{r_out:.6f} {g_out:.6f} {b_out:.6f}")

    Path(output_path).write_text("\n".join(lines))
    print(f"Generated {output_path}")


if __name__ == "__main__":
    base_dir = Path(__file__).parent.parent / "assets" / "luts"
    base_dir.mkdir(parents=True, exist_ok=True)

    # Golden Hour Warm: boost red, reduce blue (warm shift)
    generate_lut(
        str(base_dir / "golden_hour.cube"),
        "Golden Hour Warm",
        red_shift=1.2,  # boost reds
        green_shift=1.0,  # neutral greens
        blue_shift=0.85,  # reduce blues
    )

    # Editorial Neutral: slight contrast boost via S-curve simulation
    # We'll do this by slightly boosting mids and reducing extremes
    generate_lut(
        str(base_dir / "editorial_neutral.cube"),
        "Editorial Neutral",
        red_shift=1.05,  # subtle lift
        green_shift=1.05,  # subtle lift
        blue_shift=1.05,  # subtle lift
    )

    # Cinematic Moody: cool tones, lifted blacks
    generate_lut(
        str(base_dir / "cinematic_moody.cube"),
        "Cinematic Moody",
        red_shift=0.95,  # slightly reduce reds
        green_shift=1.0,  # neutral greens
        blue_shift=1.1,  # boost blues (cooler)
    )
