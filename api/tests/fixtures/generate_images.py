"""Generate test fixture images with EXIF metadata for Playwright and unit tests.

Creates 6 JPEG images with distinct dates, times, and GPS coordinates so the
deterministic grouping service can produce meaningful groups. All images are
100x100 solid-color squares with embedded EXIF.

Group 1 (same day, same location, <2h gap): Rome Colosseum morning shots
Group 2 (same day, different location >500m): Rome Vatican afternoon
Group 3 (next day): Florence
"""

from __future__ import annotations

import os
from datetime import datetime

import piexif
from PIL import Image

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__)) + "/images"

FIXTURES = [
    {
        "filename": "rome_colosseum_01.jpg",
        "color": (200, 150, 100),  # warm beige
        "datetime": "2024:05:15 09:30:00",
        "lat": 41.8902,
        "lng": 12.4922,
    },
    {
        "filename": "rome_colosseum_02.jpg",
        "color": (180, 130, 90),
        "datetime": "2024:05:15 09:45:00",
        "lat": 41.8903,
        "lng": 12.4923,
    },
    {
        "filename": "rome_colosseum_03.jpg",
        "color": (220, 170, 110),
        "datetime": "2024:05:15 10:15:00",
        "lat": 41.8904,
        "lng": 12.4921,
    },
    {
        "filename": "rome_vatican_01.jpg",
        "color": (100, 140, 180),  # cool blue
        "datetime": "2024:05:15 14:00:00",
        "lat": 41.9022,
        "lng": 12.4533,
    },
    {
        "filename": "rome_vatican_02.jpg",
        "color": (110, 150, 190),
        "datetime": "2024:05:15 14:30:00",
        "lat": 41.9023,
        "lng": 12.4534,
    },
    {
        "filename": "florence_duomo_01.jpg",
        "color": (150, 100, 80),  # terracotta
        "datetime": "2024:05:16 11:00:00",
        "lat": 43.7731,
        "lng": 11.2558,
    },
]


def _decimal_to_dms(decimal: float) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
    """Convert decimal degrees to EXIF DMS format (degrees, minutes, seconds)."""
    sign = 1 if decimal >= 0 else -1
    decimal = abs(decimal)
    degrees = int(decimal)
    minutes_float = (decimal - degrees) * 60
    minutes = int(minutes_float)
    seconds_float = (minutes_float - minutes) * 60
    seconds = int(seconds_float * 100)  # EXIF uses rational (numerator, denominator)
    return (
        (degrees * sign, 1),
        (minutes, 1),
        (seconds, 100),
    )


def _build_exif(fixture: dict) -> bytes:
    """Build EXIF bytes with datetime and GPS for a fixture."""
    dt = datetime.strptime(fixture["datetime"], "%Y:%m:%d %H:%M:%S")
    dt_str = dt.strftime("%Y:%m:%d %H:%M:%S")

    zeroth = {
        piexif.ImageIFD.DateTime: dt_str.encode("utf-8"),
        piexif.ImageIFD.Make: b"Canon",
        piexif.ImageIFD.Model: b"EOS R5",
    }

    exif = {
        piexif.ExifIFD.DateTimeOriginal: dt_str.encode("utf-8"),
        piexif.ExifIFD.ISOSpeedRatings: 400,
        piexif.ExifIFD.FNumber: (56, 10),  # f/5.6
        piexif.ExifIFD.ExposureTime: (1, 250),  # 1/250s
    }

    gps = {
        piexif.GPSIFD.GPSLatitudeRef: "N",
        piexif.GPSIFD.GPSLatitude: _decimal_to_dms(fixture["lat"]),
        piexif.GPSIFD.GPSLongitudeRef: "E",
        piexif.GPSIFD.GPSLongitude: _decimal_to_dms(fixture["lng"]),
    }

    exif_dict = {"0th": zeroth, "Exif": exif, "GPS": gps}
    return piexif.dump(exif_dict)


def main() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for fixture in FIXTURES:
        path = os.path.join(OUTPUT_DIR, fixture["filename"])
        img = Image.new("RGB", (200, 150), fixture["color"])
        exif_bytes = _build_exif(fixture)
        img.save(path, "JPEG", quality=85, exif=exif_bytes)
        print(f"Created {fixture['filename']} — {fixture['datetime']} ({fixture['color']})")
    print(f"\nDone. {len(FIXTURES)} images in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
