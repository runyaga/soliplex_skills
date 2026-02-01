---
name: api-deprecation-migrator
description: Assists developers in migrating codebases from deprecated API endpoints to new versions
---

# API Deprecation Migrator

A structured methodology for migrating codebases between API versions.

## When to Use This Skill

Use this skill when you need to:
- Find all usages of deprecated API endpoints in a codebase
- Understand the mapping from old endpoints to new ones
- Follow a standardized migration process
- Create properly documented pull requests

## Methodology

1. **Identify Target API**: Determine which API migration guide applies
2. **Load Migration Guide**: Read the relevant guide from resources to understand endpoint mappings
3. **Scan Codebase**: Use `find_deprecated_patterns.py` to locate all deprecated calls
4. **Report Findings**: Present file paths and line numbers to the user
5. **Guide Refactoring**: Help user update code using the migration mappings
6. **Provide PR Template**: Supply standardized PR template for the migration

## Resources

| Resource | Description |
|----------|-------------|
| `authservice-v1-to-v2.md` | Official AuthService v1 to v2 endpoint mappings |
| `migration-pr-template.md` | Standard PR template for API migrations |
| `migration-checklist.md` | Pre-flight checklist before submitting migration |

## Scripts

| Script | Description | Args |
|--------|-------------|------|
| `find_deprecated_patterns.py` | Scans directory for deprecated patterns | `{"patterns": [...], "directory": "..."}` |

## Example Workflow

```
User: I need to migrate user-service from AuthService v1 to v2

Agent:
1. list_skills() -> finds api-deprecation-migrator
2. load_skill("api-deprecation-migrator") -> reads this methodology
3. read_skill_resource("api-deprecation-migrator", "authservice-v1-to-v2.md")
   -> learns the endpoint mappings
4. run_skill_script("api-deprecation-migrator", "find_deprecated_patterns.py",
   {"patterns": ["/v1/users/"], "directory": "/code/user-service"})
   -> finds all deprecated calls
5. Guides user through refactoring each endpoint
6. read_skill_resource("api-deprecation-migrator", "migration-pr-template.md")
   -> provides PR template
```

## Value Proposition

**Without Skills**: Developer searches Confluence, asks in Slack, manually greps codebase, hopes they found everything.

**With Skills**: Agent has complete context - the process, the mappings, the scanner, and the templates - all bundled together and discoverable on-demand.
