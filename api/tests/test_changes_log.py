"""Tests for changes log rendering."""

from __future__ import annotations

from app.lib.changes_log import render_changes_log


def test_empty_corrections() -> None:
    """Test that empty corrections dict returns original text."""
    result = render_changes_log({})
    assert "Original" in result


def test_original_preset() -> None:
    """Test that original preset is recognized."""
    result = render_changes_log({"preset": "original"})
    assert "Original" in result
    assert "sin edición" in result


def test_golden_hour_renders_spanish() -> None:
    """Test that golden hour preset renders Spanish text."""
    corrections = {
        "preset": "golden_hour",
        "display_name": "Golden Hour Warm",
        "exposure": 0.15,
        "saturation": 1.08,
        "temp": 300,
    }
    result = render_changes_log(corrections)
    assert "Golden Hour" in result
    assert "Exposición" in result or "Exposición" in result
    assert "EV" in result


def test_editorial_neutral_renders() -> None:
    """Test that editorial neutral renders correctly."""
    corrections = {
        "preset": "editorial_neutral",
        "display_name": "Editorial Neutral",
        "contrast": 1.12,
        "exposure": 0.05,
        "highlights": -0.08,
    }
    result = render_changes_log(corrections)
    assert "Editorial Neutral" in result
    assert "Contraste" in result


def test_cinematic_moody_renders() -> None:
    """Test that cinematic moody renders correctly."""
    corrections = {
        "preset": "cinematic_moody",
        "display_name": "Cinematic Moody",
        "saturation": 0.92,
        "temp": -150,
    }
    result = render_changes_log(corrections)
    assert "Cinematic Moody" in result


def test_temperature_positive() -> None:
    """Test that positive temperature is rendered correctly."""
    result = render_changes_log({"temp": 300})
    assert "+300K" in result


def test_temperature_negative() -> None:
    """Test that negative temperature is rendered correctly."""
    result = render_changes_log({"temp": -150})
    assert "-150K" in result


def test_saturation_boost() -> None:
    """Test saturation boost percentage."""
    result = render_changes_log({"saturation": 1.15})
    assert "+15%" in result


def test_saturation_reduction() -> None:
    """Test saturation reduction percentage."""
    result = render_changes_log({"saturation": 0.85})
    assert "-15%" in result
