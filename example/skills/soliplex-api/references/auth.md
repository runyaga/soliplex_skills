# Authentication & Authorization

## Authentication (authn.py)

- **OIDC/JWT**: RS256 validation, iterates through `oidc_auth_system_configs`
- **No Auth Mode**: `--no-auth-mode` returns `NO_AUTH_MODE_USER_TOKEN`
- **User Model**: Ephemeral JWT dict (NO local User table!)

```yaml
# installation.yaml
oidc_auth_system_configs:
  - provider: google
    issuer: https://accounts.google.com
    token_validation_pem: |
      -----BEGIN PUBLIC KEY-----
      ...
```

### API Authentication

All API endpoints (except health/debug) require OAuth2 authentication.

**Header:** `Authorization: Bearer <token>`

```bash
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/rooms
```

## Authorization (authz/schema.py)

**Policy-Based Access Control:**

| Table | Purpose |
|-------|---------|
| `AdminUser` | Email allowlist for admin access |
| `RoomPolicy` | Per-room policy with `default_allow_deny` |
| `ACLEntry` | Granular rules (everyone, authenticated, email, preferred_username) |

### Access Logic

1. Admin check → ALLOW
2. Policy lookup for room_id
3. **NO policy found → ALLOW (PUBLIC!)** ⚠️
4. Policy found → iterate ACL by **creation time**, return first match or `default_allow_deny`

⚠️ **SECURITY WARNING**: Rooms are PUBLIC by default if no policy exists!

## Authorization Persistence Warning

⚠️ Default `room_authz_dburi` uses **IN-MEMORY SQLite**.

Server restart **WIPES all policies** → rooms revert to PUBLIC.

**Fix:** Configure persistent DB:
```yaml
room_authz_dburi: sqlite:///./authz.db
# or PostgreSQL
room_authz_dburi: postgresql://user:pass@host/db
```

## MCP Authentication

Rooms can be exposed as MCP servers:

```yaml
# room_config.yaml
allow_mcp: true
```

**Token endpoint:** `GET /api/v1/rooms/{room_id}/mcp_token`

**Token Characteristics:**
- Symmetric encryption via `itsdangerous.URLSafeTimedSerializer`
- `room_id` used as SALT → tokens room-bound (can't replay cross-room)
- `MCP_TOKEN_MAX_AGE` default: 3600s

**⚠️ Limitations:**
- No token revocation (rotate `URL_SAFE_TOKEN_SECRET` to invalidate ALL tokens)
- `FASTAPI_CONTEXT` tools are **AUTO-EXCLUDED** (invisible via MCP)

## Security Warnings Summary

| Issue | Impact | Mitigation |
|-------|--------|------------|
| Rooms PUBLIC by default | Unauthorized access if no policy | Always create RoomPolicy |
| In-memory authz DB | Policies lost on restart | Use persistent DB |
| JWT audience validation disabled | Accepts tokens for other apps | Document/accept risk |
| Multi-worker session breakage | Random logouts | Set `SESSION_SECRET_KEY` |
| MCP token no revocation | Can't invalidate compromised tokens | Short expiry, rotate secret |

## CLI Authorization Commands

```bash
# List admin users
soliplex list-admin-users --installation path/to/install

# Add admin (requires persistent DB or --skip-ram-db-check)
soliplex add-admin-user --installation path/to/install --email admin@example.com

# Show room ACL
soliplex show-room-authz --installation path/to/install --room-id my-room

# Add user to room
soliplex add-room-user --installation path/to/install --room-id my-room --email user@example.com

# Clear room policies (⚠️ makes room public!)
soliplex clear-room-authz --installation path/to/install --room-id my-room
```

**Note:** CLI commands exit by default if using in-memory DB. Use `--skip-ram-db-check` to override.
