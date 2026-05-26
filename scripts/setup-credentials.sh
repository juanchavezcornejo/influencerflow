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
  die "Missing $api_env. Run: make bootstrap"
fi

if [[ ! -f "$web_env" ]]; then
  die "Missing $web_env. Run: make bootstrap"
fi

# ============================================================================
# Section 1: Claude API Key
# ============================================================================

echo ""
log "━━━ 1. Claude API Key ━━━"
log "Get it from: https://console.anthropic.com/api/keys"
log "Should start with: sk-ant-"
log ""

anthropic_key=$(prompt_for_input \
  "ANTHROPIC_API_KEY" \
  "Paste your Claude API key" \
  "" \
  true)

ok "✓ Claude API key set"

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
