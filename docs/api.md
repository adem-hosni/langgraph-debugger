# REST API Reference

Base URL: `http://<host>:<port>` (default `http://127.0.0.1:2026`)

Authentication: None by default (local development only).

Content-Type: `application/json` for all requests and responses.

---

## Chat

### POST /chat/send

Send a user message to the LangGraph and persist the conversation.

**Source**: `server/src/api/routes/chat.py`

**Request Body** (`SendMessageRequest`):

```json
{
  "sessionId": "string",
  "content": "string",
  "attachments": [
    { "name": "file.js", "type": "code", "size": "2.4 KB" }
  ],
  "model": "gpt-4o",
  "mode": "default"
}
```

| Field | Type | Description |
|---|---|---|
| `sessionId` | string | Chat session identifier; creates new session if missing |
| `content` | string | User message text |
| `attachments` | Attachment[] | Optional file attachments |
| `model` | string | AI model alias (aliased from `model_name`) |
| `mode` | enum | `default`, `thinking`, `research`, `creative`, `concise` |

**Response** (`SendMessageResponse`):

```json
{
  "userMessage": { "id": "...", "role": "user", "content": "...", "timestamp": "2:34 PM" },
  "assistantMessage": { "id": "...", "role": "assistant", "content": "...", "timestamp": "2:34 PM" },
  "updatedSessionTitle": "Analyze index.js code..."
}
```

**Status Codes**: `200 OK` on success, `500 Internal Server Error` on graph execution failure.

---

## History

### GET /history/threads

Returns all chat sessions with their messages, most recent first.

**Source**: `server/src/api/routes/history.py`

**Response**: Array of session objects:

```json
[
  {
    "id": "uuid",
    "title": "Analyze code",
    "date": "2025-06-28",
    "messages": [
      { "id": "...", "role": "user", "content": "...", "timestamp": "..." },
      { "id": "...", "role": "assistant", "content": "...", "timestamp": "..." }
    ]
  }
]
```

### GET /history/{thread_id}

Retrieve the full checkpoint history for a specific thread.

**Response**:

```json
{
  "threadId": "uuid",
  "totalCheckpoints": 5,
  "history": [
    {
      "checkpointId": "uuid",
      "values": { "inputText": "hello", "result": "Hi there!" },
      "next": ["agent_node"],
      "createdAt": null
    }
  ]
}
```

Requires a graph with a checkpointer configured.

### GET /history/{thread_id}/latest

Fetch only the most recent state snapshot.

**Response**:

```json
{
  "threadId": "uuid",
  "values": { "inputText": "hello", "result": "Hi there!" },
  "next": []
}
```

Returns `400` if the graph lacks a checkpointer.

---

## AI Models

### POST /models/add

Create a new custom AI model entry.

**Source**: `server/src/api/routes/aimodels.py`

**Request Body**:

```json
{ "label": "Llama 3.1 70B" }
```

**Response**: The created `AIModel` (without DB `id`):

```json
{ "label": "Llama 3.1 70B", "value": "Llama 3 1 70B", "custom": true }
```

### GET /models/fetch

Fetch all AI models.

**Response**:

```json
[
  { "label": "GPT-4o", "value": "gpt-4o", "custom": false },
  { "label": "Claude 3.5 Sonnet", "value": "claude-3.5-sonnet", "custom": false },
  { "label": "Llama 3.1 70B", "value": "Llama 3 1 70B", "custom": true }
]
```

### DELETE /models/delete/{label}

Delete a model by label.

**Response**: `200 OK` with `{ "detail": "Model deleted" }`

**Errors**: `404 Not Found` if label doesn't exist.

---

## Graph Metadata

### GET /ws/info

Return a JSON-serializable representation of the compiled graph, suitable for React Flow rendering. This is an HTTP endpoint that returns the same data as the WebSocket `fetch` action.

**Source**: `server/src/api/routes/graph.py`

**Response** (`GraphData`):

```json
{
  "nodes": [
    {
      "id": "initialize",
      "type": "graphNode",
      "position": { "x": 400, "y": 30 },
      "data": {
        "label": "Initialize",
        "type": "agent",
        "status": "idle",
        "input": {},
        "output": {},
        "state": {},
        "error": null,
        "hasBreakpoint": false
      }
    }
  ],
  "edges": [
    {
      "id": "e-initialize-draft",
      "source": "initialize",
      "target": "draft",
      "animated": true,
      "style": { "stroke": "hsl(142, 71%, 45%)" }
    }
  ],
  "executionSteps": []
}
```

---

## Example cURL Requests

```bash
# Send a chat message
curl -X POST http://127.0.0.1:2026/chat/send \
  -H "Content-Type: application/json" \
  -d '{"sessionId":"abc","content":"Hello","model":"gpt-4o","mode":"default"}'

# Fetch all sessions
curl http://127.0.0.1:2026/history/threads

# Fetch graph metadata
curl http://127.0.0.1:2026/ws/info

# Fetch all AI models
curl http://127.0.0.1:2026/models/fetch

# Add a custom model
curl -X POST http://127.0.0.1:2026/models/add \
  -H "Content-Type: application/json" \
  -d '{"label":"My Custom Model"}'

# Delete a model
curl -X DELETE http://127.0.0.1:2026/models/delete/My%20Custom%20Model
```

---

## Error Responses

| Code | Meaning |
|---|---|
| `400 Bad Request` | Missing checkpointer, invalid parameters |
| `404 Not Found` | Model label not found |
| `500 Internal Server Error` | Graph execution failure, database errors |

Error bodies follow FastAPI's default format:

```json
{ "detail": "Error executing AI Graph." }
```
