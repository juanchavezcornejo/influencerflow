"""Celery scaffold tests.

In test mode (``conftest.py``) Celery runs in eager mode, so ``.delay()``
executes synchronously and the broker is never touched.
"""

from __future__ import annotations

from app.workers.tasks_sync import ping


def test_ping_direct() -> None:
    assert ping() == "pong"


def test_ping_via_delay() -> None:
    result = ping.delay()
    assert result.get(timeout=5) == "pong"
    assert result.successful()
