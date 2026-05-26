"""EXIF extraction from images."""

from __future__ import annotations

from contextlib import suppress
from datetime import datetime
from pathlib import Path

import piexif
from PIL import Image
from PIL.ExifTags import TAGS


def extract_exif(image_path: str) -> dict:
    """
    Extract EXIF data from an image.

    Returns dict with: datetime_original, gps_lat, gps_lng, camera, lens, iso, aperture, shutter.
    """
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")

    exif_data = {
        "datetime_original": None,
        "gps_lat": None,
        "gps_lng": None,
        "camera": None,
        "lens": None,
        "iso": None,
        "aperture": None,
        "shutter": None,
    }

    try:
        # Try using piexif first (better for EXIF data)
        exif_dict = piexif.load(str(path))

        # DateTime
        if "0th" in exif_dict:
            dt_bytes = exif_dict["0th"].get(piexif.ImageIFD.DateTime)
            if dt_bytes:
                try:
                    dt_str = dt_bytes.decode("utf-8").strip()
                    exif_data["datetime_original"] = datetime.strptime(
                        dt_str, "%Y:%m:%d %H:%M:%S"
                    ).isoformat()
                except Exception:
                    pass

        # GPS coordinates
        if "GPS" in exif_dict:
            gps = exif_dict["GPS"]
            try:
                lat_ref = gps[piexif.GPSIFD.GPSLatitudeRef].decode()
                lat = gps[piexif.GPSIFD.GPSLatitude]
                lat_decimal = (
                    lat[0][0] / lat[0][1]
                    + lat[1][0] / (lat[1][1] * 60)
                    + lat[2][0] / (lat[2][1] * 3600)
                )
                if lat_ref == "S":
                    lat_decimal *= -1
                exif_data["gps_lat"] = lat_decimal

                lng_ref = gps[piexif.GPSIFD.GPSLongitudeRef].decode()
                lng = gps[piexif.GPSIFD.GPSLongitude]
                lng_decimal = (
                    lng[0][0] / lng[0][1]
                    + lng[1][0] / (lng[1][1] * 60)
                    + lng[2][0] / (lng[2][1] * 3600)
                )
                if lng_ref == "W":
                    lng_decimal *= -1
                exif_data["gps_lng"] = lng_decimal
            except Exception:
                pass

        # Camera make/model
        if "0th" in exif_dict:
            model = exif_dict["0th"].get(piexif.ImageIFD.Model)
            if model:
                with suppress(Exception):
                    exif_data["camera"] = model.decode("utf-8").strip()

        # ISO
        if "Exif" in exif_dict:
            iso = exif_dict["Exif"].get(piexif.ExifIFD.ISOSpeedRatings)
            if iso:
                exif_data["iso"] = int(iso)

            # Aperture
            aperture = exif_dict["Exif"].get(piexif.ExifIFD.FNumber)
            if aperture:
                try:
                    f_num = aperture[0] / aperture[1]
                    exif_data["aperture"] = f"f/{f_num:.1f}"
                except Exception:
                    pass

            # Shutter speed
            shutter = exif_dict["Exif"].get(piexif.ExifIFD.ExposureTime)
            if shutter:
                try:
                    exposure = shutter[0] / shutter[1]
                    if exposure < 1:
                        exif_data["shutter"] = f"1/{int(1 / exposure)}"
                    else:
                        exif_data["shutter"] = f"{exposure:.1f}s"
                except Exception:
                    pass

    except Exception:
        # Fall back to Pillow EXIF
        try:
            img = Image.open(path)
            exif = img.getexif()
            if exif:
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    if tag == "DateTime":
                        with suppress(Exception):
                            exif_data["datetime_original"] = datetime.strptime(
                                value, "%Y:%m:%d %H:%M:%S"
                            ).isoformat()
        except Exception:
            pass

    return exif_data
