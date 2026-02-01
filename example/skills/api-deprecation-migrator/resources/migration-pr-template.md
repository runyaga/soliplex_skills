# API Migration Pull Request Template

Use this template when creating PRs for API deprecation migrations.

---

## PR Title Format

```
chore(api): migrate {service-name} from {API} v1 to v2
```

Example: `chore(api): migrate user-profile-service from AuthService v1 to v2`

---

## PR Description Template

```markdown
## Summary

This PR migrates all calls from the deprecated **{API Name} v1** to **v2** endpoints.

**Migration Guide**: [Link to internal wiki/guide]
**Deprecation Deadline**: {DATE}

## Changes

### Endpoints Updated

| Old Endpoint | New Endpoint | Files Changed |
|--------------|--------------|---------------|
| `POST /v1/users/validate_token` | `POST /v2/tokens/introspect` | `auth.py:42` |
| `GET /v1/users/get_profile` | `GET /v2/users/{id}` | `profile.py:89,157` |

### Code Changes

- Updated `AuthClient` to use v2 endpoints
- Modified request/response handling for new payload format
- Updated error handling for v2 error codes

## Testing

- [ ] Unit tests updated and passing
- [ ] Integration tests updated and passing
- [ ] Manual testing against v2 staging environment
- [ ] Verified rollback procedure works

## Migration Checklist

- [ ] All v1 endpoint references removed
- [ ] Request payload format updated to v2 spec
- [ ] Response parsing updated for v2 format
- [ ] Error handling updated for v2 error codes
- [ ] Environment variables updated (if any)
- [ ] Documentation updated
- [ ] No hardcoded v1 URLs remain

## Rollback Plan

If issues arise after deployment:
1. Revert this PR
2. v1 endpoints remain functional until {DEPRECATION_DATE}
3. Alert #team-platform channel

## Related Issues

- Closes #{ISSUE_NUMBER}
- Related to #{TRACKING_ISSUE}
```

---

## Labels to Apply

- `api-migration`
- `chore`
- `no-release-notes`

## Reviewers

- @platform-team (required for API changes)
- @security-team (if auth-related)
