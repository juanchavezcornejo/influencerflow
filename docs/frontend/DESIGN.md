# DESIGN.md

Frontend UI/UX specification for InfluencerFlow. Read this **and**
`docs/frontend/CONVENTIONS.md` before adding/changing any page, component, or hook.

`CONVENTIONS.md` is about **how to write it** (structure, naming, API calls).
`DESIGN.md` is about **what it should look like and how it should feel**.

If a decision isn't covered here, prefer the smallest, calmest option that
matches the rest of the app — then note the new decision back in this file.

---

## 0. Context in one paragraph

Single-user tool for turning 100–1000 travel photos into Instagram-ready
posts. Juan opens it on desktop (primary) and occasionally on a tablet /
phone. The app handles large media grids, an edit slider, and several
paid-API operations. The UX must make three things impossible to
miss: **what will cost money**, **what is a preview vs. the final full-res**,
and **what the app is doing right now** (sync, generate, export).

---

## 1. Design Principles

1. **Calm surface, dense content.** Photos are the product. Chrome stays
   out of the way — no gradients, no decorative icons, no drop shadows on
   everything. Borders and subtle surface steps do the structural work.
2. **Always show state.** Every async action has `loading → success | error`.
   No spinning dots in a vacuum: show *what* is loading and, when we know,
   *how much is left*.
3. **Paid ops are explicit.** Nothing that spends money runs without a
   **cost badge** on the trigger **and** a confirmation modal. Budget cap
   is enforced server-side; UI mirrors it.
4. **Reversible by default.** Anything destructive (Resync, delete session,
   reject edit with regenerate) prompts or supports undo via toast.
5. **Keyboard-first where it matters.** Edit view and review grid are
   designed to be driven with `←/→`, `1–4`, `Enter`, `X`, `Esc`.
6. **Dark is the canonical theme.** Light is not planned for MVP — but the
   HSL token system is already light-mode capable; don't hardcode colors.
7. **Aspect ratios are sacred.** Thumbnails, previews, and before/after
   sliders never distort. Use `object-cover` on fixed tiles, `object-contain`
   in the edit view.
8. **No custom form controls** unless shadcn doesn't have it. Stay on the
   shadcn contract so upgrades are cheap.

---

## 2. Visual System

### 2.1 Tokens (HSL, via `globals.css` + Tailwind)

Defined in `web/src/app/globals.css`. Use **only** via Tailwind utilities
(`bg-background`, `text-foreground`, `border-border`, …). Never hand-write
`hsl(...)` in components.

| Token | Dark value | Usage |
|---|---|---|
| `--background` | `240 10% 3.9%` | App canvas |
| `--foreground` | `0 0% 98%` | Primary text |
| `--card` | `240 10% 3.9%` | Card surface (same as bg — use `border` to separate) |
| `--popover` | `240 10% 3.9%` | Menus, combobox |
| `--primary` / `-foreground` | `0 0% 98%` / `240 5.9% 10%` | Primary button |
| `--secondary` / `-foreground` | `240 3.7% 15.9%` / `0 0% 98%` | Secondary button |
| `--muted` / `-foreground` | `240 3.7% 15.9%` / `240 5% 64.9%` | Labels, hints, metadata |
| `--accent` / `-foreground` | same as muted | Hover / focused surface |
| `--destructive` / `-foreground` | `0 62.8% 30.6%` / `0 0% 98%` | Reject / delete |
| `--border` / `--input` | `240 3.7% 15.9%` | All borders, dividers, input outlines |
| `--ring` | `240 4.9% 83.9%` | Focus ring |
| `--radius` | `0.5rem` | Base radius (shadcn `sm/md/lg` derive from this) |

**Semantic badges** — extra colors, all composed with existing tokens:

- 🆓 **Free**: `bg-secondary text-secondary-foreground`
- 💰 **Paid (USD)**: amber — use `bg-amber-500/15 text-amber-300 border border-amber-500/30`
- 🤖 **AI tokens**: violet — `bg-violet-500/15 text-violet-300 border border-violet-500/30`
- ✅ **Success**: emerald — `bg-emerald-500/15 text-emerald-300 border border-emerald-500/30`
- ⚠️ **Warning**: amber (same as paid — distinguish by label)
- ❌ **Error/reject**: `bg-destructive text-destructive-foreground`

Keep the amber/violet/emerald uses **list-exhaustive** above — don't introduce new color ramps ad-hoc.

### 2.2 Typography

- Font: system default (no custom webfont in MVP). If we add one later, it
  goes through `next/font/google` in `app/layout.tsx` only.
- Scale (Tailwind classes):
  - `text-xs` (12px): meta / timestamps / cost counts
  - `text-sm` (14px): body, buttons, labels (default)
  - `text-base` (16px): form inputs, description textarea
  - `text-lg` (18px): group titles inline in review
  - `text-xl` (20px): page headings in-app
  - `text-2xl` (24px): login / dashboard hero
  - `text-3xl` (30px): marketing-ish copy on empty states
- Weights: `font-normal` body, `font-medium` labels/buttons, `font-semibold` headings. No `font-bold` unless it's a numeric callout (cost totals).
- Line height: Tailwind defaults. Use `leading-tight` on large numbers.
- Max measure: `max-w-prose` (~65ch) for any paragraph text longer than two lines (descriptions, empty-state body copy).

### 2.3 Spacing & layout

- **4-px base grid** (Tailwind default). Use `space-y-4` (16px) as the default vertical rhythm inside a card; `space-y-2` for tight label/input pairs; `space-y-6` between sections.
- **Container**: `container mx-auto px-4 md:px-6` — relies on `tailwind.config.ts` `container.screens["2xl"]: 1400px`.
- **Page max-width by screen type**:
  - Auth / settings forms: `max-w-md` centered.
  - Dashboard, session, group detail: full container.
  - Edit view: full viewport (`min-h-screen`, no container padding).

### 2.4 Radii & borders

- Cards / modals / inputs: `rounded-lg` (shadcn default `md`).
- Thumbnails: `rounded-md`.
- Pills/badges: `rounded-full`.
- Borders: always via `border border-border` (1px). Never >1px except for the focus ring on active drag targets.

### 2.5 Elevation

Dark UI: avoid drop shadows. Use **surface steps** instead:
- Level 0 = `bg-background` (page)
- Level 1 = `bg-card border border-border` (card)
- Level 2 = `bg-popover border border-border shadow-lg` (popover/modal)

Only Level 2 gets a shadow, and only because modals overlap content.

### 2.6 Iconography

- Library: `lucide-react` (installed with shadcn).
- Size: `h-4 w-4` inside buttons/badges, `h-5 w-5` standalone, `h-6 w-6` in empty-state illustrations.
- Strokes: default. Don't override `strokeWidth` unless aligning with a specific shadcn component.

### 2.7 Motion

- Duration: `duration-150` for hovers, `duration-200` for panel transitions, `duration-300` for slider/compare drag release.
- Easing: Tailwind defaults (`ease-out` for enter, `ease-in` for exit).
- Respect `prefers-reduced-motion` — wrap any non-essential transition in a `motion-safe:` variant.
- No parallax, no auto-playing video. Hover-to-preview on thumbnails is **off** (too costly to decode on a 200-asset grid).

---

## 3. Responsive Strategy

### 3.1 Breakpoints (Tailwind defaults)

| Name | Min width | Primary target |
|---|---|---|
| `sm` | 640px | Large phones landscape |
| `md` | 768px | Tablet portrait |
| `lg` | 1024px | Tablet landscape / small laptop |
| `xl` | 1280px | Desktop (design baseline) |
| `2xl` | 1536px | Wide desktop |

**Design baseline is `xl`.** Everything is drawn at 1280–1440 first; then we scale *down* with `md:` / `sm:` overrides — never scale up.

### 3.2 Grid densities

Responsive grids are the #1 thing we touch. Use these three templates:

| Grid | Class | Where |
|---|---|---|
| **Dense** | `grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 2xl:grid-cols-8 gap-2` | Review grid (thumbnails) |
| **Comfortable** | `grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4` | Session cards on dashboard |
| **Form** | `grid-cols-1 md:grid-cols-2 gap-4` | Settings, two-column forms |

### 3.3 Navigation patterns

- **≥ `md`**: left sidebar (collapsible) + top bar (session title + cost badge + user menu).
- **< `md`**: top bar only; sidebar becomes a sheet (shadcn `<Sheet>`) triggered by a hamburger.
- Edit view is full-screen on every breakpoint (no sidebar).

### 3.4 Touch targets

Minimum 44×44 px for any interactive element (WCAG). Icon-only buttons use `h-10 w-10` or `h-11 w-11`. The before/after slider handle is `h-12 w-12` with an 8-px hit-slop outside its visible bounds.

---

## 4. Accessibility (non-negotiable)

- All interactive elements must be reachable by keyboard. Use shadcn primitives — they handle this — or native `<button>` / `<a>`.
- Focus styles: use shadcn's default `focus-visible:ring-2 ring-ring ring-offset-2 ring-offset-background`. Never remove the ring.
- Color contrast: ≥ 4.5:1 for text, ≥ 3:1 for UI borders. The token system meets this; don't tint below it.
- Images: every `<img>` / `<Image>` has a meaningful `alt`. Thumbnails use `alt="{filename} — {date}"`.
- Live regions: SSE progress updates go into a polite `aria-live="polite"` region so screen readers get sync/export progress.
- Modals trap focus (shadcn `<Dialog>` handles it). `Esc` always closes.
- Form inputs always have a visible `<Label>`.

---

## 5. Layout Primitives (app chrome)

Define these once, reuse everywhere. Live in `src/components/shared/`.

### 5.1 `<AppShell>`
Wraps all authenticated pages. Responsibilities:
- Renders `<Sidebar>` (≥ `md`) or `<MobileNav>` (< `md`).
- Renders `<TopBar>`.
- Receives `children` as the main column.
- Owns the `<Toaster>` portal and the global `<CostConfirm>` dialog provider.

### 5.2 `<Sidebar>`
- Width `w-64` collapsed to `w-14` with a toggle persisted in localStorage.
- Items: Dashboard, Current Session (disabled if none), Cost Log, Settings.
- At the bottom: small footer with app version + "Connected: Drive ✓/✗".

### 5.3 `<TopBar>`
- Height `h-14`.
- Left: page title (server-provided via `<PageTitle>` context) + breadcrumb crumbs where applicable.
- Right: **running session cost** (clickable → cost page), **connect-drive indicator**, user menu (logout, settings).

### 5.4 `<PageHeader>`
- `h-20` band inside the main column.
- Slots: `title`, `subtitle`, `actions` (right-aligned). Most pages pass a primary action here.

### 5.5 `<EmptyState>`
- Centered icon (lucide, `h-6 w-6 text-muted-foreground`) + title (`text-lg font-medium`) + body (`text-sm text-muted-foreground max-w-prose`) + optional CTA.

### 5.6 `<ErrorState>`
Same shape as EmptyState but:
- Icon: `AlertCircle`, `text-destructive`.
- Body shows the user-safe error message (from `ApiError.message`).
- CTA is always "Retry" unless the action is non-retryable.

### 5.7 `<CostBadge>`
Shows cost classification on any trigger that invokes a paid op.
- Props: `{ kind: "free" | "paid" | "ai"; estimate?: string }`.
- Visual: one of the semantic chips in §2.1. Size: `text-xs px-2 py-0.5 rounded-full`.
- The estimate (`$0.12`) is shown only when `kind !== "free"`.

### 5.8 `<CostConfirm>` (modal — spec from W4-008)
Reusable. Signature:
```ts
type CostConfirmProps = {
  operation: CostOperation;
  inputs: Record<string, unknown>;
  onConfirm: () => Promise<void>;
  onCancel?: () => void;
};
```
Fetches `/cost/estimate`, shows: operation name, estimated $, session total so far, budget remaining, soft-cap warning if exceeded. Buttons: **Cancel**, **Continue**. Confirming locks the button + shows a small inline spinner until `onConfirm` resolves.

### 5.9 `<Toast>`
shadcn `<Toaster>` (sonner). Four variants: info, success, warning, destructive. Duration 4s for info/success, 8s for warning/destructive. Always include an action slot for retryable errors.

---

## 6. Screen Catalog

Each screen below documents: **route**, **purpose**, **layout**, **data required** (TypeScript-ish shapes), **states**, **responsive notes**, **interactions / shortcuts**.

> Data shapes reference types that live in `web/src/types/` once authored. Treat them as the API contract; keep them in sync with FastAPI response schemas (see `docs/BACKEND.md`).

---

### 6.1 `/login` — Sign in *(W1-002)*

**Purpose:** Single-user credentials login.

**Layout:**
- No `<AppShell>`. Centered card on plain background.
- Card `max-w-md`, `space-y-6` inside.
- Logo/title on top (`InfluencerFlow`, `text-2xl font-semibold`).
- `<form>`: email, password, **Sign in** button (primary, full width).
- Below button: rate-limit hint line (muted).

**Data required:** none on render. On submit:
```ts
// POST /api/v1/auth/login
{ email: string; password: string } → { accessToken: string } // stored as HttpOnly cookie
```

**States:**
- idle → submitting (button disabled + spinner) → success (redirect `/dashboard`) → error (inline error above button, message from `ApiError`).
- Rate-limited: destructive toast "Too many attempts, try again in N minutes".

**Responsive:** card is `max-w-md` everywhere; padding `px-4` on < `sm`.

**Interactions:** `Enter` submits. Password field has show/hide toggle.

---

### 6.2 `/dashboard` — Sessions list *(W1-005, W1-006)*

**Purpose:** Land here after login. Shows past sessions + CTA to start a new one + Google Drive connection status.

**Layout:**
- `<AppShell>` + `<PageHeader title="Sessions" actions={<NewSessionButton/>}/>`.
- Below header: Drive connection card (shows status, "Connect" or "Disconnect" button).
- Grid of session cards (template **Comfortable** from §3.2).

**Data required:**
```ts
type Session = {
  id: string;
  cloudFolderName: string;
  assetCount: number;
  groupCount: number;
  status: "pending" | "syncing" | "ready" | "error" | "deleted";
  costToDateUsd: number;
  createdAt: string; // ISO
  thumbnailAssetIds: string[]; // up to 4 for card preview
};
type DriveStatus = { connected: boolean; email?: string };
// GET /api/v1/sessions → Session[]
// GET /api/v1/storage/google-drive → DriveStatus
```

**Session card layout:**
- 4-tile thumbnail grid (2×2) at the top, aspect `aspect-[4/3]`.
- Body: cloud folder name (`text-base font-medium truncate`), meta row (`assetCount assets · groupCount groups`), status pill, cost pill.
- Hover: elevated border (`hover:border-ring`). Click → `/session/{id}`.
- Three-dot menu: Rename, Delete (destructive confirm).

**States:**
- Drive disconnected: connection card is primary CTA; "New session" button disabled with tooltip.
- No sessions: `<EmptyState icon=Folder title="No sessions yet" body="Connect Google Drive and sync a folder to get started." cta={<NewSessionButton/>}/>`.
- Loading: 6 skeleton cards.
- Error: `<ErrorState>` in the grid area.

**Responsive:** 1 col < `sm`, 2 cols `lg`, 3 cols `xl`. Drive card is always full-width.

---

### 6.3 `/dashboard/new` — Folder picker *(W1-007)*

**Purpose:** Paste a Drive folder URL / ID, validate it, create a session.

**Layout:**
- `<AppShell>` + `<PageHeader title="New session" />`.
- Max-width `max-w-2xl` centered.
- Step 1: input field + "Validate" button. Accepts URL or raw ID.
- Step 2 (after validation): preview card showing folder name, file count, sample thumbnails (from Drive), estimated disk usage.
- Step 3: "Create session" primary button → redirects to `/session/{id}` and kicks off resync.

**Data required:**
```ts
// GET /api/v1/storage/google/folders/{id} → { id, name, fileCount, sampleThumbnails: string[], approxBytes: number }
// POST /api/v1/sessions { cloudProvider: "google_drive", cloudFolderId, cloudFolderName } → Session
```

**States:**
- idle → validating (button spinner) → valid (step 2 appears) → invalid (inline error, step 2 hidden).
- Creating session → disable everything → redirect on success; destructive toast on failure.

**Responsive:** single column, `max-w-2xl`; on `< sm`, thumbnails collapse from 4 to 2.

---

### 6.4 `/session/{id}` — Review *(W1-016 + W2-007)*

**Purpose:** The core screen. Shows all assets grouped into potential posts, lets Juan review/reorganize.

**Layout:**
- `<AppShell>` + compact session header:
  - Left: editable session title (inline edit, `text-xl`).
  - Right: **Resync** (destructive confirm), **Re-group** (free), session status pill, cost pill.
  - Progress bar underneath when `status = syncing`.
- Group list:
  - Each group is a `<GroupBlock>`: title (editable inline), asset count, "Generate caption" button, "Download ZIP" button, three-dot menu (rename, delete, merge).
  - Assets inside the group render in the **Dense** grid (§3.2).
  - Near-duplicate clusters collapse into a stack with a `+N` chip; click expands inline.
- **Ungrouped drawer** at the bottom (sticky). Collapsible; shows count; expands into a horizontal scroll strip of cards.

**Data required:**
```ts
type Asset = {
  id: string;
  thumbnailUrl: string;      // /api/v1/assets/{id}/thumbnail
  previewUrl: string;        // /api/v1/assets/{id}/preview
  filename: string;
  takenAt: string | null;
  isVideo: boolean;
  hasFace: boolean;
  aestheticScore: number | null;
  phash: string | null;
  nearDuplicateClusterId: string | null;
  status: "active" | "rejected";
  currentEditVersionId: string | null;
};
type Group = {
  id: string;
  name: string;
  autoGenerated: boolean;
  orderIndex: number;
  assets: Asset[]; // ordered by position
};
type SessionDetail = Session & {
  groups: Group[];
  ungroupedAssetIds: string[];
};
// GET /api/v1/sessions/{id}/groups → Group[]
// SSE /api/v1/events/session/{id} → SyncEvent (see hooks/use-session-events.ts)
```

**Asset card** (reused in Ungrouped too):
- `aspect-[4/5]` wrapper for IG-ish feel; thumbnail `object-cover`.
- Overlays:
  - Top-left: face icon if `hasFace`, video icon if `isVideo`.
  - Top-right: aesthetic score chip (only if present).
  - Bottom gradient on hover: filename + date.
  - Top-right on hover: **quick-reject** (×) button. Rejected cards dim to `opacity-40` + `grayscale`.
- Ring style: `hover:ring-2 ring-ring ring-offset-2 ring-offset-background`.
- Drag handle: entire card is draggable (dnd-kit).

**States:**
- `status = pending | syncing`: progress bar + live filename ("Downloading IMG_1234.HEIC (48/200)"). Thumbnails stream in as they finish.
- `status = ready` + 0 groups: `<EmptyState>` with "Re-group" CTA.
- `status = error`: destructive banner at top with retry CTA.
- Near-dup cluster: top card has the representative image; `+N` chip bottom-right; click expands row.

**Responsive:**
- Dense grid drops to 2 cols on mobile; group header stacks (title on line 1, actions on line 2).
- Ungrouped drawer becomes fixed sheet on < `md`.
- Drag-and-drop disabled on touch below `md`; long-press menu instead (move to group via dropdown).

**Interactions / shortcuts:**
- `X` → quick-reject focused asset.
- `Arrow` keys within grid → move focus (roving tabindex).
- `Enter` → open `/edit/{assetId}`.
- Click group title → inline edit; `Enter` commits, `Esc` cancels.

---

### 6.5 `/edit/{assetId}` — Edit view *(W3-008, W3-009, W4-006, W4-013)*

**Purpose:** Before/after slider with correction panels.

**Layout (full-screen, no AppShell):**
- Top rail (`h-12`): back button (← to session), asset filename + group name, cost pill, close (Esc).
- Main canvas: before/after slider occupying most of the viewport. Aspect preserved; `object-contain` + black letterbox background.
- Right panel (`w-96` on ≥ `lg`, hidden on < `lg` — replaced by bottom sheet): correction tabs + controls.
- Bottom bar (`h-16`): **Accept** (primary), **Reject → Regenerate** (secondary, shows cost badge), **Reject → Manual** (ghost).
- Proposal cycler: arrows on the right edge of canvas (`< >`) + tab pills labeled "1/3, 2/3, 3/3" below slider.

**Correction tabs (4):** 🎨 Color · 🧭 Crop · 🧽 Remove · 👤 Face

Each tab contains:
- Mode selector (segmented control): **🧑 Manual · 🆓 Local · 🤖 AI**.
- Mode-specific controls (see §6.5.1–4).
- Changes log (plain text bullets, see below).

**Data required:**
```ts
type EditVersion = {
  id: string;
  assetId: string;
  parentVersionId: string | null;
  createdAt: string;
  correctionsAppliedJson: Record<string, unknown>;
  changesLogText: string;      // Spanish bullet list
  outputPath: string | null;    // populated once full-res is rendered
  previewUrl: string;           // low-res preview of this version
  userDecision: "pending" | "accepted" | "rejected" | "manual";
};
type EditCandidatesResponse = { proposals: EditVersion[]; current: EditVersion };
// POST /api/v1/assets/{id}/edits/suggest { corrections, mode } → EditCandidatesResponse
// POST /api/v1/edits/{id}/accept { selectedCorrections } → EditVersion (now accepted)
// POST /api/v1/edits/{id}/reject { regenerate: boolean } → EditVersion | EditCandidatesResponse
// SSE edit.completed → refresh outputPath
```

#### 6.5.1 Color tab
- Local mode: 3 preset cards (Golden Hour, Editorial Neutral, Cinematic Moody) — click cycles proposals; each card shows mini before/after.
- AI mode: "Propose" button with `<CostBadge kind=ai estimate=...>`; opens `<CostConfirm>`.
- Manual mode: "Upload corrected" file input → produces a new `EditVersion`.

#### 6.5.2 Crop tab
- Local mode: one suggested crop (SmartCrop). Slider shows cropped result vs. original.
- AI mode: "Propose crop" → Claude Vision → cost confirm → returns one recommended crop.
- Manual mode: interactive crop box (free-transform, 1:1 / 4:5 / 3:4 / 16:9 presets).

#### 6.5.3 Remove (objects) tab *(W4-006)*
- AI mode: candidate boxes overlaid on preview with checkboxes (default checked per `recommend_remove`).
- "Run removal" → `<CostConfirm>` (LaMa cost) → runs, SSE refreshes preview.
- Manual mode: brush tool placeholder — "coming later" (V1).

#### 6.5.4 Face tab *(W4-013)*
Three-state flow per detected face:
1. **Detected** → "Download crop" button + face bbox overlay.
2. **Uploaded** → "Blend" button enabled; shows uploaded crop thumbnail.
3. **Blended** → preview updated; "Re-upload" to redo.

Data:
```ts
type FaceCrop = {
  id: string;
  assetId: string;
  bboxJson: { x: number; y: number; w: number; h: number };
  cropUrl: string;                 // original crop download
  uploadedCropUrl: string | null;
  blendedOutputUrl: string | null;
  status: "cropped" | "uploaded" | "blended";
};
// POST /api/v1/assets/{id}/face-crops → FaceCrop[]
// POST /api/v1/face-crops/{id}/upload-corrected (multipart)
// tasks_editing.blend_face emits SSE `face.blended`
```

**Slider component:** `react-compare-slider`. Vertical divider; touch + mouse. Position persists while cycling proposals (so Juan can A/B compare the same split).

**Changes log card** (right panel, always visible once an accepted version exists):
```
- Color: LUT "Golden Hour v2" (temp +400K, saturación -8)
- Crop: 4:5, sujeto en intersección superior-derecha
- Borrado: persona esquina inferior-izquierda (LaMa)
- Cara: manual (FaceApp) + Poisson seamless clone
```
Rendered from `edit_versions.changes_log_text`. Always Spanish per `PROMPTS.md`.

**Responsive:**
- `≥ xl`: right panel is docked at `w-96`.
- `md` / `lg`: right panel collapses into a bottom sheet (`<Sheet side="bottom">`).
- `< md`: edit view shows a reduced control strip (mode selector + Accept/Reject only); advanced controls require tapping a "More" button → full-screen sheet.

**Shortcuts:** `←/→` cycle proposals · `Enter` accept · `Esc` back · `1/2/3/4` switch correction tabs · `R` reject+regenerate · `M` reject+manual.

---

### 6.6 `/session/{id}/cost` — Cost log *(W5-010)*

**Purpose:** Full breakdown of every cent spent in a session.

**Layout:**
- `<AppShell>` + `<PageHeader title="Session cost" subtitle={sessionTitle} />`.
- Summary row: three stat tiles — **Total**, **Budget** (from `SESSION_BUDGET_USD`), **Remaining**. Progress bar tinted by ratio (emerald < 70%, amber 70–100%, destructive > 100%).
- Table (shadcn `<Table>`): Operation · Count · Model · Tokens · Dollars. Sortable by dollars desc default.
- Below: stacked bar chart by operation (optional if time; swap for a grouped list if chart lib is overkill).

**Data required:**
```ts
type CostSummary = {
  totalDollars: number;
  budgetDollars: number;
  hardCapDollars: number;
  byOperation: Array<{ operation: string; count: number; model: string | null; tokens: number; dollars: number }>;
};
// GET /api/v1/sessions/{id}/cost → CostSummary
```

**States:** loading (skeleton rows), empty (`"No paid ops yet — everything has been free so far."`), error (retry).

**Responsive:** table becomes horizontally scrollable on `< md`.

---

### 6.7 `/settings` — Settings *(W6-003 + ad-hoc)*

**Purpose:** Language toggle, per-session budget, style seed editor, OAuth management.

**Layout:**
- `<AppShell>` + `<PageHeader title="Settings" />`.
- Left sub-nav on `≥ md`, top tabs on `< md`. Sections:
  1. **Account** — email (read-only), change password.
  2. **Integrations** — Google Drive (connected email + Disconnect), Claude API key status, Replicate API key status. No key input UI — keys live in env; show "configured ✓/✗".
  3. **Budget** — show `SESSION_BUDGET_USD` and `SESSION_HARD_CAP_USD` from server; read-only (change via env).
  4. **Language** — `es | en` toggle (W6-003). Persists in localStorage + NextAuth session.
  5. **Style seed** — textarea to paste past IG captions (writes to server, stored per user).

**Data required:**
```ts
// GET /api/v1/auth/me → { email, createdAt }
// GET /api/v1/settings → { budgetUsd, hardCapUsd, integrations: { google: bool, claude: bool, replicate: bool }, styleSeedPresent: bool }
// PUT /api/v1/settings/style-seed { text } → void
```

**States:** standard loading/error; style-seed textarea has "Save" disabled until dirty.

**Responsive:** sub-nav collapses to tabs on `< md`; forms follow **Form** grid (§3.2).

---

### 6.8 Modals & overlays

Reusable, called from many places. Enumerated here so they are not re-invented.

| Modal | Triggered by | Content |
|---|---|---|
| `<CostConfirm>` | Every paid op | §5.8 |
| `<ConfirmDestructive>` | Resync, Delete session, Delete group, Reject+Regenerate | Title, body describing what will be lost, "Type to confirm" only for Resync. Buttons: Cancel / Confirm (destructive). |
| `<ConnectDriveDialog>` | Dashboard CTA | Explains scope (`drive.readonly`), Continue → redirects to OAuth. |
| `<FaceCropDialog>` | Face tab download | Shows crop preview + "Download PNG" + copy-with-EXIF warning. |
| `<ExportReadyToast>` | Export finished | Success toast with "Download" action. |
| `<BudgetExceededBanner>` | Cost > soft cap | In-line orange banner inside `<CostConfirm>`; offers override. Blocking banner when > hard cap. |

---

### 6.9 Error & empty states — catalog

| Scenario | Component | Copy (Spanish default) |
|---|---|---|
| No sessions | `<EmptyState icon=Folder>` | "Aún no hay sesiones. Conecta Google Drive y sincroniza una carpeta." |
| No assets in session | `<EmptyState icon=ImageOff>` | "Esta sesión está vacía. Revisa la carpeta o re-sincroniza." |
| No groups yet | `<EmptyState icon=Group>` | "Nada agrupado todavía. Ejecuta 'Re-agrupar' cuando la sincronización termine." |
| No faces detected | inline hint in Face tab | "No se detectaron rostros en esta foto." |
| Drive disconnected | card CTA | "Google Drive no está conectado." |
| API 401 | global redirect | redirect to `/login` + toast "Tu sesión expiró." |
| API 429 | toast | "Demasiados intentos. Espera unos minutos." |
| API 5xx | `<ErrorState>` | "Algo falló. Intenta de nuevo." |
| Budget hard-cap hit | blocking banner | "Has alcanzado el límite de gasto de esta sesión. Cámbialo en la configuración." |

---

## 7. Loading-State Playbook

Every `apiFetch` call in UI must map to one of these patterns — pick the least jarring:

1. **Skeletons** for grids and lists known to be > 1 card (session cards, asset grid). Preserve final layout to avoid CLS.
2. **Spinner button** for per-action loads (submit, accept, generate).
3. **Inline progress** (`<Progress>`) for long-running jobs with SSE feedback (sync, export, blend).
4. **Soft blur + overlay** for paid ops that take > 2s without progress (object removal) — blur the preview, show centered spinner + "Generating…".
5. **Never** a top-of-page spinner with an empty body. The page must show its own chrome immediately.

---

## 8. Cost UX pattern (mandatory)

For any action that spends money:

1. The trigger renders a `<CostBadge kind="paid" | "ai" estimate={...} />` next to its label **before** click.
2. Clicking opens `<CostConfirm>`; that's the only surface that starts the job.
3. When running, the trigger shows a spinner with "Running…" and is disabled.
4. On success, success toast with "Added $X.XX to this session".
5. On failure, destructive toast with retry action (unless the Replicate/Claude call itself failed with a billing error, in which case link to `/settings`).

Free ops (local grouping, deterministic re-group, manual upload) skip all of the above — just do the thing.

---

## 9. Copy & tone

- Default language: **Spanish (es)**. English is a toggle (W6-003).
- Voice: short, neutral, informative. Not cute, not corporate. No exclamation marks except in success toasts.
- Numbers: money as `$1.23` (USD), two decimals always. Counts as raw integers. Dates as `DD MMM YYYY` (e.g., `16 abr 2026`) via `Intl.DateTimeFormat("es")`.
- Buttons: verb-first, lowercase after first word (Spanish). "Sincronizar" not "Sincronizar Ahora". Destructive actions are explicit: "Eliminar sesión" not "Eliminar".
- Keep user-facing strings in one place per component (top of file) until `next-intl` lands; then extract to `messages/{es,en}.json`.

---

## 10. Checklist before you open a PR

Every UI change must pass this list (mirrored in `.claude/skills/ui-changes`):

- [ ] Reads DESIGN.md + CONVENTIONS.md section relevant to the change.
- [ ] Uses Tailwind **tokens** (`bg-background`, etc.), not hand-mixed colors.
- [ ] Responsive baseline at `xl`, degrades cleanly down to `sm`.
- [ ] Works in dark theme (default); no hardcoded light colors.
- [ ] Every interactive element keyboard-reachable with a visible focus ring.
- [ ] Images have `alt`.
- [ ] Async: has loading + success + error paths, no silent failures.
- [ ] Paid op: has `<CostBadge>` + `<CostConfirm>`.
- [ ] Destructive op: has `<ConfirmDestructive>` (or inline confirm for small cases).
- [ ] New strings: grouped at the top of the file for future i18n extraction.
- [ ] No default export unless it's a Next.js page/layout.
- [ ] Types use the shared `types/api.ts` — no duplicates.

---

## 11. Open design questions

Track additions here rather than in CLAUDE.md.

- [ ] Edit history UI (data exists, no screen yet). Probably a right-panel tab in `/edit` with a version tree. V1.
- [ ] AI grouping refinement UX (opt-in per cluster). Probably a "🤖 Refine" button at group header with cost badge. V1.
- [ ] Mobile capture flow — not planned; just verify the grid is *readable* on phone.
- [ ] Exporting multiple groups at once (zip of zips). V1.
- [x] Keyboard-shortcut overlay (`?`). Specced in §6.10.

---

### 6.10 Keyboard shortcut overlay *(W6, nice-to-have)*

**Purpose:** `?` key reveals a two-column modal listing every keyboard shortcut in the app.

**Layout:**
- `<Dialog>` (shadcn). `max-w-lg`. No close button — Esc / `?` / click-outside closes.
- Header: "Atajos de teclado" (`text-xl font-semibold`).
- Body: two columns (`grid-cols-2 gap-x-8 gap-y-1`).
- Each row: `<kbd>` chip (monospace, `bg-muted px-1.5 py-0.5 rounded text-xs border border-border`) + description `text-sm`.
- Grouped under headings: **Revisión** / **Edición** / **Global**.

**Shortcut catalog:**

| Scope | Key | Action |
|---|---|---|
| Global | `?` | Toggle shortcut overlay |
| Global | `Esc` | Close modal / back |
| Review | `←` `→` | Move focus between assets |
| Review | `↑` `↓` | Move focus between groups |
| Review | `X` | Quick-reject focused asset |
| Review | `Enter` | Open `/edit` for focused asset |
| Review | `G` | Focus group title (inline edit) |
| Edit | `←` `→` | Cycle proposals |
| Edit | `1` `2` `3` `4` | Switch correction tabs |
| Edit | `Enter` | Accept current proposal |
| Edit | `R` | Reject + regenerate |
| Edit | `M` | Reject + manual |
| Edit | `Esc` | Back to review |

**States:** always modal; no loading.

**Responsive:** same on all breakpoints; stacks to single column on `< sm`.

---

## 12. Skeleton loading specs

Each screen's skeleton preserves the **exact layout** of the loaded state to prevent CLS.

### 12.1 Dashboard (`/dashboard`)

```
<Skeleton className="h-20 w-full rounded-lg mb-4" />   {/* Drive card */}
<div className="grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
  {Array.from({ length: 6 }).map(() => (
    <div className="border border-border rounded-lg p-0 overflow-hidden">
      <Skeleton className="aspect-[4/3] w-full" />
      <div className="p-4 space-y-2">
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-3 w-1/2" />
        <Skeleton className="h-5 w-16 rounded-full" />
      </div>
    </div>
  ))}
</div>
```

### 12.2 Review grid (`/session/{id}`)

Per group:
```
<div className="space-y-2 mb-8">
  <div className="flex justify-between">
    <Skeleton className="h-6 w-40" />        {/* group title */}
    <Skeleton className="h-8 w-24" />        {/* actions */}
  </div>
  <div className="grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-2">
    {Array.from({ length: 6 }).map(() => (
      <Skeleton className="aspect-[4/5] rounded-md" />
    ))}
  </div>
</div>
```

### 12.3 Edit view (`/edit/{assetId}`)

```
{/* Canvas area */}
<Skeleton className="flex-1 rounded-none" />
{/* Right panel */}
<div className="w-96 border-l border-border p-4 space-y-4">
  <Skeleton className="h-8 w-full" />         {/* tab strip */}
  <Skeleton className="h-32 w-full rounded-lg" />   {/* control card */}
  <Skeleton className="h-24 w-full rounded-lg" />   {/* changes log */}
</div>
```

### 12.4 Cost log (`/session/{id}/cost`)

```
<div className="grid-cols-3 gap-4 mb-6">
  {[...Array(3)].map(() => <Skeleton className="h-20 rounded-lg" />)}
</div>
<div className="space-y-1">
  {[...Array(8)].map(() => <Skeleton className="h-10 w-full rounded" />)}
</div>
```

---

## 13. Drag-and-drop visual contract

Used in `/session/{id}` to reorganize assets between groups (dnd-kit).

### 13.1 States

| State | Visual |
|---|---|
| **Idle** | Normal card |
| **Dragging (ghost)** | `opacity-50 scale-95 rotate-1` on the source card |
| **Drag overlay** | Full-opacity card with `shadow-lg ring-2 ring-ring rotate-2 scale-105` rendered in dnd-kit's overlay portal |
| **Valid drop target (group)** | Group header pulses `bg-accent/30` border becomes `border-ring` |
| **Invalid drop** | Red flash `bg-destructive/10` on the container (100ms, then fades) |
| **Drop complete** | Card animates into final position `transition-transform duration-200` |

### 13.2 Constraints

- Dragging is **disabled** on touch breakpoints `< md`. Long-press opens a "Move to group" `<DropdownMenu>` instead.
- Within a group, cards can be reordered by dragging. Order is persisted via `PATCH /groups/{id}/assets/reorder`.
- Cross-group drops: `PATCH /group-assets/{assetId}/move { targetGroupId, position }`.
- Ungrouped drawer: accepts drops from any group (unassigns asset). Emits drag from its strip to any group.

### 13.3 Touch fallback (< md)

Long-press (300ms) on an asset card shows a `<DropdownMenu>`:
```
Move to group
  ├─ Group "Roma Day 1"
  ├─ Group "Roma Day 2"
  └─ Ungrouped
```

---

## 14. Form validation and error patterns

### 14.1 Field-level validation

- Validate `onBlur`, not `onChange` (less noise).
- Error message replaces the hint text below the field (`text-xs text-destructive`).
- The field border switches to `border-destructive ring-destructive/20`.
- Use React Hook Form + zod. Schemas live next to the form file.

### 14.2 Form-level errors

- Server errors (non-field) render in a `<Alert variant="destructive">` above the submit button.
- Use `ApiError.message` verbatim for the user-facing string (API is responsible for safe copy).

### 14.3 Optimistic updates

- Apply optimistic state immediately (React `useOptimistic` or local state).
- On failure, roll back + destructive toast with "Retry" action.
- Never leave the UI in an indeterminate state after a failed mutation.

### 14.4 Submit button conventions

| State | Classes |
|---|---|
| Idle | `<Button>` default |
| Submitting | `disabled` + `<Loader2 className="animate-spin h-4 w-4 mr-2" />` |
| Success | brief `<CheckCircle2 className="h-4 w-4 mr-2 text-emerald-400" />` (300ms), then reset |
| Error | reset to idle; error shown elsewhere |

---

## 15. Micro-interaction catalog

Exhaustive list of interactive feedback that must be consistent across the app.

| Element | Interaction | Visual |
|---|---|---|
| Asset thumbnail | Hover | `ring-2 ring-ring ring-offset-2` + bottom gradient fades in |
| Asset thumbnail | Focus (keyboard) | `ring-2 ring-ring ring-offset-2 ring-offset-background` (permanent) |
| Asset quick-reject | Click `×` | Immediate `opacity-40 grayscale transition-all duration-150`, toast "Rechazada. Deshacer" |
| Asset undo reject | Toast action | `opacity-100 grayscale-0 transition-all duration-150` |
| Session card | Hover | `border-ring` |
| Compare slider handle | Drag | `scale-110 cursor-ew-resize` on handle div |
| Compare slider | Release | `transition-[left] duration-300 ease-out` snap to nearest 5% |
| Sidebar toggle | Click | `transition-[width] duration-200 ease-in-out` |
| Inline group title | Click | Input replaces text; auto-focuses; Esc cancels |
| Cost badge | Mount | fade-in `animate-in fade-in duration-150` (only first render) |
| Progress bar | Update | `transition-[width] duration-500 ease-out` |
| Near-dup cluster expand | Click | `grid` animates from `max-h-0` to `max-h-[999px]` with `overflow-hidden transition-[max-height] duration-300` |
| Primary button | Active/press | `active:scale-[0.97] transition-transform duration-75` |
| Destructive button | Active | `active:brightness-90` |
| Toast | Enter | `animate-in slide-in-from-right-5 fade-in duration-200` |
| Toast | Exit | `animate-out slide-out-to-right-5 fade-out duration-150` |
| Modal | Enter | `animate-in fade-in zoom-in-95 duration-150` |
| Modal | Exit | `animate-out fade-out zoom-out-95 duration-100` |

All `motion-safe:` variants must wrap transitions that move layout. Opacity-only transitions are allowed without `motion-safe:`.

---

## 16. SSE progress patterns

Used during Resync (sync) and Export. Every long-running job uses the same visual contract.

### 16.1 Sync progress (`/session/{id}` — status: syncing)

```
┌──────────────────────────────────────────────────┐
│ Sincronizando… IMG_0042.HEIC (48 de 200)         │
│ [████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 24 %   │
└──────────────────────────────────────────────────┘
```

- `<Progress value={pct} className="h-1.5" />` (shadcn, full width, below session header).
- File name: `text-xs text-muted-foreground font-mono truncate`.
- When done: progress bar disappears (`transition-opacity duration-300`), status pill → "Listo".

### 16.2 Export progress

- After clicking "Download ZIP", a full-width inline `<Progress>` replaces the button.
- When done: `<ExportReadyToast>` fires (`sonner`, success variant, "Descargar" action).

### 16.3 Object removal / face blend (2-step paid ops)

- Canvas blurred (`blur-sm opacity-60 transition-all duration-200`).
- Centered spinner overlay: `<Loader2 className="animate-spin h-8 w-8 text-primary" />` + "Generando…" below.
- SSE `edit.completed` → remove blur, refresh preview URL + SSE triggers `mutate()` on the edit version query.

### 16.4 Aria live regions

Every SSE-driven progress string must also be announced:
```tsx
<span aria-live="polite" className="sr-only">{progressText}</span>
```

---

## 17. Responsive breakpoint decision tree

When implementing a new component, walk this tree to decide its layout at each breakpoint:

```
Is it full-screen?  (edit view)
  YES → no container, no sidebar, full viewport at all breakpoints
  NO  → uses <AppShell>

Does it have a right panel / sidebar?
  YES → w-96 at ≥ lg | bottom sheet at md | full-screen sheet at < md
  NO  → continues

Is it a data grid?  (assets, sessions)
  YES → Dense or Comfortable grid template (§3.2)
  NO  → continues

Is it a single record / form?
  YES → max-w-md (auth/settings) or max-w-2xl (new session)
  NO  → full container
```

### 17.1 Sidebar on mobile

The `<AppShell>` passes a `sidebarOpen` boolean via context. On `< md`:
- `<Sheet side="left">` with `w-64` content — same `<Sidebar>` component, no duplication.
- Hamburger button in `<TopBar>` triggers it (`h-10 w-10`).
- Clicking any nav item closes the sheet.

### 17.2 Table scrolling on small screens

All `<Table>` uses:
```tsx
<div className="overflow-x-auto -mx-4 px-4 md:mx-0 md:px-0">
  <Table>…</Table>
</div>
```
This lets the table scroll horizontally while keeping the page padding on mobile.

---

## 18. Component placement quick-reference

```
components/shared/
  AppShell.tsx
  Sidebar.tsx
  TopBar.tsx
  MobileNav.tsx
  PageHeader.tsx
  EmptyState.tsx
  ErrorState.tsx
  CostBadge.tsx
  CostConfirm.tsx
  ConfirmDestructive.tsx
  ToasterWrapper.tsx
  BudgetExceededBanner.tsx
  KeyboardShortcutOverlay.tsx

components/review/
  GroupBlock.tsx
  GroupBlock.client.tsx
  AssetCard.tsx
  AssetCard.client.tsx
  UngroupedDrawer.tsx
  NearDupStack.tsx
  DragOverlayCard.tsx

components/edit/
  CompareSlider.tsx
  CorrectionTabs.tsx
  ColorPanel.tsx
  CropPanel.tsx
  RemovePanel.tsx
  FacePanel.tsx
  ChangesLog.tsx
  ProposalCycler.tsx

components/ui/                    ← shadcn-generated, never hand-write
```
