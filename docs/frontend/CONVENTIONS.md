# CONVENTIONS.md

Frontend coding conventions for InfluencerFlow. Read this before adding any
page, component, hook, or utility. Covers the _how to write it_ side of the
frontend. For the _what it looks like_ side, read `docs/frontend/DESIGN.md`.

---

## 1. Mental Model — Server Components vs Client Components

Next.js 15 App Router renders **React Server Components (RSC) by default**.
Server Components run on the server only: they can `async/await`, call
`apiFetch` directly, and read cookies/headers. They never use `useState`,
`useEffect`, or browser APIs.

**Client Components** are opted-in with `"use client"` at the top of the
file. They run in the browser (and during SSR hydration). Use them for
anything interactive: event handlers, local state, browser APIs, SSE hooks.

### Naming convention: `.client.tsx`

Any file that carries `"use client"` **must** end in `.client.tsx` (or
`.client.ts` for non-JSX). This makes the boundary visible in the filesystem
without opening the file.

```
app/(app)/dashboard/
  page.tsx                      ← Server Component (default)
  DashboardContent.client.tsx   ← Client Component (opt-in)
```

The server page fetches data and passes it as props to the client component.
The client component owns interactivity.

**Rule:** push `"use client"` as far down the tree as possible. A page that
is 90 % static should not be a client component just because one button needs
`onClick`.

---

## 2. File Naming

| File type | Convention | Example |
|---|---|---|
| Next.js page | `page.tsx` (required by framework) | `app/(app)/dashboard/page.tsx` |
| Next.js layout | `layout.tsx` (required by framework) | `app/layout.tsx` |
| Client Component | `PascalCase.client.tsx` | `DashboardContent.client.tsx` |
| Server Component (non-page) | `PascalCase.tsx` | `SessionCard.tsx` |
| Hook | `use-kebab-case.ts` | `use-session-events.ts` |
| Utility / lib | `kebab-case.ts` | `api-client.ts`, `format.ts` |
| Type module | `kebab-case.ts` | `api.ts`, `sse.ts` |

### Where each goes

```
src/
  app/                        ← routing only; pages + layouts
    (auth)/login/page.tsx
    (app)/
      dashboard/page.tsx
      dashboard/DashboardContent.client.tsx
      dashboard/new/page.tsx
      session/[id]/page.tsx
      session/[id]/cost/page.tsx
      edit/[assetId]/page.tsx
      settings/page.tsx
  components/
    shared/                   ← cross-feature reusables (AppShell, CostBadge, …)
    review/                   ← review-screen components (GroupBlock, AssetCard, …)
    edit/                     ← edit-view components (CompareSlider, CorrectionTabs, …)
    ui/                       ← shadcn-generated primitives (never hand-roll)
  hooks/                      ← all custom hooks, use-kebab-case.ts
  lib/                        ← api-client.ts, utils.ts, format.ts
  types/                      ← api.ts, sse.ts
```

Page-specific sub-components that will never be reused go in an
`_components/` directory next to the page:
```
app/(app)/session/[id]/_components/SyncProgressBar.client.tsx
```

---

## 3. Path Aliases

`@/` maps to `web/src/`. Configured in `tsconfig.json` and respected by
Next.js automatically.

```ts
import { apiFetch } from "@/lib/api-client";
import type { Session } from "@/types/api";
import { Button } from "@/components/ui/button";
import { useSessionEvents } from "@/hooks/use-session-events";
```

Never use relative imports that climb more than one level (`../../`). If you
find yourself doing that, the file is in the wrong place.

---

## 4. API Calls

All HTTP calls go through `apiFetch<T>()` from `@/lib/api-client`.

### How it works

- **Browser:** calls hit `/api/v1/*`, which Next.js rewrites to the FastAPI
  host (`API_BASE` env var, default `http://localhost:8000`).
- **Server (RSC):** calls go directly to `API_BASE + /api/v1`.
- `credentials: "include"` is always set — JWT cookies travel automatically.
- Plain-object `body` is serialized to JSON and `Content-Type: application/json`
  is set automatically. `FormData` and `Blob` are passed through as-is.

### GET (server component)

```ts
import { apiFetch } from "@/lib/api-client";
import type { Session } from "@/types/api";

// In an async Server Component or async function:
const sessions = await apiFetch<Session[]>("/sessions");
```

### GET with query params

```ts
import type { CostLogEntry } from "@/types/api";

const entries = await apiFetch<CostLogEntry[]>("/cost/log", {
  query: { sessionId: id, limit: 50 },
});
```

### POST with body

```ts
import { apiFetch } from "@/lib/api-client";
import type { Session } from "@/types/api";

const session = await apiFetch<Session>("/sessions", {
  method: "POST",
  body: {
    cloudProvider: "google_drive",
    cloudFolderId: folderId,
    cloudFolderName: folderName,
  },
});
```

### PATCH

```ts
import type { Asset } from "@/types/api";

await apiFetch<void>(`/assets/${assetId}/status`, {
  method: "PATCH",
  body: { status: "rejected" },
});
```

### Error handling — `ApiError`

`apiFetch` throws `ApiError` (exported from `@/lib/api-client`) for non-2xx
responses. Always import the type when catching:

```ts
import { apiFetch, ApiError } from "@/lib/api-client";

try {
  const result = await apiFetch<Session[]>("/sessions");
} catch (err) {
  if (err instanceof ApiError) {
    // err.status  → HTTP status code (number)
    // err.message → user-safe message from the API
    // err.body    → raw response body (unknown)
    console.error("API error", err.status, err.message);
  }
}
```

In UI components, redirect to `/login` on 401; show destructive toast on
5xx; show field-level error on 4xx with a message.

---

## 5. TypeScript Rules

- **No `any`.** Use `unknown` and narrow, or define a proper type.
- **Import types with `import type`** when the import is used only as a type:
  ```ts
  import type { Session, Asset } from "@/types/api";
  ```
- **No default exports** except Next.js pages and layouts (framework
  requirement). All components, hooks, and utilities use named exports:
  ```ts
  // correct
  export function DashboardContent(…) { … }
  // wrong (not a page file)
  export default function DashboardContent(…) { … }
  ```
- **Strict mode is on.** `tsconfig.json` has `"strict": true`. No
  `@ts-ignore` unless accompanied by a comment explaining why.
- All API shapes live in `web/src/types/api.ts`. Never redeclare `Session`,
  `Asset`, `Group`, etc. inline in a component.

---

## 6. shadcn/ui Usage

- Import **only** from `@/components/ui/`. Never hand-roll a button, dialog,
  badge, input, or table that shadcn already provides.
- Add new components with:
  ```bash
  pnpm dlx shadcn@latest add <component>
  ```
  This generates the source file in `src/components/ui/` and respects the
  project's Tailwind config.
- Do not edit the generated files in `components/ui/` unless fixing a genuine
  bug in the primitive. Customise by wrapping, not by patching.
- When a shadcn primitive is close-but-not-quite, compose it:
  ```tsx
  import { Button } from "@/components/ui/button";
  import { Loader2 } from "lucide-react";

  export function SpinnerButton({ loading, children, ...props }: ButtonProps & { loading?: boolean }) {
    return (
      <Button disabled={loading} {...props}>
        {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
        {children}
      </Button>
    );
  }
  ```

---

## 7. Styling

- **Tailwind only.** No inline `style={{}}`, no CSS modules, no styled-components.
- **HSL tokens from `globals.css`.** Use semantic utilities (`bg-background`,
  `text-foreground`, `border-border`, `text-muted-foreground`, `bg-card`, etc.).
  Never hand-write `hsl(...)` or hardcode hex colors in a component.
- **Dark mode is canonical.** The app is dark-first. Do not conditionally
  render light colors. The token system handles theming.
- Responsive modifiers go in order: base (mobile) → `sm:` → `md:` → `lg:` → `xl:` → `2xl:`.
- Max line length for className strings: break onto multiple lines with a
  template literal or `cn()` helper when exceeding 80 chars.

```tsx
// Good
<div className={cn(
  "flex items-center gap-2 rounded-lg border border-border p-4",
  isActive && "border-ring bg-accent/30",
)}>

// Bad — hardcoded color
<div style={{ backgroundColor: "#1a1a2e" }}>
```

---

## 8. Cookie Security

Any `Set-Cookie` issued by the backend (or Next.js middleware) must carry:

```
SameSite=Strict; Secure; HttpOnly
```

- `HttpOnly` — JS cannot read the JWT cookie.
- `Secure` — cookie only sent over HTTPS (Railway enforces TLS).
- `SameSite=Strict` — CSRF mitigation without a separate token.

Do not create cookies from client-side JS. Auth cookies are set server-side
by the FastAPI `/auth/login` response. If you need client-accessible storage,
use `localStorage` via `useLocalStorage` from `@/hooks/use-local-storage`.

---

## 9. Import Order

ESLint enforces five groups, separated by a blank line:

1. **Node built-ins** (`path`, `fs`, etc.)
2. **External packages** (`react`, `next/*`, `lucide-react`, etc.)
3. **Internal aliases** (`@/lib/*`, `@/components/*`, `@/hooks/*`, `@/types/*`)
4. **Relative imports** (`./something`, `../sibling`)
5. **Type-only imports** (`import type { … }` — always last within their group)

```ts
import { useCallback, useState } from "react";
import { useRouter } from "next/navigation";

import { apiFetch, ApiError } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { useSessionEvents } from "@/hooks/use-session-events";
import type { Session } from "@/types/api";
```

---

## 10. Adding a Page — Checklist

1. **Create the route file** at `app/(app)/<route>/page.tsx` as an async
   Server Component. Fetch data here; pass as props.
2. **Add a `.client.tsx` companion** if the page has interactive parts.
   Named export, `"use client"` at top.
3. **Wire up metadata** via `export const metadata = { title: "…" }` in the
   page file.
4. **Add the route to the sidebar** in `components/shared/Sidebar.tsx` if it
   should be top-level navigation.
5. **Update `docs/frontend/DESIGN.md` §6** with the new screen spec (route,
   purpose, layout, data, states, responsive notes).

---

## 11. Code Style

- **Line length: 100 characters.** Prettier is configured at `printWidth: 100`.
- **Strict TypeScript:** `strict: true` in `tsconfig.json`. No `as any`, no
  `@ts-ignore` without a justification comment.
- **Trailing commas** on multi-line structures (Prettier default).
- **Single quotes** for strings in TypeScript; JSX attribute strings use
  double quotes (Prettier handles this automatically).
- **User-facing strings** grouped at the top of each file in a `const COPY = {…}` object — see `DashboardContent.client.tsx` for the pattern. This enables future `next-intl` extraction without a rewrite.
- Run `make format` before committing. `make lint` must pass with zero errors.
