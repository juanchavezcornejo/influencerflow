# STATE.md

State management conventions for InfluencerFlow. Read this before adding a
hook, a data-fetching call, or any piece of shared state. Covers real hook
signatures and patterns drawn from the actual codebase.

For visual/UX decisions read `docs/frontend/DESIGN.md`.
For file layout and TypeScript rules read `docs/frontend/CONVENTIONS.md`.

---

## 1. No Global State Library

There is no Redux, Zustand, Jotai, or similar. State is kept local and
close to where it is used:

| Need | Tool |
|---|---|
| UI state scoped to a component | `useState` / `useReducer` |
| Server state visible to multiple components | URL params + `router.refresh()` |
| Long-running job progress | SSE via `useSessionEvents` |
| Persisted user preference | `useLocalStorage` |
| Async confirmation flow | `useConfirm` |
| Cost gate before a paid action | `useCostEstimate` + `<CostConfirm>` |

**URL params are state.** If two components on the page both care about
"which group is selected", the group ID belongs in the URL, not in a shared
React context. This makes the state bookmarkable and survives a hard reload.

**`router.refresh()`** re-runs all Server Components for the current route
without a full page reload. Use it after a mutation to re-fetch server data.
This is the primary "invalidate and refetch" mechanism — there is no SWR or
React Query.

---

## 2. SSE — `useSessionEvents`

**File:** `web/src/hooks/use-session-events.ts`

Subscribes to `EventSource` at `/api/v1/events/session/{sessionId}` and
returns the latest parsed event object, or `null` before the first event.

### Signature

```ts
interface SSEEvent {
  type: string;
  progress?: number;        // 0–100
  current_file?: string;    // filename being processed
  message?: string;
  [key: string]: unknown;   // event-specific extras
}

function useSessionEvents(sessionId: string): SSEEvent | null
```

### Usage pattern

```tsx
"use client";

import { useSessionEvents } from "@/hooks/use-session-events";

export function SyncProgress({ sessionId }: { sessionId: string }) {
  const lastEvent = useSessionEvents(sessionId);

  if (!lastEvent) return null;

  return (
    <div>
      <p className="text-xs text-muted-foreground font-mono truncate">
        {lastEvent.current_file ?? "Sincronizando…"}
      </p>
      <Progress value={lastEvent.progress ?? 0} className="h-1.5" />
      <span aria-live="polite" className="sr-only">
        {lastEvent.message ?? `${lastEvent.progress ?? 0}%`}
      </span>
    </div>
  );
}
```

### Reconnect behavior

The hook does **not** automatically reconnect on error. `EventSource.onerror`
logs the error and calls `eventSource.close()`. The cleanup function in the
`useEffect` return also closes the connection on unmount or when `sessionId`
changes. If a session ends (status `ready` or `error`), the backend closes
the stream and no reconnect is needed.

If you need reconnect logic (e.g., for a future long-lived export job), wrap
the effect with an exponential-backoff loop and track attempt count in a ref.

---

## 3. Optimistic Updates

Apply state changes immediately in the UI before the API call confirms them.
On failure, roll back to the previous state. Never leave the UI in an
indeterminate state after a failure.

The `useAssetReject` hook is the canonical pattern for optimistic mutations
in this codebase.

**File:** `web/src/hooks/use-asset-reject.ts`

```ts
// Actual hook signature:
function useAssetReject(options?: {
  onSettled?: (assetId: string, status: AssetStatus) => void;
}): {
  toggle: (assetId: string, currentStatus: AssetStatus) => Promise<void>;
  isPending: (id: string) => boolean;
}
```

### Complete pattern with rollback

```tsx
"use client";

import { useState } from "react";
import { useAssetReject } from "@/hooks/use-asset-reject";
import { useToast } from "@/hooks/use-toast";
import type { Asset } from "@/types/api";

export function AssetCard({ asset: initialAsset }: { asset: Asset }) {
  const [asset, setAsset] = useState(initialAsset);
  const { addToast } = useToast();

  const { toggle, isPending } = useAssetReject({
    onSettled: (assetId, newStatus) => {
      // Called optimistically (before API) AND on rollback (after failure).
      setAsset((prev) => ({ ...prev, status: newStatus }));

      if (newStatus === "rejected") {
        addToast("Rechazada. Deshacer", "info");
      }
    },
  });

  const isRejected = asset.status === "rejected";

  return (
    <div className={isRejected ? "opacity-40 grayscale" : ""}>
      <button
        disabled={isPending(asset.id)}
        onClick={() => toggle(asset.id, asset.status)}
        aria-label="Rechazar foto"
      >
        ×
      </button>
    </div>
  );
}
```

The hook calls `onSettled` **optimistically** (immediately, before the API
call) with the next status, then calls it again with the **original** status
if the API call throws, effectively rolling back.

---

## 4. Confirm Dialog — `useConfirm`

**File:** `web/src/hooks/use-confirm.ts`

Provides an imperative `confirm()` function that returns a `Promise<boolean>`.
Await it; `true` means the user clicked Confirm, `false` means Cancel or Esc.

### Signature

```ts
interface ConfirmOptions {
  title: string;
  body?: string;
  confirmLabel?: string;    // default: "Confirmar"
  cancelLabel?: string;     // default: "Cancelar"
  variant?: "default" | "destructive";
}

interface UseConfirmReturn {
  confirmState: ConfirmState | null;  // wire into <ConfirmDestructive>
  confirm: (options: ConfirmOptions) => Promise<boolean>;
  handleConfirm: () => void;          // call from dialog's confirm button
  handleCancel: () => void;           // call from dialog's cancel button / Esc
}
```

### Usage

```tsx
"use client";

import { useConfirm } from "@/hooks/use-confirm";
import { ConfirmDestructive } from "@/components/shared/ConfirmDestructive";

export function ResyncButton({ sessionId }: { sessionId: string }) {
  const { confirm, confirmState, handleConfirm, handleCancel } = useConfirm();

  async function handleResync() {
    const ok = await confirm({
      title: "¿Re-sincronizar sesión?",
      body: "Se borrarán todos los grupos y ediciones actuales.",
      confirmLabel: "Re-sincronizar",
      variant: "destructive",
    });

    if (!ok) return;

    await apiFetch(`/sessions/${sessionId}/resync`, { method: "POST" });
  }

  return (
    <>
      <Button variant="destructive" onClick={handleResync}>
        Re-sincronizar
      </Button>

      {/* Render the dialog driven by confirmState */}
      <ConfirmDestructive
        state={confirmState}
        onConfirm={handleConfirm}
        onCancel={handleCancel}
      />
    </>
  );
}
```

The hook is entirely controlled — `confirmState` is `null` when no dialog is
open and populated with the options + a resolve function when `confirm()` has
been called and is awaiting the user's choice.

---

## 5. Cost Estimate — `useCostEstimate`

**File:** `web/src/hooks/use-cost-estimate.ts`

Fetches a cost estimate from `POST /api/v1/cost/estimate` before showing
`<CostConfirm>`. Call `fetch()` on hover or on trigger-button click — not
on mount.

### Signature

```ts
interface UseCostEstimateReturn {
  estimate: CostEstimate | null;
  loading: boolean;
  error: Error | null;
  fetch: (operation: string, inputs: Record<string, unknown>) => Promise<CostEstimate | null>;
  reset: () => void;
}
```

`CostEstimate` shape (from `@/types/api`):
```ts
interface CostEstimate {
  operation: string;
  estimatedDollars: number;
  estimatedTokens: number | null;
  sessionTotalDollars: number;
  budgetDollars: number;
  remainingDollars: number;
  hardCapDollars: number;
  exceedsSoftCap: boolean;
  exceedsHardCap: boolean;
}
```

### Usage

```tsx
"use client";

import { useCostEstimate } from "@/hooks/use-cost-estimate";
import { CostBadge } from "@/components/shared/CostBadge";
import { CostConfirm } from "@/components/shared/CostConfirm";

export function AiGroupButton({ sessionId }: { sessionId: string }) {
  const { estimate, loading, fetch, reset } = useCostEstimate();
  const [open, setOpen] = useState(false);

  async function handleClick() {
    const result = await fetch("ai_grouping", { sessionId });
    if (result) setOpen(true);
  }

  return (
    <>
      <Button onClick={handleClick} disabled={loading}>
        {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
        Agrupar con IA
        <CostBadge kind="ai" estimate={estimate ? `$${estimate.estimatedDollars.toFixed(2)}` : undefined} />
      </Button>

      <CostConfirm
        open={open}
        estimate={estimate}
        onConfirm={async () => {
          setOpen(false);
          await apiFetch(`/sessions/${sessionId}/group`, { method: "POST" });
        }}
        onCancel={() => { setOpen(false); reset(); }}
      />
    </>
  );
}
```

---

## 6. Toast — `useToast`

**File:** `web/src/hooks/use-toast.ts`

Lightweight in-app toast. Returns `addToast` and `removeToast`. The
`<Toaster>` component (rendered once in `<AppShell>`) reads the `toasts`
array and renders them.

### Signature

```ts
type ToastType = "success" | "error" | "info";

interface Toast {
  id: string;
  message: string;
  type: ToastType;
}

function useToast(): {
  toasts: Toast[];
  addToast: (message: string, type?: ToastType, duration?: number) => string;
  removeToast: (id: string) => void;
}
```

### Usage

```tsx
"use client";

import { useToast } from "@/hooks/use-toast";

export function SaveButton() {
  const { addToast } = useToast();

  async function handleSave() {
    try {
      await apiFetch("/settings/style-seed", { method: "PUT", body: { text } });
      addToast("Guardado correctamente", "success");
    } catch (err) {
      addToast("Error al guardar. Inténtalo de nuevo.", "error", 8000);
    }
  }
}
```

Duration defaults: `3000ms` for success/info, pass `8000` explicitly for
errors and warnings to give the user time to read.

---

## 7. Local Storage — `useLocalStorage`

**File:** `web/src/hooks/use-local-storage.ts`

SSR-safe, typed `localStorage` wrapper. Falls back to `initialValue` on the
server. Uses `JSON.parse` / `JSON.stringify` internally.

### Signature

```ts
function useLocalStorage<T>(
  key: string,
  initialValue: T,
): readonly [T, (next: T | ((prev: T) => T)) => void]
```

### Usage

```tsx
"use client";

import { useLocalStorage } from "@/hooks/use-local-storage";

export function Sidebar() {
  const [collapsed, setCollapsed] = useLocalStorage("sidebar-collapsed", false);

  return (
    <aside className={collapsed ? "w-14" : "w-64"}>
      <button onClick={() => setCollapsed((prev) => !prev)}>
        {collapsed ? "Expand" : "Collapse"}
      </button>
      {/* … */}
    </aside>
  );
}
```

The updater supports both a direct value and a function (same API as
`useState`). Quota errors on write are caught silently; the in-memory value
still updates.

---

## 8. Router Refresh After Mutations

After a mutation (create, update, delete) that changes server data visible
on the current page, trigger a re-render of Server Components with:

```ts
import { useRouter } from "next/navigation";

const router = useRouter();

// After a successful mutation:
router.refresh();
```

`router.refresh()` is the right choice when:
- The current page has Server Components that fetched the mutated data.
- You want to re-run server-side fetches without navigating away.
- The mutation affects a list (new session created, group renamed, etc.).

**Do not use `window.location.reload()`** — it triggers a full browser
reload, loses in-memory state, and is slower than `router.refresh()`.

The only exception: if you need to clear all client state (e.g., after a
Resync that wipes everything), navigate with `router.push("/session/{id}")`
instead, which remounts the whole route tree.
