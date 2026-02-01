# Soliplex API Reference

Base URL: `http://127.0.0.1:8002` (configurable via SOLIPLEX_URL)

## Health Check

```
GET /api/ok
```

Returns `OK` if server is running.

## List Rooms

```
GET /api/v1/rooms
```

Returns array of room objects:

```json
[
  {
    "id": "gpt-20b",
    "name": "GPT-OSS 20B",
    "description": "Math-capable room with gpt-oss:20b model",
    "welcome_message": "...",
    "suggestions": ["Calculate factorial of 23", ...]
  }
]
```

## Get Room Details

```
GET /api/v1/rooms/{room_id}
```

Returns detailed room configuration including tools and model.

## AG-UI Protocol (Chat)

Soliplex uses AG-UI protocol which requires two steps:

### Step 1: Create Thread/Run

```
POST /api/v1/rooms/{room_id}/agui
Content-Type: application/json

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

Returns SSE stream with events:
- `TEXT_MESSAGE_CONTENT` - Assistant response text (delta field)
- `TOOL_CALL_START/END` - Tool invocations
- `RUN_FINISHED` - Completion signal

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

```python
for line in response.iter_lines():
    if line.startswith("data: "):
        event = json.loads(line[6:])
        if event.get("type") == "TEXT_MESSAGE_CONTENT":
            text += event.get("delta", "")
```
