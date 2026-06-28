# WebSocket Protocol Reference

The WebSocket interface enables real-time graph execution control and state streaming between the client and server.

---

## Connection

**URL**: `ws://<host>:<port>/ws/graph`

Default: `ws://127.0.0.1:2026/ws/graph`

The server accepts the connection immediately via `await websocket.accept()`. No authentication or subprotocol negotiation is required.

**Source**: `server/src/api/routes/graph.py` (WebSocket handler)  
**Action Router**: `server/src/services/action_router.py`

---

## Message Format

All messages are JSON objects.

### Client → Server

Minimum required field: `action`

```json
{ "action": "<action_name>", ...additional fields }
```

### Server → Client

```json
{
  "type": "<response_type>",
  "message": "<human_readable_message>",
  "data": { ...optional_payload }
}
```

---

## Client Actions

### `fetch`

Request the server's computed React Flow graph data (nodes, edges, layout).

**Request**:
```json
{ "action": "fetch" }
```

**Response** (`type: "graph_data"`):
```json
{
  "type": "graph_data",
  "message": "",
  "data": {
    "nodes": [ /* NodeFlow objects */ ],
    "edges": [ /* EdgeFlow objects */ ],
    "executionSteps": []
  }
}
```

The `data` payload matches the `GraphData` Pydantic model from `server/src/schemas/graph.py`.

**Implementation**: Calls `get_graph_metadata()` in `action_router.py` which runs a BFS hierarchical layout and maps nodes to React Flow format. Back-edges (cycles) are detected and rendered with `smoothstep` type and orange stroke.

---

### `run`

Execute the graph asynchronously.

**Request**:
```json
{ "action": "run" }
```

**Response sequence**:
1. `{ "type": "status", "message": "Execution Started..." }`
2. Zero or more `{ "type": "node_state_update", "nodeId": "...", "data": { ... } }` packets
3. Final node state updates as each node completes

**Implementation**: Calls `executor.execute()` which invokes `graph.ainvoke(state, stream_mode="updates")` in a background asyncio task. `VirtualNode` pre/post hooks fire automatically and forward state packets via `state_update_func`.

---

### `update_state`

Inject a state mutation hook into a specific node. The mutation is merged into the node's input state just before it executes.

**Request**:
```json
{
  "action": "update_state",
  "nodeId": "fix_nodename",
  "state": { "iterations": 5, "status": "approved" }
}
```

**Response**:
```json
{
  "type": "node_state_update",
  "nodeId": "fix_nodename",
  "data": { "input": { "iterations": 5, "status": "approved" } }
}
```

**Implementation**: The hook is stored in `executor._statehooks` and applied in `on_node_pre_executed()` in LIFO order.

---

### `set_breakpoint`

Set a breakpoint on a specific node. Execution will pause before that node runs.

**Request**:
```json
{ "action": "set_breakpoint", "nodeId": "review" }
```

**Response**: The client receives the breakpoint state via subsequent `node_state_update` packets.

**Implementation**: Looks up the `VirtualNode` by name via `virtual_graph[nodeId]` and calls `node.set_breakpoint(True)`. The node's `__call__` method spins with `asyncio.sleep(0.1)` until the breakpoint is cleared.

---

### `remove_breakpoint`

Remove a breakpoint from a specific node.

**Request**:
```json
{ "action": "remove_breakpoint", "nodeId": "review" }
```

**Implementation**: Calls `node.set_breakpoint(False)`, allowing the node to proceed with execution.

---

## Server Response Types

| Type | Description |
|---|---|
| `graph_data` | Full graph metadata response to `fetch` |
| `node_state_update` | Real-time node execution state update |
| `status` | Informational status message (e.g., "Execution Started...") |
| `error` | Error message with details |

### Node State Update Packet

```json
{
  "type": "node_state_update",
  "nodeId": "initialize",
  "data": {
    "input": { "topic": "LangGraph" },
    "output": { "draft": "Initial draft..." },
    "state": { "draft": "Initial draft..." },
    "error": "",
    "hasBreakpoint": false,
    "status": "running"
  }
}
```

Status values: `running`, `success`, `error`

---

## Client Implementation

The frontend WebSocket client is implemented in `client/src/hooks/use-graph-ws.ts`:

- **Auto-reconnect**: Exponential backoff from 2s to 30s
- **Subscription model**: Components subscribe to `graph_data` and `node_state_update` events via `subscribe()` and `subscribeNodeState()`
- **Graceful handling**: Parse errors are logged to `console.warn` without crashing

Key functions exposed by `useGraphWebSocket()`:

| Function | Description |
|---|---|
| `send(action, payload)` | Send a WebSocket action |
| `subscribe(handler)` | Subscribe to `graph_data` events; returns unsubscribe function |
| `subscribeNodeState(handler)` | Subscribe to `node_state_update` events; returns unsubscribe function |
| `connected` | Boolean indicating WebSocket connection state |
| `updateNodeState(nodeId, state)` | Convenience wrapper for `update_state` action |

---

## Error Handling

- **WebSocketDisconnect**: Client closed connection — server prints "WebSocket disconnected" and stops
- **Server exceptions**: Caught in the WebSocket handler; a `type: "error"` response is sent with the exception message
- **Unknown actions**: The router returns `{ "type": "error", "message": "Unknown action type" }`
