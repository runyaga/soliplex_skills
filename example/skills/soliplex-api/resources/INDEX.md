# Resource Index

Meta-guide to soliplex-api skill resources.

## Resource Map

| Resource | Purpose | When to Read |
|----------|---------|--------------|
| `design-principles.md` | Core principles for building integrations | First, before any development |
| `architecture.md` | Soliplex concepts: rooms, tools, installations | Understanding the system |
| `config-system.md` | ToolConfig, RoomConfig, InstallationConfig | Writing configuration |
| `adapter-patterns.md` | Patterns for wrapping external libraries | Building adapters |
| `soliplex-skills-example.md` | Case study: how soliplex_skills was built | Learning by example |
| `api-reference.md` | HTTP endpoints, AG-UI protocol | API integration |

## Reading Order

**New to Soliplex:**
1. `design-principles.md` - Understand the philosophy
2. `architecture.md` - Learn core concepts
3. `config-system.md` - Understand configuration

**Building an Adapter:**
1. `adapter-patterns.md` - Study patterns
2. `soliplex-skills-example.md` - See real implementation
3. `config-system.md` - Reference for configs

**API Integration:**
1. `api-reference.md` - Endpoints and protocol
2. `architecture.md` - Understand what you're calling

## Resource Freshness

Each resource should track its freshness:

```markdown
---
version: 1.0
last_verified: 2025-02-01
covers:
  - soliplex >= 0.5.0
  - soliplex_skills >= 0.3.0
references:
  - src/soliplex_skills/config.py
  - src/soliplex_skills/tools.py
---
```

## Context Rot Detection

Resources can become stale when:
- Referenced code changes
- APIs evolve
- New patterns emerge
- Dependencies update

### Manual Validation Checklist

For each resource, verify:

- [ ] Code examples still run
- [ ] Referenced files still exist
- [ ] Function signatures match
- [ ] Config schemas are current
- [ ] Links are not broken

### Automated Validation

Run the validation script to check for rot:

```bash
cd example && uv run python skills/soliplex-api/scripts/validate_resources.py
```

The script checks:
1. **File references** - Do referenced files exist?
2. **Import statements** - Do imports work?
3. **Code blocks** - Does Python code parse?
4. **Config examples** - Do YAML examples validate?

### Rot Indicators

| Signal | Meaning |
|--------|---------|
| Import errors | Module structure changed |
| Missing files | Code was moved/deleted |
| Schema errors | Config format changed |
| Broken links | Resources reorganized |

## Contributing

When updating resources:

1. Update the `last_verified` date
2. Run validation script
3. Update `covers` versions if needed
4. Add to `references` if new files involved

When adding resources:

1. Add entry to this INDEX.md
2. Include frontmatter with version info
3. Add to appropriate reading order section
4. Create validation rules if applicable
