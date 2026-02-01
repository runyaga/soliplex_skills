# Design Principles

Core principles for building Soliplex integrations and adapters.

## 1. Always Use pydantic-ai for LLM Connectivity

**Do not** use raw HTTP calls to LLM APIs or vendor SDKs directly.

```python
# WRONG - Direct API calls
import httpx
response = httpx.post("https://api.openai.com/v1/chat/completions", ...)

# WRONG - Vendor SDK
from openai import OpenAI
client = OpenAI()
response = client.chat.completions.create(...)

# RIGHT - pydantic-ai
from pydantic_ai import Agent
agent = Agent("openai:gpt-4o")
result = await agent.run("Your prompt")
```

**Why:**
- Unified interface across providers (OpenAI, Anthropic, Ollama, etc.)
- Built-in tool calling support
- Type-safe with Pydantic models
- Consistent with Soliplex's agent system

## 2. Check if Soliplex Integration Helps

Before building custom agent logic, ask:

| Question | If Yes | If No |
|----------|--------|-------|
| Does a Soliplex room already do this? | Use `HTTPClient.ask()` | Build new |
| Is this a reusable capability? | Create a skill | Inline code |
| Does it need tools/context? | Use room with tools | Simple agent |
| Multiple steps with state? | Room with system prompt | Single call |

**Decision flow:**
```
Need LLM capability?
    │
    ├─ Existing room handles it? ──► HTTPClient.ask(room_id, query)
    │
    ├─ Reusable across projects? ──► Create a skill
    │
    └─ One-off task? ──► pydantic-ai Agent directly
```

## 3. Skills Over Hardcoded Tools

Prefer skills (declarative, portable) over hardcoded tool functions.

```python
# WRONG - Hardcoded tool in agent
@agent.tool
def calculate_factorial(n: int) -> int:
    ...

# RIGHT - Skill with script
# skills/math-solver/scripts/calculate.py
# Then: run_skill_script("math-solver", "scripts/calculate.py", ...)
```

**Why:**
- Skills are discoverable (`list_skills`)
- Skills have documentation (SKILL.md, resources/)
- Skills are portable across rooms
- Skills can be versioned independently

## 4. Configuration Over Code

Put behavior in config files, not Python code.

```yaml
# RIGHT - room_config.yaml
agent:
  system_prompt: |
    You are a code reviewer. Use these tools...
tools:
  - tool_name: soliplex_skills.tools.run_skill_script
    directories:
      - ../../skills
```

```python
# WRONG - Hardcoded in Python
agent = Agent(
    "gpt-4o",
    system_prompt="You are a code reviewer...",
    tools=[my_custom_tool],
)
```

**Why:**
- Non-developers can modify behavior
- Version control for prompts
- Easy A/B testing of configurations
- Separation of concerns

## 5. Fail Fast, Validate Early

Validate configurations at load time, not runtime.

```python
# RIGHT - Validate on load
config = load_installation("installation.yaml")
config.reload_configurations()  # Fails here if invalid

# WRONG - Discover errors at runtime
def handle_request():
    room = get_room(room_id)  # Might fail here
    ...
```

## 6. DirectClient for Discovery, HTTPClient for Execution

Use the right client for the job:

| Task | Client | Why |
|------|--------|-----|
| List rooms/skills | DirectClient | No server needed |
| Validate configs | DirectClient | Offline testing |
| Send queries | HTTPClient | Needs running agent |
| Integration tests | HTTPClient | Tests full stack |
| CI/CD checks | DirectClient | No infrastructure |

## 7. Document with Resources, Not Comments

Put documentation in skill resources, not inline comments.

```
skills/my-skill/
├── SKILL.md           # Overview, quick start
├── scripts/           # Executable code
└── resources/
    ├── INDEX.md       # What's in each file
    ├── concepts.md    # Core concepts
    └── examples.md    # Usage examples
```

## 8. Version Your Resources

Track when documentation was written and what it covers:

```markdown
---
version: 1.0
last_verified: 2025-02-01
soliplex_version: ">=0.5.0"
---

# My Resource

...
```

This helps detect context rot (see INDEX.md for validation).
