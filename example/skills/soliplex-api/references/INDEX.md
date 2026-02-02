# Reference Index

Meta-guide to soliplex-api skill references.

## Skill Structure

```
soliplex-api/
├── SKILL.md            # Entry point (activation triggers, quick start)
├── REFERENCE.md        # Client usage, script reference, examples
├── references/         # Detailed technical documentation
│   ├── INDEX.md        # This file
│   ├── architecture.md # Core concepts, runtime flow
│   ├── ag-ui.md        # AG-UI protocol, events, SSE
│   ├── auth.md         # Authentication & authorization
│   ├── config-system.md
│   ├── adapter-patterns.md
│   └── ...
└── scripts/            # Executable code
    ├── client.py
    └── soliplex_client.py
```

## Reference Map

| Reference | Purpose | When to Read |
|-----------|---------|--------------|
| `../REFERENCE.md` | Client usage, CLI commands, code examples | Using the skill scripts |
| `design-principles.md` | Core principles for building integrations | First, before any development |
| `architecture.md` | Core concepts, runtime flow, directory structure | Understanding the system |
| `ag-ui.md` | AG-UI protocol, events, state management, SSE parsing | Working with conversations |
| `auth.md` | Authentication, authorization, security warnings | Security & access control |
| `config-system.md` | ToolConfig, RoomConfig, InstallationConfig, YAML structure | Writing configuration |
| `adapter-patterns.md` | Tool patterns (Pattern A/B), caching, MCP compatibility | Building adapters |
| `soliplex-skills-example.md` | Case study: how soliplex_skills was built | Learning by example |
| `api-reference.md` | Complete HTTP endpoints, request/response formats | API integration |

## Key Topics by Resource

**architecture.md:**
- Core concepts (Installation, Room, Tool)
- Runtime flow diagram
- Directory structure
- Links to detailed docs

**ag-ui.md:**
- Run lifecycle & hierarchy
- State management (event sourcing)
- 25+ AG-UI event types
- SSE parsing with code examples
- Thinking events (ephemeral)

**auth.md:**
- OIDC/JWT authentication
- Policy-based access control (ACL)
- Security warnings (public-by-default!)
- MCP token authentication
- CLI authorization commands

**config-system.md:**
- Corrected YAML structures (installation.yaml, room_config.yaml)
- `tool_name` resolution (NOT `type` discriminator)
- `mcp_client_toolsets` (separate from `tools`)
- Environment variables

**adapter-patterns.md:**
- Pattern A (Frozen Configuration) vs Pattern B (Runtime Context)
- Agent caching lifecycle (canonical source)
- Error handling (wiring vs runtime)
- MCP compatibility matrix
- Packaging checklist

**api-reference.md:**
- Complete endpoint tables (Rooms, AG-UI, Completions, Installation)
- Message data models (polymorphic)
- Known limitations

## Reading Order

**New to Soliplex:**
1. `design-principles.md` - Understand the philosophy
2. `architecture.md` - Learn core concepts
3. `config-system.md` - Understand configuration

**Building an Adapter:**
1. `adapter-patterns.md` - Study patterns (includes agent caching)
2. `soliplex-skills-example.md` - See real implementation
3. `config-system.md` - Reference for configs

**API Integration:**
1. `api-reference.md` - Endpoints and protocol
2. `ag-ui.md` - AG-UI events and SSE parsing

**Security & Auth:**
1. `auth.md` - Authentication and authorization
2. `architecture.md` - Runtime flow context

## Resource Freshness

Each resource should track its freshness:

```markdown
---
version: 2.0
last_verified: 2026-02-01
covers:
  - soliplex (upstream review 2026-02-01)
  - soliplex_skills >= 0.3.0
references:
  - ~/dev/soliplex-upstream/src/soliplex/
  - PLAN_COMPREHENSIVE_REVIEW.md
  - KNOWN_ISSUES.md
---
```

**Review Methodology:** 7-group iterative review (Analysis → Critic → Synthesis) of upstream Soliplex source code.

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
