# AG-UI System Architecture

AG-UI (Agent UI) is Soliplex's protocol for managing conversations.

## Run Lifecycle & Hierarchy

Runs form a **tree** structure via `parent_run_id`:

```
Thread
  └── Run 1 (root)
        └── Run 2 (child of 1)
              └── Run 3 (child of 2)
```

**Validation Rules:**
- **Room Isolation**: `ThreadRoomMismatch` if thread accessed via wrong room
- **Single Execution**: `RunAlreadyStarted` if re-executing same run

## State Management (Event Sourcing)

| Event Type | Purpose |
|------------|---------|
| `STATE_SNAPSHOT` | Full state object replacement |
| `STATE_DELTA` | JSON Patches (RFC 6902) applied to state |
| `ACTIVITY_SNAPSHOT` | Full widget content |
| `ACTIVITY_DELTA` | Widget patches |

`as_run_agent_input()` regenerates input for next run from current state.

## Persistence & Replay

⚠️ **Thinking Events are EPHEMERAL**:
- `THINKING_TEXT_MESSAGE_*` events are streamed live but NOT persisted
- Users see "Thinking" in real-time, but it disappears on page refresh
- This is an intentional UI/UX decision

## Message Types (Polymorphic)

| Type | Structure |
|------|-----------|
| `AssistantMessage` | `{id, role: "assistant", content, tool_calls[]}` |
| `ToolMessage` | `{id, role: "tool", tool_call_id, content}` |
| `ActivityMessage` | `{id, role: "assistant", activity_type, content: {...}}` |

## AG-UI Event Types

SSE stream returns 25+ event types. Key categories:

**Text Messages:**
| Type | Description |
|------|-------------|
| `TEXT_MESSAGE_START` | New message begins |
| `TEXT_MESSAGE_CONTENT` | Text delta (streaming) |
| `TEXT_MESSAGE_END` | Message complete |

**Thinking (Ephemeral - NOT persisted):**
| Type | Description |
|------|-------------|
| `THINKING_TEXT_MESSAGE_START` | Thinking begins |
| `THINKING_TEXT_MESSAGE_CONTENT` | Thinking text delta |
| `THINKING_TEXT_MESSAGE_END` | Thinking complete |

**Tool Calls:**
| Type | Description |
|------|-------------|
| `TOOL_CALL_START` | Tool invocation begins |
| `TOOL_CALL_ARGS` | Tool arguments (streaming) |
| `TOOL_CALL_END` | Tool call complete |
| `TOOL_CALL_RESULT` | Tool result returned |

**State Management:**
| Type | Description |
|------|-------------|
| `STATE_SNAPSHOT` | Full state replacement |
| `STATE_DELTA` | JSON Patch (RFC 6902) |
| `ACTIVITY_SNAPSHOT` | Full widget content |
| `ACTIVITY_DELTA` | Widget patch |

**Lifecycle:**
| Type | Description |
|------|-------------|
| `RUN_STARTED` | Run begins |
| `RUN_FINISHED` | Run completes successfully |
| `RUN_ERROR` | Run failed |
| `STEP_STARTED` | Step begins |
| `STEP_FINISHED` | Step complete |

**Other:**
| Type | Description |
|------|-------------|
| `MESSAGES_SNAPSHOT` | Full message history |
| `CUSTOM` | Custom event (ignored by default) |
| `RAW` | Raw event (ignored by default) |

## Parsing SSE Response

```python
import json

text = ""
thinking = ""

for line in response.iter_lines():
    if line.startswith(b"data: "):
        event = json.loads(line[6:])
        event_type = event.get("type")

        if event_type == "TEXT_MESSAGE_CONTENT":
            text += event.get("delta", "")
            print(event.get("delta", ""), end="", flush=True)

        elif event_type == "THINKING_TEXT_MESSAGE_CONTENT":
            # Thinking is ephemeral - visible live, disappears on refresh
            thinking += event.get("delta", "")
            print(f"(thinking) {event.get('delta', '')}", end="", flush=True)

        elif event_type == "RUN_FINISHED":
            print("\n--- Run complete ---")

        elif event_type == "RUN_ERROR":
            print(f"\n--- Error: {event.get('message')} ---")
```

## Known Limitations

1. **Data Loss on Disconnect**: Client disconnect during SSE stream = run events NOT saved to database

2. **Thinking Events Not Persisted**: Live-streamed but filtered from replay

See [architecture.md](architecture.md#known-limitations) for full list.
