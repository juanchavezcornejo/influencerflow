# Celery Workers

Task queue conventions for InfluencerFlow's background processing.

---

## Queues

The Celery app (`api/app/workers/celery_app.py`) uses a single default queue in the MVP.

| Queue name | Purpose |
|---|---|
| `default` | All tasks — sync, editing, export. Single queue in MVP; split by concern in V1 if throughput requires. |

`task_default_queue = "default"` is set in `celery_app.conf`. Worker startup:

```bash
celery -A app.workers.celery_app worker --loglevel=info --queues=default
```

---

## Task Naming Convention

Task names use `<module_basename>.<function_name>` (no `app.workers.` prefix):

```
tasks_sync.ping
tasks_sync.resync_session
tasks_editing.apply_corrections
tasks_export.build_zip
```

The `name=` parameter on `@celery_app.task` must always match this pattern exactly. Callers invoke tasks by this name:

```python
celery_app.send_task("tasks_sync.resync_session", args=[session_id])
```

---

## Task Function Shape

All tasks that do async work follow the same pattern: a synchronous outer function decorated with `@celery_app.task`, which calls `asyncio.run()` on an inner async function. The inner function opens its own DB session using `AsyncSessionLocal`.

```python
from __future__ import annotations

import asyncio
import logging

from app.db import AsyncSessionLocal
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="tasks_<module>.do_thing")
def do_thing(self, resource_id: str) -> dict:
    """Short docstring describing what the task does."""

    async def _run() -> None:
        async with AsyncSessionLocal() as db:
            try:
                # ... all async work using db ...
                await db.commit()
            except Exception as e:
                logger.error("do_thing.failed resource_id=%s error=%s", resource_id, e)
                # mark resource as errored
                await db.commit()

    asyncio.run(_run())
    return {"resource_id": resource_id, "status": "complete"}
```

Rules:
- `bind=True` gives access to `self` for retry control.
- Always use `async with AsyncSessionLocal() as db` — never reuse a session across tasks.
- The outer function returns a plain dict (Celery serializes this as the task result).
- Never raise from the outer function unless you intend a retry; catch and log instead.

---

## SSE Progress Events

Tasks report progress by writing structured log lines. The `events` router (`app/routers/events.py`) exposes a Server-Sent Events endpoint that the frontend polls. In the MVP, progress is communicated via log lines that the SSE router reads from Redis pub/sub.

Pattern used in `tasks_sync.resync_session`:

```python
logger.info(
    "sync.progress session_id=%s progress=%d current_file=%s",
    session_id, progress_pct, file_name,
)
```

Event naming convention: `<domain>.<event>` (e.g. `sync.progress`, `sync.complete`, `export.ready`).

To emit from within a task:
1. Log the structured line with `logger.info(...)`.
2. The SSE router subscribes to a Redis channel keyed by `session_id` and forwards matching log events to the browser.

No direct Redis publish calls are made from task code in the MVP — logging is the source of truth.

---

## Error Handling in Tasks

### Retry pattern

```python
@celery_app.task(bind=True, name="tasks_sync.resync_session", max_retries=3)
def resync_session(self, session_id: str) -> dict:
    async def _run() -> None:
        ...

    try:
        asyncio.run(_run())
    except Exception as exc:
        # Exponential backoff: 60s, 120s, 240s
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

    return {"session_id": session_id, "status": "complete"}
```

### Marking a resource as errored

Inside the inner async function, catch the exception and update the model status before re-raising or returning:

```python
except Exception as e:
    logger.error("sync.failed session_id=%s error=%s", session_id, e)
    repo = SessionRepository(db)
    await repo.update_status(session_id, "error")
    await db.commit()
    # Do not re-raise — task returns normally with error status captured in DB
```

---

## Task Catalog

| Task name | Queue | Inputs | What it does |
|---|---|---|---|
| `tasks_sync.ping` | default | — | Smoke test. Returns `"pong"`. |
| `tasks_sync.resync_session` | default | `session_id: str` | Full sync: wipe assets → list Drive folder → download → generate previews → extract EXIF → compute pHash → detect faces → deterministic grouping → mark session ready. |
| `tasks_editing.apply_corrections` | default | `edit_version_id: str` | Load full-res image, apply color corrections from `edit_versions.corrections_applied_json`, write JPEG to `/data/edits/{asset_id}/{edit_version_id}.jpg`, update `edit_versions.output_path`. |
| `tasks_export.build_zip` | default | `group_id: str` | Load group + assets + accepted edit versions, copy files to staging dir with `{NN}_{place_or_date}.{ext}` naming, ZIP into `/data/exports/{session_id}/{group_id}.zip`, clean staging dir, log `export.ready`. |

---

## Testing Tasks

Set `CELERY_TASK_ALWAYS_EAGER=True` to run tasks synchronously in the test process (no worker needed):

```python
# conftest.py or individual test
import pytest
from app.workers.celery_app import celery_app


@pytest.fixture(autouse=True)
def celery_eager(monkeypatch):
    celery_app.conf.update(task_always_eager=True, task_eager_propagates=True)
    yield
    celery_app.conf.update(task_always_eager=False)


def test_ping():
    from app.workers.tasks_sync import ping
    result = ping.delay()
    assert result.get() == "pong"
```

`task_eager_propagates=True` ensures exceptions inside eager tasks are re-raised in the test, making failures visible rather than silently swallowed.

For tasks that open their own `AsyncSessionLocal`, use a test DB override in `conftest.py` (see `docs/TESTING.md`).
