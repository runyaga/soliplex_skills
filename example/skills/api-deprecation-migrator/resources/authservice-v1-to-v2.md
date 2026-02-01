# AuthService API Migration Guide: v1 to v2

Official endpoint mapping for migrating from AuthService v1 (deprecated) to v2.

## Deprecation Timeline

- **Announcement**: January 15, 2025
- **Soft Deprecation**: February 1, 2025 (warnings in logs)
- **Hard Deprecation**: March 1, 2025 (v1 endpoints return 410 Gone)

## Endpoint Mappings

| Method | v1 Endpoint (Deprecated) | v2 Endpoint (New) | Breaking Changes |
|--------|--------------------------|-------------------|------------------|
| POST | `/v1/users/validate_token` | `/v2/tokens/introspect` | Request body changed (see below) |
| GET | `/v1/users/get_profile?id={id}` | `/v2/users/{id}` | Query param → path param |
| GET | `/v1/users/get_permissions` | `/v2/users/{id}/permissions` | Now requires user ID in path |
| POST | `/v1/users/create` | `/v2/users` | Response includes `created_at` |
| DELETE | `/v1/users/delete?id={id}` | `/v2/users/{id}` | Now uses DELETE method properly |
| POST | `/v1/auth/login` | `/v2/auth/sessions` | Returns session token, not user object |
| POST | `/v1/auth/logout` | `/v2/auth/sessions/current` | Use DELETE method |

## Request Body Changes

### Token Validation (v1 → v2)

**v1 Request:**
```json
{
  "token": "eyJhbG...",
  "validate_permissions": true
}
```

**v2 Request:**
```json
{
  "access_token": "eyJhbG...",
  "token_type_hint": "access_token",
  "include_permissions": true
}
```

### Response Changes

**v1 Response:**
```json
{
  "valid": true,
  "user_id": "usr_123",
  "permissions": ["read", "write"]
}
```

**v2 Response:**
```json
{
  "active": true,
  "sub": "usr_123",
  "scope": "read write",
  "client_id": "app_456",
  "exp": 1735689600
}
```

## Common Patterns to Search

When scanning your codebase, look for these patterns:

```
/v1/users/
/v1/auth/
AuthServiceV1
auth_client.v1
AUTHSERVICE_V1_URL
```

## Migration Tips

1. **Update one endpoint at a time** - Don't try to migrate everything at once
2. **Add feature flags** - Allow rollback if issues arise
3. **Update tests first** - Ensure your tests reflect v2 behavior before changing code
4. **Check error handling** - v2 returns different error codes/formats
5. **Monitor after deploy** - Watch for increased error rates
