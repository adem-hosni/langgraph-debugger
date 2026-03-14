# Architecture

This project is split into two primary components:

- Client (frontend): a TypeScript + React single-page application that
  provides the debugging UI, including websocket-based controls and a
  visual graph inspector. See `client/` for the source.
- Server (backend): a Python ASGI application that hosts the graph
  execution engine and debugger hooks. See `server/` for the source.

Core Concepts

- CompiledStateGraph: the runtime representation of a state graph that
  can be asynchronously invoked.
- VirtualNode / VirtualGraph: debugger wrappers around runtime nodes to
  add pre/post hooks, breakpoint semantics, and a representation the
  UI can observe.
- Executor: ties a VirtualGraph to a CompiledStateGraph and emits state
  updates to the client.

Data flow (simplified)

1. Client requests execution or sets breakpoints via websocket.
2. Server's Executor attaches hooks and compiles a VirtualGraph.
3. Executor triggers the compiled graph; VirtualNodes call pre/post
   callbacks that forward JSON packets to the client.
4. Client updates the UI (state inspector, node status, logs) as packets
   arrive.

Files of interest

- `server/src/debugger/virtual_node.py` — runtime wrapper for node
  execution.
- `server/src/debugger/virtual_graph.py` — builds virtual nodes and
  compiles them into an executable graph.
- `server/src/debugger/executor.py` — orchestrates execution and
  forwards state packets to the frontend.
