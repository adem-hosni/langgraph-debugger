# Architecture

## Overview

LangGraph Debugger is a two-component system:

- **Server** (`server/`): A Python FastAPI ASGI application that hosts the LangGraph execution engine, debugger wrappers, REST API, WebSocket endpoint, and SQLite database.
- **Client** (`client/`): A React + TypeScript single-page application that provides the chat interface and interactive graph debugger UI.

Communication between the two occurs over HTTP (REST) for data queries and WebSocket for real-time graph execution streaming.

---

## Core Concepts

### CompiledStateGraph
The runtime representation of a LangGraph state graph that can be asynchronously invoked. The server receives a pre-compiled `CompiledStateGraph` from the user's application code and wraps it with debugger instrumentation.

### VirtualNode
A lightweight wrapper around each graph node's runnable function. It adds:
- **Pre-execution hook**: Called before the node runs; used to inject state mutations and emit status packets.
- **Post-execution hook**: Called after the node completes; emits the result or error status.
- **Breakpoint support**: When enabled, the node spins in a cooperative loop until the breakpoint is cleared.

### VirtualGraph
A compiler that takes a `CompiledStateGraph` and produces a new instrumented graph where every node is wrapped in a `VirtualNode`. It preserves the original graph's edge structure, including conditional edges (via `ConditionalNode`).

### Executor
Orchestrates execution of the virtual graph. It manages:
- State hooks (user-injected mutations applied before a node runs)
- Pre/post execution callbacks that forward JSON packets to the frontend
- Async graph invocation with streaming updates

### Action Router
The WebSocket message dispatcher (`action_router.py`) maps incoming action strings (`fetch`, `run`, `update_state`, `set_breakpoint`, `remove_breakpoint`) to handler logic.

---

## Data Flow

### Graph Debugger Flow

```
1. Client connects to ws://127.0.0.1:2026/ws/graph
2. Client sends { "action": "fetch" }
3. Server computes graph metadata (BFS layout, node/edge mapping)
4. Server returns { "type": "graph_data", "data": { nodes, edges, executionSteps } }
5. Client renders React Flow diagram
6. User clicks Play → client sends { "action": "run" }
7. Executor invokes graph.ainvoke() with streaming
8. VirtualNode pre/post hooks fire:
   a. on_node_pre_executed → sends { "type": "node_state_update", status: "running" }
   b. Node function executes
   c. on_node_post_executed → sends { "type": "node_state_update", status: "success"|"error" }
9. Client updates node colors and state inspector in real-time
```

### Chat Flow

```
1. User types a message and clicks send
2. Client POSTs to /chat/send with { sessionId, content, model, mode }
3. Server:
   a. Creates/retrieves session in SQLite
   b. Invokes graph.ainvoke() with input_text
   c. Persists user message and AI response to database
   d. Returns { userMessage, assistantMessage, updatedSessionTitle }
4. Client appends messages to the active session
```

---

## Component Responsibilities

### Server Packages

| Package | Responsibility |
|---|---|
| `api/routes/` | HTTP and WebSocket route handlers |
| `core/` | Application configuration (Pydantic Settings) |
| `db/` | SQLAlchemy engine, session factory, ORM models |
| `debugger/` | VirtualNode, VirtualGraph, Executor, ConditionalNode |
| `schemas/` | Pydantic request/response models with camelCase aliasing |
| `services/` | Business logic (WebSocket action routing, graph metadata) |

### Client Packages

| Package | Responsibility |
|---|---|
| `components/chat/` | Chat UI (input, messages, sidebar, selectors, modals) |
| `components/graph/` | Graph debugger UI (flow, nodes, controls, inspector) |
| `components/ui/` | Reusable shadcn/ui primitives (buttons, dialogs, selects, etc.) |
| `hooks/` | React hooks for state management and side effects |
| `lib/` | API client, mock data, type definitions, utilities |
| `pages/` | Top-level page components (Index, NotFound) |

---

## Technology Choices

| Decision | Rationale |
|---|---|
| FastAPI over Flask | Native async support, WebSocket support, auto-generated OpenAPI |
| WebSocket over SSE | Bidirectional, lower latency for execution control |
| React Flow over D3 | Purpose-built for directed graphs, built-in controls and minimap |
| SQLite over PostgreSQL | Zero-config, file-based, sufficient for local development |
| Context over Redux | Simpler state management for this scope; GraphWsContext for WebSocket |
| Mock API fallback | Enables frontend development without the backend running |
