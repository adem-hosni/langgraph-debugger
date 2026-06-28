# Server Debugger Internals

This document provides an in-depth technical explanation of the debugger engine components: `VirtualNode`, `VirtualGraph`, `Executor`, `ConditionalNode`, and the action router.

---

## VirtualNode (`server/src/debugger/virtual_node.py`)

### Purpose
Wraps each node in a LangGraph with instrumentation hooks that allow the debugger to observe and control execution.

### Class Structure

```python
class VirtualNode:
    def __init__(self, name, func, on_pre_execute, on_post_execute,
                 next_node=None, breakpoint=False):
```

| Attribute | Type | Description |
|---|---|---|
| `original_name` | str | Original node name from the graph |
| `name` | str | Public name used in the StateGraph |
| `func` | RunnableCallable | The wrapped node function |
| `next` | VirtualNode or None | Linked list pointer to the next node |
| `breakpoint` | bool | Whether execution should pause before this node |
| `input_state` | dict | State received before execution |
| `output_state` | dict | State produced after execution |
| `error` | str | Exception traceback if the node failed |
| `on_pre_execute` | callable | Hook invoked before node execution |
| `on_post_execute` | callable | Hook invoked after node execution |

### Execution Flow (`__call__`)

```
1. Store args[0] as input_state
2. If breakpoint is True:
     Loop asyncio.sleep(0.1) until breakpoint is False
3. Call on_pre_execute(self)  ← Executor sends "running" packet
4. Execute self.func(input_state)
5. If exception: store traceback in self.error
6. Store result as output_state
7. Call on_post_execute(self) ← Executor sends "success"/"error" packet
8. Return result
```

### Breakpoint Mechanism
The breakpoint is a **cooperative** spin-loop. When `breakpoint=True`, the `__call__` method enters a `while self.breakpoint: await asyncio.sleep(0.1)` loop. This yields control to the event loop every 100ms until the breakpoint is cleared by a `remove_breakpoint` action. This approach is simple and effective for local debugging but does not support hard real-time constraints.

---

## VirtualGraph (`server/src/debugger/virtual_graph.py`)

### Purpose
Transforms a `CompiledStateGraph` into an instrumented version where every node is wrapped in a `VirtualNode`. This is the compiler that bridges the original graph structure with the debugger's linked-list execution model.

### Key Methods

#### `build_virtual_nodes(nodes)`
Creates `VirtualNode` instances for each node in the graph's node map. Handles subgraph recursion — if a node contains a nested `CompiledStateGraph`, it recursively unwraps it.

#### `compile_node(node_id, node)`
Returns either:
- A single `VirtualNode` for regular nodes
- A list of `VirtualNode` instances for subgraph nodes

Extracts the runnable function from `node.data.func` (for `Node` objects) or uses the node directly.

#### `link_virtual_edges()`
Chains `VirtualNode` instances together following the graph's edge structure:

1. Iterates all edges from `graph.get_graph().edges`
2. For forward edges: sets `source_node.next = target_node`
3. For conditional edges: creates a `ConditionalNode` that evaluates the condition function at runtime
4. For back-edges (cycles): links back to an earlier node, creating a loop

#### `compile_graph(state)`
Builds a new `StateGraph` from the virtual node chain:
1. Calls `link_virtual_edges()` to get the start node
2. Creates a fresh `StateGraph(state)`
3. Walks the linked list, adding each node to the builder
4. Adds edges between consecutive nodes
5. Compiles and returns the new `CompiledStateGraph`

### Node Lookup (`__getitem__`)
Two forms:
- `vg["nodeName"]` — Searches the default linked list (`self`)
- `vg["nodeName", nodes_list]` — Searches an explicit list

### Iteration (`__iter__`)
Walks the linked list from `start_node` through `node.next` pointers.

---

## ConditionalNode (`server/src/debugger/conditional_node.py`)

### Purpose
Extends `VirtualNode` to handle conditional routing (when a node has multiple possible successors based on state).

### How It Works

```python
class ConditionalNode(VirtualNode):
    def __init__(self, name, func, condition, condition_node,
                 on_pre_execute, on_post_execute, virtual_graph, virtual_nodes):
```

- `condition` — Dict mapping output values → target node names (e.g., `{"approved": "finalize", "rejected": "fix_errors"}`)
- `condition_node` — The source node whose output determines routing
- `_virtual_graph` — Reference to the containing VirtualGraph for node lookups

### Dynamic `next` Property

```python
@property
def next(self):
    node_result = self._virtual_graph[self.condition_node, self.virtual_nodes].output_state
    for k, v in self.condition.items():
        if node_result == v:
            return self._virtual_graph[k, self.virtual_nodes]
    return self._next
```

At runtime, it reads the condition node's `output_state` and matches it against the condition dict to determine the actual next node. This enables dynamic routing including cycles (e.g., a review node that routes back to `fix_errors` until approved).

---

## Executor (`server/src/debugger/executor.py`)

### Purpose
Orchestrates the execution lifecycle, managing state hooks and forwarding real-time updates to the frontend.

### Key Methods

#### `set_virtual_graph(virtual_graph)`
Attaches a `VirtualGraph` and recompiles the runnable graph:
1. Stores the virtual graph reference
2. Calls `_compile_graph()` which:
   a. Populates virtual nodes from `self.graph.builder.nodes`
   b. Compiles a new graph from the virtual representation

#### `execute(state)`
Launches async graph execution:
```python
asyncio.create_task(self.graph.ainvoke(state, stream_mode="updates"))
```
Runs in a detached task so the WebSocket handler can continue processing.

#### `insert_state_hook(hook)`
Stores a `StateHook` (node ID + state updates) in `self._statehooks`. Multiple hooks can target the same node; they are applied in LIFO order.

#### `on_node_pre_executed(node)`
Called by VirtualNode before execution:
1. Iterates `_statehooks` in reverse (LIFO)
2. If a hook matches `node.name`, merges hook updates into `node.input_state`
3. Sends a status packet with `status: "running"`

#### `on_node_post_executed(node)`
Called by VirtualNode after execution:
1. Sends a status packet with `status: "success"` or `status: "error"` (based on `node.error`)

### State Packet Format

```python
{
    "nodeId": node.name,
    "state": node.output_state,
    "input": node.input_state,
    "output": node.output_state,
    "error": node.error,
    "hasBreakpoint": node.breakpoint,
    "status": "running" | "success" | "error"
}
```

---

## Action Router (`server/src/services/action_router.py`)

### Purpose
Dispatches incoming WebSocket messages to the appropriate handler.

### Action Dispatch Table

| Action | Handler | Description |
|---|---|---|
| `fetch` | `get_graph_metadata()` | Returns React Flow-compatible graph layout |
| `run` | `executor.execute()` | Starts async graph execution |
| `update_state` | `executor.insert_state_hook()` | Injects state mutation for a node |
| `set_breakpoint` | `virtual_graph[node].set_breakpoint(True)` | Pauses execution before the node |
| `remove_breakpoint` | `virtual_graph[node].set_breakpoint(False)` | Resumes execution at the node |

### get_graph_metadata() — Layout Engine

The layout engine in `action_router.py` converts the LangGraph structure to React Flow format:

1. **BFS Traversal**: Assigns depth levels starting from `__start__` at level 0
2. **Hierarchical Positioning**:
   - X_CENTER = 400, X_SPACING = 250, Y_SPACING = 130, START_Y = 30
   - Nodes at each level are centered horizontally
3. **Node Type Mapping**:
   - `__start__` → `"start"` (green)
   - `__end__` → `"end"` (gray)
   - Nodes containing "tool" → `"tool"` (amber)
   - All others → `"agent"` (blue)
4. **Edge Styling**:
   - Back-edges (target level ≤ source level) → `smoothstep` type + orange stroke
   - START edges → animated green stroke
   - Normal edges → gray bezier
5. **Serialization**: Returns `GraphData.model_dump(mode="json", by_alias=True)` for camelCase output

---

## Execution Lifecycle Summary

```
1. Client connects via WebSocket
2. initialize_context() creates:
   - Executor (with state_update_func bound to websocket.send)
   - VirtualGraph (with executor's pre/post hooks)
   - Wires executor → virtual_graph → compiled graph
3. Client sends "fetch" → get_graph_metadata() returns layout
4. Client sends "run" → executor.execute() launches graph.ainvoke()
5. VirtualNode.__call__() fires for each node:
   a. Breakpoint check (spin if set)
   b. on_pre_execute → state hook merge → "running" packet
   c. Node function executes
   d. on_post_execute → "success"/"error" packet
6. Client receives node_state_update events in real-time
```
