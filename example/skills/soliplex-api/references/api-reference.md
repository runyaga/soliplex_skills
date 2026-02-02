# Soliplex API Reference

**Base URL:** `http://127.0.0.1:8000` (configurable)

**URL Structure:** Routers define `/v1/...`, mounted with `/api` prefix.
- Internal router path: `/v1/rooms`
- **Actual URL:** `/api/v1/rooms`

## Authentication

All API endpoints (except health/debug) require OAuth2 authentication.

**Header:** `Authorization: Bearer <token>`

```bash
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/rooms
```

**No-Auth Mode:** Start server with `--no-auth-mode` to bypass (development only).

## Rooms API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/rooms` | List all rooms |
| GET | `/api/v1/rooms/{id}` | Room configuration |
| GET | `/api/v1/rooms/{id}/bg_image` | Room background image |
| GET | `/api/v1/rooms/{id}/mcp_token` | MCP client token (if `allow_mcp: true`) |
| GET | `/api/v1/rooms/{id}/documents` | RAG documents list |
| GET | `/api/v1/rooms/{id}/chunk/{chunk_id}` | Chunk visualization |

### List Rooms

```
GET /api/v1/rooms
Authorization: Bearer <token>
```

Returns:
```json
[
  {
    "id": "gpt-20b",
    "name": "GPT-OSS 20B",
    "description": "Math-capable room",
    "welcome_message": "...",
    "suggestions": ["Calculate factorial of 23", ...]
  }
]
```

### Get Room Details

```
GET /api/v1/rooms/{room_id}
```

Returns detailed room configuration including tools and model.

## AG-UI API (Chat)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/rooms/{id}/agui` | List threads |
| POST | `/api/v1/rooms/{id}/agui` | Create thread + initial run |
| GET | `/api/v1/rooms/{id}/agui/{thread_id}` | Get thread details |
| DELETE | `/api/v1/rooms/{id}/agui/{thread_id}` | Delete thread |
| POST | `/api/v1/rooms/{id}/agui/{thread_id}` | Create new run in thread |
| POST | `/api/v1/rooms/{id}/agui/{thread_id}/meta` | Update thread metadata |
| GET | `/api/v1/rooms/{id}/agui/{thread_id}/{run_id}` | Get run details |
| POST | `/api/v1/rooms/{id}/agui/{thread_id}/{run_id}` | **Execute run (SSE stream)** |
| POST | `.../feedback` | Submit run feedback |

### Step 1: Create Thread/Run

```
POST /api/v1/rooms/{room_id}/agui
Content-Type: application/json
Authorization: Bearer <token>

{
  "thread_id": "unique-thread-id",
  "messages": [
    {"id": "msg-1", "role": "user", "content": "Your message"}
  ]
}
```

Returns:
```json
{
  "thread_id": "...",
  "runs": {
    "<run_id>": { "run_id": "...", ... }
  }
}
```

### Step 2: Execute Run (SSE Stream)

```
POST /api/v1/rooms/{room_id}/agui/{thread_id}/{run_id}
Content-Type: application/json
Accept: text/event-stream
Authorization: Bearer <token>

{
  "threadId": "<thread_id>",
  "runId": "<run_id>",
  "state": {},
  "messages": [
    {"id": "msg-1", "role": "user", "content": "Your message"}
  ],
  "tools": [],
  "context": [],
  "forwardedProps": {}
}
```

## AG-UI Event Types

SSE stream returns 25+ event types across categories: text messages, thinking (ephemeral), tool calls, state management, and lifecycle events.

→ **Full reference:** [ag-ui.md](ag-ui.md) - Complete event type tables, state management, SSE parsing examples

### Multi-Turn Conversations

For multi-turn conversations, you must create a new run for each user message within the same thread:

```
POST /api/v1/rooms/{room_id}/agui/{thread_id}
Content-Type: application/json

{}
```

Returns:
```json
{
  "thread_id": "...",
  "run_id": "<new_run_id>",
  "created": "2026-02-01T..."
}
```

Then execute that run with the full conversation history in the `messages` array.

### Complete Multi-Turn Example

```python
import requests
import json

BASE_URL = "http://127.0.0.1:8003"
ROOM_ID = "simple-todo"

# Step 1: Create initial thread/run
session = requests.post(
    f"{BASE_URL}/api/v1/rooms/{ROOM_ID}/agui",
    json={}
).json()

thread_id = session["thread_id"]
run_id = list(session["runs"].keys())[0]

messages = []

def send_message(user_message: str):
    global run_id

    # Add user message to history
    messages.append({
        "id": f"msg-{len(messages)}",
        "role": "user",
        "content": user_message
    })

    # Execute run
    response = requests.post(
        f"{BASE_URL}/api/v1/rooms/{ROOM_ID}/agui/{thread_id}/{run_id}",
        json={
            "threadId": thread_id,
            "runId": run_id,
            "state": {},
            "messages": messages,
            "tools": [],
            "context": [],
            "forwardedProps": {}
        },
        stream=True
    )

    # Parse SSE response
    assistant_text = ""
    for line in response.iter_lines():
        if line.startswith(b"data: "):
            event = json.loads(line[6:])
            if event.get("type") == "TEXT_MESSAGE_CONTENT":
                assistant_text += event.get("delta", "")

    # Add assistant response to history
    messages.append({
        "id": f"msg-{len(messages)}",
        "role": "assistant",
        "content": assistant_text
    })

    # Create new run for next message
    new_run = requests.post(
        f"{BASE_URL}/api/v1/rooms/{ROOM_ID}/agui/{thread_id}",
        json={}
    ).json()
    run_id = new_run["run_id"]

    return assistant_text

# Usage
send_message("Add a task to buy groceries")
send_message("Show me my todo list")
send_message("Mark the groceries task as done")
```

### Key Points

1. **Two endpoints per message**: First create a run, then execute it
2. **Thread persists**: Use the same `thread_id` for the entire conversation
3. **Run is one-time**: Each run can only be executed once
4. **Full history required**: Always send the complete `messages` array
5. **SSE streaming**: Response is a Server-Sent Events stream

## Parsing SSE Response

→ **Full reference:** [ag-ui.md](ag-ui.md#parsing-sse-response) - Complete SSE parsing patterns with thinking event handling

## Completions API (Ephemeral)

OpenAI-compatible completions endpoint. **NOT persisted** - no threads/runs/events saved.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/chat/completions` | List completions |
| GET | `/api/v1/chat/completions/{id}` | Get completion details |
| POST | `/api/v1/chat/completions/{id}` | Execute completion (SSE) |

## Installation API (Admin Required)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/installation` | Admin | Full installation config |
| GET | `/api/v1/installation/versions` | Admin | pip list output |
| GET | `/api/v1/installation/providers` | Admin | Available LLM providers |
| GET | `/api/v1/installation/git_metadata` | **User** | Git info (no admin required) |

## Message Data Models

Messages in AG-UI are polymorphic:

**AssistantMessage:**
```json
{
  "id": "msg-123",
  "role": "assistant",
  "content": "Here's the result...",
  "tool_calls": [
    {"id": "tc-1", "type": "function", "function": {"name": "search", "arguments": "{...}"}}
  ]
}
```

**ToolMessage:**
```json
{
  "id": "msg-124",
  "role": "tool",
  "tool_call_id": "tc-1",
  "content": "{\"results\": [...]}"
}
```

**ActivityMessage:**
```json
{
  "id": "msg-125",
  "role": "assistant",
  "activity_type": "citations",
  "content": {"documents": [...], "chunks": [...]}
}
```

## Known Limitations

1. **Data Loss on Disconnect**: Client disconnect during SSE = run events NOT saved
2. **Blocking Visualization**: `/chunk/{id}` blocks event loop (heavy PIL/Base64)
3. **Ephemeral Completions**: `/v1/chat/completions` has no persistence
4. **Thinking Not Persisted**: Live-streamed but filtered from replay

## Debug Endpoints (No Auth)

⚠️ **Warning**: These endpoints have NO authentication.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/ssetest` | Test SSE streaming |
| WS | `/wstest` | Test WebSocket |
