# Usage Guide

## Interface Overview

The application has two main views, switchable via the top navigation tabs:

- **Chat View**: A full-featured AI chat interface with multi-session management
- **Graph Debugger**: An interactive visual debugger for LangGraph execution graphs

---

## Chat View

### Starting a Conversation
1. Click **New Chat** in the sidebar (or use the `+` button)
2. Select an AI model from the dropdown in the top-right
3. Optionally change the **chat mode** (Default, Deep Thinking, Research, Creative, Concise)
4. Type your message in the input area and press Enter (or click the send button)

### File Attachments
- Drag and drop files onto the input area
- Supported types: code (`.js`, `.py`, `.ts`, etc.), data (`.csv`, `.json`), images (`.png`, `.jpg`), documents
- Attached files appear as badges above the input; click the `×` to remove

### Managing Sessions
- **Session sidebar**: Lists all conversations grouped by date
- **Click a session**: Switch to that conversation
- **New Chat**: Creates a fresh session
- **Theme toggle**: Bottom-left sidebar button cycles through light/dark/system

### Settings
Click the gear icon in the sidebar to open the Settings modal, where you can configure the **System Instructions** prompt that shapes AI behavior.

---

## Graph Debugger

### Loading the Graph
1. Switch to the **Graph Debugger** tab
2. The client connects via WebSocket to the backend
3. The graph renders as a React Flow diagram with hierarchical layout
4. Each node is color-coded:
   - **Green border**: Successfully executed
   - **Blue border + pulse**: Currently running
   - **Red border**: Error state
   - **Gray/opaque**: Idle (not yet executed)

### Execution Controls

The control bar appears at the bottom center of the graph view:

| Control | Shortcut | Action |
|---|---|---|
| Reset | `R` | Reset all execution state |
| Step Back | `←` | Move to the previous execution step |
| Play/Pause | `Space` | Start or pause auto-execution |
| Step Forward | `→` | Advance to the next execution step |
| Breakpoint count | — | Shows active breakpoints; click to clear all |

### Breakpoints

- Click the small circle button on the left side of any agent or tool node to toggle a breakpoint
- When execution reaches a node with a breakpoint, it pauses automatically
- A toast notification shows which node triggered the pause
- Resume by clicking Play or clearing the breakpoint

### State Inspector

Click any node to open the **State Inspector** side panel:

- **Input tab**: Shows the node's input state (editable for agent/tool nodes)
- **Output tab**: Shows the output produced by the node
- **Error display**: If the node failed, a red error section shows the full stack trace
- **Rerun button**: Re-execute the individual node
- **Edit state**: Click the pencil icon to modify the node's state in JSON, then click Save

### Keyboard Shortcuts

| Key | Action |
|---|---|
| `Space` | Play / Pause |
| `←` | Step Back |
| `→` | Step Forward |
| `R` | Reset |
| `Escape` | Close State Inspector |

### Node Types

| Type | Icon | Description |
|---|---|---|
| START | Play (green) | Graph entry point |
| Agent | Bot (blue) | AI/LLM node that processes state |
| Tool | Wrench (amber) | External tool node (search, code, etc.) |
| END | Square (gray) | Graph terminal node |

### Cycle Detection

If the graph contains cyclical edges (e.g., a review loop that iterates until approval), the debugger renders them with:
- **Smoothstep edge routing** to avoid overlapping nodes
- **Orange stroke color** to visually distinguish back-edges

---

## Common Workflows

### Debugging a Failing Node
1. Run the graph (click Play)
2. When a node fails, the inspector auto-opens with the error stack trace
3. Inspect the input that caused the failure
4. Edit the state and rerun the node
5. Continue execution from the corrected state

### Observing a Cyclical Workflow
1. The demo graph (`dev.py`) implements a writing workflow with review cycles
2. It intentionally rejects the draft twice before approving
3. Watch the orange back-edge highlight as execution loops between `review` and `fix_errors`
4. The iterations counter in the state shows progress through the cycle

### Setting Up a Custom Graph
1. Define your LangGraph state schema and nodes (see `server/src/dev.py` for an example)
2. Compile your graph with `builder.compile()`
3. Pass it to `create_app()` from `server/src/app.py`
4. Start the server with `python -m src.your_module`
