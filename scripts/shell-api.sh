#!/usr/bin/env bash
# Open a Python REPL inside the running api container with app imported.
source "$(dirname "$0")/_lib.sh"

require docker

exec docker compose exec api uv run python -c "
from app.main import app          # noqa
from app.config import settings   # noqa
from app.db import AsyncSessionLocal  # noqa
import code
banner = 'InfluencerFlow REPL — app, settings, AsyncSessionLocal in scope'
code.interact(banner=banner, local=dict(globals(), **locals()))
"
