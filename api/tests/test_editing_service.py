"""Tests for editing_service.py"""

from app.services.editing_service import EditingService


def test_render_changes_log_exposure():
    """Test rendering changes log for exposure adjustment."""
    service = EditingService(None)
    corrections = {"exposure": 0.5}
    result = service.render_changes_log(corrections)
    assert "Exposición" in result
    assert "más brillante" in result


def test_render_changes_log_contrast():
    """Test rendering changes log for contrast adjustment."""
    service = EditingService(None)
    corrections = {"contrast": -0.2}
    result = service.render_changes_log(corrections)
    assert "Contraste" in result
    assert "reducido" in result


def test_render_changes_log_saturation():
    """Test rendering changes log for saturation adjustment."""
    service = EditingService(None)
    corrections = {"saturation": 0.15}
    result = service.render_changes_log(corrections)
    assert "Saturación" in result
    assert "aumentada" in result


def test_render_changes_log_white_balance():
    """Test rendering changes log for white balance adjustment."""
    service = EditingService(None)
    corrections = {"white_balance": {"temp": 20, "tint": 0}}
    result = service.render_changes_log(corrections)
    assert "Temperatura" in result
    assert "cálida" in result


def test_render_changes_log_empty():
    """Test rendering empty changes log."""
    service = EditingService(None)
    result = service.render_changes_log({})
    assert "Sin cambios" in result


def test_render_changes_log_multiple():
    """Test rendering multiple corrections."""
    service = EditingService(None)
    corrections = {
        "exposure": 0.1,
        "contrast": 0.2,
        "saturation": -0.05,
    }
    result = service.render_changes_log(corrections)
    assert "Exposición" in result
    assert "Contraste" in result
    assert "Saturación" in result
