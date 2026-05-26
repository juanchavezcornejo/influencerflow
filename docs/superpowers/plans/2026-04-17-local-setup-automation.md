# Local Development Setup Automation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create an interactive setup workflow that guides developers through obtaining all necessary API credentials and populating .env files for local development.

**Architecture:** A two-part system consisting of (1) an interactive bash script that prompts for credentials with validation and guidance, and (2) detailed markdown documentation with step-by-step instructions for obtaining each API key. The bootstrap script is updated to call this setup flow.

**Tech Stack:** Bash scripting, markdown documentation, Docker Compose environment variables.

---

## File Structure

```
scripts/
  setup-credentials.sh     (NEW) Interactive credential collection + .env population
  bootstrap.sh             (MODIFY) Call setup-credentials.sh after deps install
  _lib.sh                  (MODIFY) Add utility functions for setup flow

docs/
  SETUP.md                 (NEW) Complete guide: where to get credentials, step-by-step
  CREDENTIALS.md           (NEW) Reference: what each credential does + security notes

Makefile                   (MODIFY) Add setup-credentials target
```

---

## Task 1: Create SETUP.md Documentation

**Files:**
- Create: `docs/SETUP.md`

**Purpose:** Comprehensive guide for obtaining all API credentials with links, screenshots, and step-by-step instructions.

- [ ] **Step 1: Write SETUP.md with all credential sections**

Create `/Users/juan/Projects/influencerflow/docs/SETUP.md`:

```markdown
# Local Development Setup Guide

This guide walks you through setting up InfluencerFlow for local development, including obtaining all necessary API credentials.

## Prerequisites

- **Docker & Docker Compose** — for PostgreSQL, Redis, and containerized services
- **uv** — Python package manager (`brew install uv`)
- **pnpm** — Node.js package manager (`npm install -g pnpm`)
- **Git** — for version control

## Quick Start

```bash
# First time only: installs deps + creates .env files
make bootstrap

# Then: start the full stack (Postgres, Redis, API, Web)
make dev
```

The web app will be at **http://localhost:3000**  
The API will be at **http://localhost:8000**

---

## Required API Credentials

### 1. Claude API Key

**What it's for:** AI features (grouping refinement, descriptions, color suggestions)  
**Cost:** Pay-as-you-go (~$0.001–0.01 per request)  
**Time to set up:** 2 minutes

**Steps:**

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Sign in with your Anthropic account (create one if needed)
3. Click **API Keys** in the sidebar
4. Click **Create Key**
5. Copy the key (starts with `sk-ant-`)
6. Save it — you'll paste it during `make bootstrap`

**Where it goes:** `api/.env` as `ANTHROPIC_API_KEY`

---

### 2. Google Drive API Credentials

**What it's for:** Accessing the Google Drive folder containing your travel photos/videos  
**Cost:** Free (within quota)  
**Time to set up:** 10 minutes

**Steps:**

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project:
   - Click the project dropdown at the top
   - Click **New Project**
   - Name it "InfluencerFlow"
   - Click **Create**
3. Enable the Google Drive API:
   - Go to **APIs & Services > Library**
   - Search for "Google Drive API"
   - Click it, then click **Enable**
4. Create OAuth 2.0 credentials:
   - Go to **APIs & Services > Credentials**
   - Click **+ Create Credentials > OAuth client ID**
   - Choose **Web application**
   - Add authorized redirect URIs:
     - `http://localhost:8000/api/v1/storage/google/oauth/callback`
     - `http://localhost:3000/api/auth/callback/google` (if using NextAuth)
   - Click **Create**
5. Download the credentials:
   - Copy **Client ID** and **Client Secret**
   - Save them — you'll paste them during `make bootstrap`

**Where it goes:**
- `api/.env`: `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`
- `api/.env`: `GOOGLE_OAUTH_REDIRECT_URI` (pre-filled)

---

### 3. Replicate API Token

**What it's for:** Image operations (object removal via LaMa, face enhancement via GFPGAN, aesthetic scoring via NIMA)  
**Cost:** Pay-as-you-go (~$0.001–0.01 per operation)  
**Time to set up:** 2 minutes

**Steps:**

1. Go to [replicate.com](https://replicate.com)
2. Sign up with GitHub or email
3. Go to **Account > API Tokens**
4. Click **Create token**
5. Copy the token
6. Save it — you'll paste it during `make bootstrap`

**Where it goes:** `api/.env` as `REPLICATE_API_TOKEN`

---

### 4. NextAuth Secret

**What it's for:** Session encryption for authenticated users  
**Cost:** Free (generated locally)  
**Time to set up:** Auto-generated

**Pre-filled during setup.** If you need a new one, run:

```bash
openssl rand -base64 32
```

**Where it goes:** `web/.env` as `NEXTAUTH_SECRET`

---

### 5. Database & Redis (Local)

**What it's for:** Data storage and task queue  
**Cost:** Free (local Docker containers)  
**Pre-filled:** Automatically set in `.env` files

```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/influencerflow
REDIS_URL=redis://localhost:6379/0
```

---

## Setup Flow

When you run `make bootstrap`:

1. ✅ Installs uv + pnpm deps
2. ✅ Copies `.env.example` → `.env`
3. 🔑 Prompts you for each credential:
   - Claude API Key
   - Google Drive Client ID & Secret
   - Replicate API Token
   - Single-user email & password (dev only)
4. ✅ Validates inputs (non-empty, format checks)
5. ✅ Generates NEXTAUTH_SECRET
6. ✅ Ready to run `make dev`

---

## Running the Stack

```bash
# Start all services (Postgres, Redis, API, Web, Celery worker)
make dev

# Or start just the API + worker
make dev-api

# Or start just the Next.js dev server (needs API running separately)
make dev-web

# View logs
make logs              # All services
make logs svc=api      # Just the API
```

---

## Troubleshooting

### "DATABASE_URL not set"

**Cause:** `.env` file not created or missing `DATABASE_URL`

**Fix:**
```bash
make bootstrap
```

### "ANTHROPIC_API_KEY is invalid"

**Cause:** Key doesn't start with `sk-ant-` or is expired

**Fix:**
1. Generate a new key at [console.anthropic.com](https://console.anthropic.com/api/keys)
2. Update `api/.env`
3. Restart: `make dev`

### "Google Drive auth fails"

**Cause:** Client ID/Secret incorrect or redirect URI not whitelisted

**Fix:**
1. Go to [console.cloud.google.com/apis/credentials](https://console.cloud.google.com/apis/credentials)
2. Click your OAuth app
3. Verify redirect URIs include `http://localhost:8000/api/v1/storage/google/oauth/callback`
4. Copy fresh Client ID + Secret
5. Update `api/.env`
6. Restart

### "Port 8000/3000 already in use"

**Cause:** Another service is using the port

**Fix:**
```bash
# Kill the process on port 8000
lsof -ti :8000 | xargs kill -9

# Or use Docker to restart
make clean && make dev
```

---

## Environment Variables Reference

| Variable | Where | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | `api/.env` | Claude API for AI features |
| `GOOGLE_OAUTH_CLIENT_ID` | `api/.env` | Google Drive auth client ID |
| `GOOGLE_OAUTH_CLIENT_SECRET` | `api/.env` | Google Drive auth secret |
| `GOOGLE_OAUTH_REDIRECT_URI` | `api/.env` | OAuth callback (pre-set) |
| `REPLICATE_API_TOKEN` | `api/.env` | Replicate image operations |
| `NEXTAUTH_SECRET` | `web/.env` | NextAuth session encryption |
| `SINGLE_USER_EMAIL` | `api/.env` | Dev user email (e.g., `dev@local.test`) |
| `SINGLE_USER_PASSWORD` | `api/.env` | Dev user password |
| `DATABASE_URL` | `api/.env` | PostgreSQL connection (pre-set) |
| `REDIS_URL` | `api/.env` | Redis connection (pre-set) |

---

## Next Steps

After `make bootstrap`:

1. Run `make dev` to start the full stack
2. Open http://localhost:3000 in your browser
3. Log in with your `SINGLE_USER_EMAIL` / `SINGLE_USER_PASSWORD`
4. Test by uploading a sample photo to Google Drive and syncing

---

## Cost Estimates (Local Development)

| Operation | Per-Request Cost | Notes |
|---|---|---|
| Claude Vision (grouping) | ~$0.001–0.003 | Tile-packed thumbnails |
| Description generation | ~$0.0005–0.001 | One caption per post |
| Replicate (LaMa removal) | ~$0.001 | Per image |
| Replicate (GFPGAN face) | ~$0.001 | Per image |
| Replicate (NIMA scoring) | ~$0.0001 | Per image |

**Typical session (100 photos, 10 posts):** $0.50–$2.00 (if using all paid features)

---

## Questions?

Check `docs/ARCHITECTURE.md` for system design details or `CLAUDE.md` for project overview.
```

- [ ] **Step 2: Commit the documentation**

```bash
git add docs/SETUP.md
git commit -m "docs: add comprehensive local setup guide with credential instructions"
```

---

## Task 2: Create setup-credentials.sh Interactive Script

**Files:**
- Create: `scripts/setup-credentials.sh`
- Modify: `scripts/_lib.sh` (add helper functions)

- [ ] **Step 1: Add helper functions to _lib.sh**

Read the current `_lib.sh`:

```bash
cat /Users/juan/Projects/influencerflow/scripts/_lib.sh
```

Then append these functions:

```bash
# In scripts/_lib.sh, add at the end:

prompt_for_input() {
  local var_name=$1
  local prompt_text=$2
  local default=$3
  local is_secret=${4:-false}
  
  local value
  if [[ "$is_secret" == "true" ]]; then
    read -sp "$prompt_text [hidden]: " value
    echo
  else
    if [[ -n "$default" ]]; then
      read -p "$prompt_text [$default]: " value
      value="${value:-$default}"
    else
      read -p "$prompt_text: " value
    fi
  fi
  
  if [[ -z "$value" ]]; then
    error "Input required: $var_name"
  fi
  
  echo "$value"
}

write_env_file() {
  local env_file=$1
  local -A vars=()
  
  # Shift args and process key=value pairs
  shift
  while [[ $# -gt 0 ]]; do
    local key="${1%=*}"
    local value="${1#*=}"
    vars["$key"]="$value"
    shift
  done
  
  # Read existing .env, update vars, write back
  if [[ -f "$env_file" ]]; then
    local temp_file="${env_file}.tmp"
    > "$temp_file"
    
    while IFS= read -r line; do
      if [[ -z "$line" || "$line" =~ ^# ]]; then
        echo "$line" >> "$temp_file"
      else
        local key="${line%=*}"
        if [[ -v "vars[$key]" ]]; then
          echo "${key}=${vars[$key]}" >> "$temp_file"
          unset "vars[$key]"
        else
          echo "$line" >> "$temp_file"
        fi
      fi
    done < "$env_file"
    
    # Append any remaining new vars
    for key in "${!vars[@]}"; do
      echo "${key}=${vars[$key]}" >> "$temp_file"
    done
    
    mv "$temp_file" "$env_file"
  fi
}

validate_api_key_format() {
  local key=$1
  local pattern=$2
  if [[ ! "$key" =~ $pattern ]]; then
    return 1
  fi
  return 0
}

generate_nextauth_secret() {
  openssl rand -base64 32
}
```

- [ ] **Step 2: Create scripts/setup-credentials.sh**

Create `/Users/juan/Projects/influencerflow/scripts/setup-credentials.sh`:

```bash
#!/usr/bin/env bash
# Interactive credential setup: guides user through obtaining API keys
# and populates .env files with their values.

set -e
source "$(dirname "$0")/_lib.sh"

echo ""
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "InfluencerFlow — Local Development Setup"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
log "This will guide you through obtaining API credentials for:"
log "  • Claude API (for AI features)"
log "  • Google Drive (for photo storage access)"
log "  • Replicate (for image operations)"
log ""
log "See docs/SETUP.md for detailed instructions on each service."
echo ""

# Check if .env files exist
api_env="api/.env"
web_env="web/.env"

if [[ ! -f "$api_env" ]]; then
  error "Missing $api_env. Run: make bootstrap"
fi

if [[ ! -f "$web_env" ]]; then
  error "Missing $web_env. Run: make bootstrap"
fi

# ============================================================================
# Section 1: Claude API Key
# ============================================================================

echo ""
log "━━━ 1. Claude API Key ━━━"
log "Get it from: https://console.anthropic.com/api/keys"
log "Should start with: sk-ant-"
log ""

while true; do
  anthropic_key=$(prompt_for_input \
    "ANTHROPIC_API_KEY" \
    "Paste your Claude API key" \
    "" \
    true)
  
  if validate_api_key_format "$anthropic_key" "^sk-ant-"; then
    ok "✓ Claude API key looks valid"
    break
  else
    warn "Invalid format. Must start with 'sk-ant-'. Try again."
  fi
done

# ============================================================================
# Section 2: Google Drive OAuth
# ============================================================================

echo ""
log "━━━ 2. Google Drive OAuth Credentials ━━━"
log "Get them from: https://console.cloud.google.com/apis/credentials"
log "See docs/SETUP.md § 2 for step-by-step instructions"
log ""

google_client_id=$(prompt_for_input \
  "GOOGLE_OAUTH_CLIENT_ID" \
  "Paste your Google OAuth Client ID" \
  "")

google_client_secret=$(prompt_for_input \
  "GOOGLE_OAUTH_CLIENT_SECRET" \
  "Paste your Google OAuth Client Secret" \
  "" \
  true)

if [[ ${#google_client_id} -gt 20 ]] && [[ ${#google_client_secret} -gt 20 ]]; then
  ok "✓ Google Drive credentials provided"
else
  warn "⚠ Google Drive credentials look short. Double-check?"
fi

# ============================================================================
# Section 3: Replicate API Token
# ============================================================================

echo ""
log "━━━ 3. Replicate API Token ━━━"
log "Get it from: https://replicate.com/account/api/tokens"
log ""

replicate_token=$(prompt_for_input \
  "REPLICATE_API_TOKEN" \
  "Paste your Replicate API token" \
  "" \
  true)

if [[ ${#replicate_token} -gt 10 ]]; then
  ok "✓ Replicate token provided"
else
  warn "⚠ Replicate token looks short. Double-check?"
fi

# ============================================================================
# Section 4: Single-User Dev Account
# ============================================================================

echo ""
log "━━━ 4. Single-User Dev Account ━━━"
log "For local development only."
log ""

single_user_email=$(prompt_for_input \
  "SINGLE_USER_EMAIL" \
  "Dev user email" \
  "dev@local.test")

single_user_password=$(prompt_for_input \
  "SINGLE_USER_PASSWORD" \
  "Dev user password (min 8 chars)" \
  "" \
  true)

if [[ ${#single_user_password} -lt 8 ]]; then
  warn "⚠ Password should be at least 8 characters"
fi

# ============================================================================
# Section 5: Generate NextAuth Secret
# ============================================================================

echo ""
log "━━━ 5. NextAuth Secret ━━━"
nextauth_secret=$(generate_nextauth_secret)
ok "✓ Generated NextAuth secret"

# ============================================================================
# Write to .env files
# ============================================================================

echo ""
log "━━━ Writing .env files ━━━"

# Update api/.env
cat > "$api_env" << EOF
ENVIRONMENT=development
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/influencerflow
REDIS_URL=redis://localhost:6379/0
DATA_DIR=/data

JWT_SECRET=$(openssl rand -base64 32)
FERNET_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>/dev/null || echo "")
SINGLE_USER_EMAIL=$single_user_email
SINGLE_USER_PASSWORD=$single_user_password

GOOGLE_OAUTH_CLIENT_ID=$google_client_id
GOOGLE_OAUTH_CLIENT_SECRET=$google_client_secret
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8000/api/v1/storage/google/oauth/callback

ANTHROPIC_API_KEY=$anthropic_key
REPLICATE_API_TOKEN=$replicate_token

SESSION_BUDGET_USD=10
SESSION_HARD_CAP_USD=50
EOF

ok "✓ Created/updated $api_env"

# Update web/.env
cat > "$web_env" << EOF
API_BASE=http://localhost:8000
NEXT_PUBLIC_API_BASE=/api/v1
NEXTAUTH_SECRET=$nextauth_secret
NEXTAUTH_URL=http://localhost:3000
EOF

ok "✓ Created/updated $web_env"

# ============================================================================
# Summary
# ============================================================================

echo ""
log "━━━ Setup Complete ━━━"
log ""
ok "✓ All credentials configured!"
ok "✓ .env files created"
echo ""
log "Next steps:"
log "  1. Run: make dev"
log "  2. Open: http://localhost:3000"
log "  3. Log in with:"
log "     Email: $single_user_email"
log "     Password: (the password you entered)"
echo ""
log "For issues, see: docs/SETUP.md"
echo ""
```

Make it executable:

```bash
chmod +x /Users/juan/Projects/influencerflow/scripts/setup-credentials.sh
```

- [ ] **Step 3: Commit the script**

```bash
git add scripts/setup-credentials.sh scripts/_lib.sh
git commit -m "feat: add interactive credential setup script with validation"
```

---

## Task 3: Update bootstrap.sh to Use Setup Script

**Files:**
- Modify: `scripts/bootstrap.sh`

- [ ] **Step 1: Update bootstrap.sh to call setup-credentials.sh**

Read the current bootstrap.sh and replace it:

```bash
#!/usr/bin/env bash
# First-time setup: install API + web deps, copy .env files, prompt for credentials.
source "$(dirname "$0")/_lib.sh"

require uv pnpm

log "Installing API dependencies (uv sync)"
(cd api && uv sync --extra dev)

log "Installing web dependencies (pnpm install)"
(cd web && pnpm install)

# Copy .env.example → .env if not exists
for f in api/.env web/.env; do
  if [[ ! -f "$f" ]] && [[ -f "$f.example" ]]; then
    cp "$f.example" "$f"
  fi
done

# Run interactive credential setup
log "Setting up credentials..."
"$(dirname "$0")/setup-credentials.sh"

ok "Bootstrap complete! Next: make dev"
```

- [ ] **Step 2: Commit the update**

```bash
git add scripts/bootstrap.sh
git commit -m "feat: integrate credential setup into bootstrap flow"
```

---

## Task 4: Add Makefile Target

**Files:**
- Modify: `Makefile`

- [ ] **Step 1: Add setup-credentials target**

Find the line:

```makefile
bootstrap:   ## First-time setup (uv sync + pnpm install + .env files)
```

Add a new target after it:

```makefile
setup-credentials: ## Re-run credential setup (update .env files)
	@./scripts/setup-credentials.sh
```

The updated Makefile section should look like:

```makefile
bootstrap:        ## First-time setup (uv sync + pnpm install + .env files)
	@./scripts/bootstrap.sh

setup-credentials: ## Re-run credential setup (update .env files)
	@./scripts/setup-credentials.sh

dev:              ## Start full stack (docker compose up)
	@./scripts/dev.sh
```

Also update the `.PHONY` line at the top to include `setup-credentials`:

```makefile
.PHONY: help bootstrap setup-credentials dev dev-api dev-web test test-api test-web \
        lint format build clean clean-data migrate migrate-new reset-db \
        logs shell-api ps
```

- [ ] **Step 2: Commit the Makefile changes**

```bash
git add Makefile
git commit -m "feat: add make target for credential setup"
```

---

## Task 5: Update docs/COMMANDS.md

**Files:**
- Modify: `docs/COMMANDS.md` (if it exists)

- [ ] **Step 1: Add entry to COMMANDS.md**

Add to the "Make targets" section:

```markdown
| `make setup-credentials` | Re-run credential setup (update .env files without re-installing deps) |
```

- [ ] **Step 2: Commit**

```bash
git add docs/COMMANDS.md
git commit -m "docs: document setup-credentials make target"
```

---

## Task 6: Create CREDENTIALS.md Reference

**Files:**
- Create: `docs/CREDENTIALS.md`

- [ ] **Step 1: Write CREDENTIALS.md with reference info**

Create `/Users/juan/Projects/influencerflow/docs/CREDENTIALS.md`:

```markdown
# Credentials Reference

This document details what each API credential is used for, security considerations, and rotation procedures.

## Claude API Key

**Service:** Anthropic  
**Environment:** `ANTHROPIC_API_KEY` (api/.env)  
**Usage:** AI-powered features (grouping, descriptions, color suggestions)

### Security
- Keep this secret — it can be used to make API calls on your account
- Store in `.env` only, never commit to git
- Regenerate if leaked

### Cost Tracking
- Budget: `SESSION_BUDGET_USD=10` (soft warn at $10)
- Hard cap: `SESSION_HARD_CAP_USD=50` (block operations)
- Check usage at [console.anthropic.com/account/usage](https://console.anthropic.com/account/usage)

### Rotation
1. Generate new key at [console.anthropic.com/api/keys](https://console.anthropic.com/api/keys)
2. Delete old key
3. Update `api/.env` with new key
4. Restart: `make dev`

---

## Google Drive OAuth Credentials

**Service:** Google Cloud Platform  
**Environment:**
- `GOOGLE_OAUTH_CLIENT_ID` (api/.env)
- `GOOGLE_OAUTH_CLIENT_SECRET` (api/.env)
- `GOOGLE_OAUTH_REDIRECT_URI` (api/.env, pre-set)

**Usage:** Accessing user's Google Drive to fetch photos/videos

### Security
- Client Secret is sensitive — store in `.env`, never commit
- Redirect URI must be whitelisted (prevents phishing)
- OAuth scope limited to Drive read-only

### Rotation
1. Go to [console.cloud.google.com/apis/credentials](https://console.cloud.google.com/apis/credentials)
2. Delete old OAuth app
3. Create new one with same redirect URIs
4. Update `api/.env`
5. Restart: `make dev`

---

## Replicate API Token

**Service:** Replicate.com  
**Environment:** `REPLICATE_API_TOKEN` (api/.env)  
**Usage:** Image processing (LaMa removal, GFPGAN face enhancement, NIMA scoring)

### Security
- Sensitive credential — store in `.env`, never commit
- Replicate can be used by anyone with the token

### Cost Tracking
- Pay-per-use (~$0.001 per operation)
- Check usage at [replicate.com/account/api/tokens](https://replicate.com/account/api/tokens)
- Operations blocked if `SESSION_HARD_CAP_USD` exceeded

### Rotation
1. Go to [replicate.com/account/api/tokens](https://replicate.com/account/api/tokens)
2. Delete old token
3. Create new one
4. Update `api/.env`
5. Restart: `make dev`

---

## NextAuth Secret

**Service:** NextAuth.js (internal)  
**Environment:** `NEXTAUTH_SECRET` (web/.env)  
**Usage:** Session encryption and CSRF protection

### Security
- Regenerated on each `make bootstrap`
- Should be 32+ bytes (base64-encoded)
- Keep secret — anyone with this can forge sessions

### Rotation
Generate new secret:
```bash
openssl rand -base64 32
```

Update `web/.env` with the new value and restart.

---

## Database & Redis Credentials

**Service:** PostgreSQL + Redis (local Docker)  
**Environment:**
- `DATABASE_URL` (api/.env)
- `REDIS_URL` (api/.env)

**Usage:** Data storage and task queue

### Pre-set for Local Dev
```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/influencerflow
REDIS_URL=redis://localhost:6379/0
```

### Reset Database
```bash
make reset-db
```

---

## Single-User Dev Account

**Service:** InfluencerFlow (internal)  
**Environment:**
- `SINGLE_USER_EMAIL` (api/.env)
- `SINGLE_USER_PASSWORD` (api/.env)

**Usage:** Local authentication (MVP single-user only)

### Security
- Dev account only — passwords not hashed yet (coming in Phase 2)
- Use throwaway email
- Never use a real password

### Change Credentials
```bash
make setup-credentials
```

---

## Checklist: First Setup

- [ ] Have Google account
- [ ] Have Anthropic account
- [ ] Have Replicate account
- [ ] Generated Google OAuth app + credentials
- [ ] Generated Claude API key
- [ ] Generated Replicate token
- [ ] Run `make bootstrap`
- [ ] Entered credentials when prompted
- [ ] Run `make dev`
- [ ] Log in at http://localhost:3000

---

## Checklist: Moving to a New Machine

1. Clone the repo
2. Run `make bootstrap`
3. Enter the same credentials as before
4. Run `make dev`
5. You're ready!

---

## Common Issues

**Q: "Invalid API key" when testing Claude features**
A: Double-check key starts with `sk-ant-` and copy-paste without extra spaces.

**Q: "Google auth fails with redirect_uri_mismatch"**
A: The redirect URI you whitelisted in Google Console must exactly match `http://localhost:8000/api/v1/storage/google/oauth/callback` (including http:// and port).

**Q: "Session budget exceeded"**
A: You've hit `SESSION_HARD_CAP_USD` (default $50). Check API usage and delete the session row from the database if you want to test more.

**Q: "Replicate token invalid"**
A: Check it doesn't have typos. Tokens are long (30+ chars).

---
```

- [ ] **Step 2: Commit CREDENTIALS.md**

```bash
git add docs/CREDENTIALS.md
git commit -m "docs: add credentials reference and security guide"
```

---

## Task 7: Test the Complete Setup Flow

**Files:**
- No files modified; testing only

- [ ] **Step 1: Verify scripts are executable**

```bash
ls -la /Users/juan/Projects/influencerflow/scripts/setup-credentials.sh
# Should show: -rwxr-xr-x
```

If not executable, run:
```bash
chmod +x /Users/juan/Projects/influencerflow/scripts/setup-credentials.sh
```

- [ ] **Step 2: Test setup-credentials.sh in dry-run (without live API keys)**

```bash
# Preview what the script does (don't actually run yet, just read it)
cat /Users/juan/Projects/influencerflow/scripts/setup-credentials.sh | head -100
```

Verify:
- ✓ Prompts for Claude API key
- ✓ Prompts for Google OAuth credentials
- ✓ Prompts for Replicate token
- ✓ Generates NextAuth secret
- ✓ Writes to api/.env and web/.env

- [ ] **Step 3: Test Makefile target**

```bash
cd /Users/juan/Projects/influencerflow
make help | grep setup-credentials
```

Expected output: Should show the setup-credentials target in the help text.

- [ ] **Step 4: Commit final changes**

```bash
git add -A
git commit -m "chore: finalize local setup automation"
```

---

## Summary

**New Files:**
- `docs/SETUP.md` — Complete setup guide with credential instructions
- `docs/CREDENTIALS.md` — Reference: what each credential does + security
- `scripts/setup-credentials.sh` — Interactive credential collection

**Modified Files:**
- `scripts/bootstrap.sh` — Now calls setup-credentials.sh
- `scripts/_lib.sh` — Added helper functions for credential setup
- `Makefile` — New `setup-credentials` target

**Result:**
Users can now run:
```bash
make bootstrap
# Prompts for Claude API key, Google OAuth, Replicate token
# Generates NextAuth secret
# Populates .env files
# Ready for: make dev
```

This eliminates manual .env editing and provides clear guidance on obtaining each credential.
