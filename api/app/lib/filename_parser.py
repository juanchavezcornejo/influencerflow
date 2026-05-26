"""Filename pattern parser."""

from __future__ import annotations

import re
from pathlib import Path

import yaml


def load_patterns() -> dict:
    """Load filename patterns from config."""
    config_path = Path(__file__).parent.parent.parent / "config" / "filename_patterns.yaml"
    if not config_path.exists():
        return {"patterns": [], "folder_patterns": []}

    with open(config_path) as f:
        config = yaml.safe_load(f) or {}
    return config


_PATTERNS_CACHE = None


def _get_patterns() -> dict:
    global _PATTERNS_CACHE
    if _PATTERNS_CACHE is None:
        _PATTERNS_CACHE = load_patterns()
    return _PATTERNS_CACHE


def parse(filename: str) -> dict | None:
    """
    Parse filename against known patterns.

    Returns dict with: pattern_name, date, sequence
    Or None if no pattern matches.
    """
    config = _get_patterns()
    patterns = config.get("patterns", [])

    for pattern_def in patterns:
        name = pattern_def.get("name")
        regex = pattern_def.get("regex")
        if not regex:
            continue

        try:
            match = re.match(regex, filename)
            if match:
                groups = match.groupdict()
                return {
                    "pattern_name": name,
                    "date": groups.get("date"),
                    "sequence": groups.get("sequence"),
                }
        except Exception:
            pass

    return None


def parse_folder(folder_name: str) -> dict | None:
    """
    Parse folder name against known folder patterns.

    Returns dict with: pattern_name, date, location
    Or None if no pattern matches.
    """
    config = _get_patterns()
    folder_patterns = config.get("folder_patterns", [])

    for pattern_def in folder_patterns:
        name = pattern_def.get("name")
        regex = pattern_def.get("regex")
        if not regex:
            continue

        try:
            match = re.match(regex, folder_name)
            if match:
                groups = match.groupdict()
                return {
                    "pattern_name": name,
                    "date": groups.get("date"),
                    "location": groups.get("location"),
                }
        except Exception:
            pass

    return None
