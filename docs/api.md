**API Reference**

This document describes the HTTP REST API exposed by the LangGraph Debugger backend and the available endpoints, request/response schemas, and error behavior. The server code that implements these routes can be found in the repository under the `server/src/api/routes` package.

- **Source:** [server/src/api/routes/__init__.py](server/src/api/routes/__init__.py#L1-L50)

**Base URL**: `http://<host>:<port>` (default `http://127.0.0.1:8000`)

**Authentication**: None by default. Endpoints are intentionally simple for local development. If you add auth, update the API accordingly.

**Content-Type**: JSON for all request and response bodies unless otherwise noted.

**Endpoints**

**Chat**
- **POST** `/chat/send` — Send a user message to the LangGraph and receive the AI assistant reply.
  - **Source:** [server/src/api/routes/chat.py](server/src/api/routes/chat.py#L1-L220)
  - **Request model**: `SendMessageRequest` (see [server/src/schemas/chat.py](server/src/schemas/chat.py#L1-L220))
    - **Fields**:
      - `sessionId` (string): Identifier for the chat session. If missing in DB, server will create a new session.
      - `content` (string): The user's message text.
      - `attachments` (optional list): Attachments array (see `Attachment`).
      - `model` (string): Alias for `model_name` — which AI model to run.
      - `mode` (enum): Chat mode; one of `default`, `thinking`, `research`, `creative`, `concise`.
    - **Example request**:
```json
{
  "sessionId": "8a6c...",
  "content": "Summarize the repository",
  "model": "gpt-4o-mini",
  "mode": "default"
}
```
  - **Response model**: `SendMessageResponse` (see [server/src/schemas/chat.py](server/src/schemas/chat.py#L1-L220))
    - `userMessage`: typed `ChatMessage` for the user's message
    - `assistantMessage`: typed `ChatMessage` for the assistant reply
    - `updatedSessionTitle`: string|null — when a new session is created, a short title may be returned
  - **Success codes**: `200 OK` with full typed JSON body.
  - **Errors**: `500 Internal Server Error` when graph execution fails. Implementation raises `HTTPException(status_code=500, detail="Error executing AI Graph.")` on errors.

**Run History**
- **GET** `/history/threads` — Returns all chat sessions and their messages (most-recent first).
  - **Source:** [server/src/api/routes/history.py](server/src/api/routes/history.py#L1-L200)
  - **Response**: JSON array of session objects:
    - `id`: string session id
    - `title`: string session title
    - `date`: string date in `YYYY-MM-DD`
    - `messages`: array of typed `ChatMessage` objects (user and assistant serialized)
  - **Errors**: `500` on DB issues.

- **GET** `/history/{thread_id}` — Retrieve entire state history for a specific thread (full checkpoints).
  - **Path parameter**: `thread_id` (string)
  - **Response**: object with `thread_id`, `total_checkpoints` and `history` array where each entry contains `checkpoint_id`, `values`, `next`, and optional `created_at`.
  - **Notes**: This uses the LangGraph `get_state_history` generator. The graph must have a checkpointer configured for meaningful history.

- **GET** `/history/{thread_id}/latest` — Retrieve the latest state snapshot for the thread.
  - **Response**: `{ "thread_id": "...", "values": {...}, "next": [...] }`.
  - **Errors**: `400` if the graph lacks a checkpointer; `500` on other failures.

**AI Models**
- **POST** `/models/add` — Create a new custom AI model entry.
  - **Request body**: JSON object containing at least `label` (string).
  - **Response**: The created `AIModel` serialized excluding DB internal `id`.
  - **Source:** [server/src/api/routes/aimodels.py](server/src/api/routes/aimodels.py#L1-L200)

- **GET** `/models/fetch` — Fetch all AI models.
  - **Response**: Array of `AIModel` objects: `{ value, label, custom }`.

- **DELETE** `/models/delete/{label}` — Delete a model by label.
  - **Path parameter**: `label` (string)
  - **Success**: `200` with `{"detail": "Model deleted"}`
  - **Errors**: `404` when label not found; `500` for DB issues.

**Graph Metadata (HTTP)**
- **GET** `/ws/info` — Return a JSON-serializable representation of the compiled graph suitable for the React Flow UI.
  - **Source:** [server/src/api/routes/graph.py](server/src/api/routes/graph.py#L1-L200)
  - **Response model**: `GraphData` (see [server/src/schemas/graph.py](server/src/schemas/graph.py#L1-L200))
    - `nodes`: list of `NodeFlow` items describing each node (id, type, position, data)
    - `edges`: list of `EdgeFlow` items describing the graph connections
    - `executionSteps`: array of `ExecutionStep` entries describing per-node execution state
  - **Example response**: The returned objects follow React Flow structures and are camelCased by Pydantic's `CamelBaseModel`.

**Models & Database**
- The DB models and serializable fields are implemented in [server/src/db/models.py](server/src/db/models.py#L1-L200). Key table mappings:
  - `sessions` (SessionRecord): `id`, `title`, `date`, `messages` relationship
  - `human_messages` (HumanMessageRecord): `id`, `session_id`, `content`, `timestamp`, `attachments`, `response`
  - `ai_messages` (AIMessageRecord): `id`, `human_message_id`, `content`, `thinking`, `model`, `mode`, `timestamp`, `tool_calls`

**Common Error Patterns**
- `500 Internal Server Error`: generic failure (graph execution, DB errors). Routes raise `HTTPException(status_code=500, detail=...)` with a human-readable message.
- `404 Not Found`: used by the models delete endpoint when a label isn't present.

**Example cURL requests**
- Send a message to the graph:
```bash
curl -X POST http://127.0.0.1:8000/chat/send \
  -H "Content-Type: application/json" \
  -d '{"sessionId":"abc","content":"Hello","model":"gpt-4o-mini","mode":"default"}'
```

- Fetch graph metadata (HTTP):
```bash
curl http://127.0.0.1:8000/ws/info
```

**Notes & Extension Points**
- The project uses Pydantic models in `server/src/schemas` for request/response typing — if you update schemas, the docs should be updated accordingly.
- The chat endpoint persists messages to SQLite by default (see `server/src/db/session.py` and `server/src/db/models.py`).
