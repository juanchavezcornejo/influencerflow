---
description: Start the full dev stack (docker compose up)
---

Run `make dev` in the background so logs stream to the user while the
conversation continues. First, check if the stack is already up with
`make ps`; if it is, just report status and ask whether to restart.

If the stack is down:
1. Run `make dev` with `run_in_background: true`.
2. Wait a moment, then `make ps` to confirm services came up healthy.
3. Report the endpoints: web at `http://localhost:3000`, API health at
   `http://localhost:8000/api/v1/health`.

Do not poll the background log — the user can tail it with `make logs` if
they want.
