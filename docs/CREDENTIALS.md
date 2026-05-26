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
