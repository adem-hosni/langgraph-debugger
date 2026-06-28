# Codebase Overview

This document provides a file-by-file walkthrough of every source file in the project.

---

## Server (`server/src/`)

### `app.py` — Application Factory

- `create_app(graph, initial_graph_state, graph_state_schema)` — FastAPI factory that injects the compiled LangGraph into `app.state`
- Configures CORS middleware from `settings.BACKEND_CORS_ORIGINS`
- Mounts all route routers with their prefixes
- `lifespan` context manager: creates database tables on startup via `Base.metadata.create_all(bind=engine)`
- `serve(app, host, port, reload)` — Uvicorn launcher utility

### `dev.py` — Demo Graph

- Defines a **writing workflow** `StateGraph` with `ComplexState` schema
- Nodes: `initialize_research`, `draft_content`, `review_content`, `fix_errors`, `finalize`
- Conditional routing: `route_review` returns `"finalize_cond"` when approved (after 2 rejections), otherwise `"fix_errors"`
- Cycle: `fix_nodename → review` creates a back-edge for iteration
- Starts the server on port **2026** with hot-reload when run directly

### `api/routes/__init__.py` — Route Registry

- Imports all route modules and pairs each `APIRouter` with its `prefix`
- Registered routes: `history` (`/history`), `chat` (`/chat`), `graph` (`/ws`), `aimodels` (`/models`)

### `api/routes/chat.py` — Chat Endpoint

- **POST /chat/send** — Main chat message handler
- Creates new `SessionRecord` if `sessionId` doesn't exist in DB
- Generates session title from first 30 characters of the message
- Calls `graph.ainvoke(graph_input, config)` with `thread_id` set to `sessionId`
- Persists `HumanMessageRecord` and `AIMessageRecord` to SQLite
- Returns `SendMessageResponse` with user and assistant messages

### `api/routes/graph.py` — WebSocket + Graph Metadata

- **WebSocket /ws/graph** — Real-time graph control endpoint
  - Accepts connection, initializes context (graph, executor, virtual graph)
  - Loops receiving JSON actions, delegates to `route_action()`
  - Handles `WebSocketDisconnect` gracefully
- **initialize_context()** — Creates an `Executor` and `VirtualGraph`, wires them together
  - The executor's `state_update_func` sends JSON packets over the WebSocket

### `api/routes/history.py` — History Endpoints

- **GET /history/threads** — Lists all sessions with their messages, ordered by date descending
  - Uses `selectinload` to eagerly load messages and AI responses
  - Serializes each session with `role` field added ("user"/"assistant")
- **GET /history/{thread_id}** — Full checkpoint history via `graph.get_state_history()`
- **GET /history/{thread_id}/latest** — Latest state snapshot via `graph.get_state()`

### `api/routes/aimodels.py` — Model Management

- **POST /models/add** — Creates a new `AIModel` from JSON body with `label`
  - Auto-generates `value` by replacing dashes and titling
  - Marks model as `custom=True`
- **GET /models/fetch** — Returns all AI models
- **DELETE /models/delete/{label}** — Deletes a model by label (404 if not found)

### `core/config.py` — Settings

- `Settings` class extending `pydantic_settings.BaseSettings`
- Fields: `PROJECT_NAME`, `DESCRIPTION`, `VERSION`, `API_V1_STR`, `BACKEND_CORS_ORIGINS`, `DEBUG`, `SQLALCHEMY_DATABASE_URL`
- Instance `settings` exported for use across the app
- Overridable via environment variables

### `db/models.py` — SQLAlchemy ORM Models

- **Base** — Declarative base with generic `serialize()` method using SQLAlchemy inspection
- **AIMessageRecord** — `ai_messages` table: id, human_message_id (FK), content, thinking, model, mode, timestamp. Has relationship to `ToolCallRecord` and `HumanMessageRecord`
- **HumanMessageRecord** — `human_messages` table: id, session_id (FK), content, timestamp. Relationships to `SessionRecord`, `AttachmentRecord`, `AIMessageRecord`
- **SessionRecord** — `sessions` table: id, title, date. One-to-many with `HumanMessageRecord`
- **AttachmentRecord** — `attachments` table: id, human_message_id (FK), name, type, size
- **ToolCallRecord** — `tool_calls` table: id, ai_message_id (FK), name, icon, status, input (JSON), output (JSON)
- **AIModel** — `ai_models` table: id, label, value, custom (boolean)

### `db/session.py` — Database Session

- Creates `engine` from `settings.SQLALCHEMY_DATABASE_URL` with `check_same_thread=False` (required for SQLite)
- `SessionLocal` — sessionmaker bound to the engine
- `get_db()` — FastAPI dependency that yields a session per request and closes it in `finally`

### `debugger/virtual_node.py` — VirtualNode

- Wraps a graph node's runnable function with debugger hooks
- **Attributes**: `name`, `func`, `breakpoint`, `input_state`, `output_state`, `error`
- `build(builder)` — Adds itself to a `StateGraph` builder
- `set_breakpoint(bool)` — Enables/disables breakpoint
- `__call__()` — Async invocation:
  1. Stores input state
  2. If breakpoint is set, spins with `asyncio.sleep(0.1)` until cleared
  3. Calls `on_pre_execute` hook
  4. Invokes the wrapped function
  5. Catches exceptions and stores error traceback
  6. Calls `on_post_execute` hook
  7. Returns the result

### `debugger/virtual_graph.py` — VirtualGraph

- Manages conversion of a `CompiledStateGraph` into a chain of `VirtualNode` instances
- `build_virtual_nodes()` — Creates VirtualNode wrappers for each node in the graph
- `link_virtual_edges()` — Chains nodes together following graph edges; creates `ConditionalNode` instances for conditional edges
- `compile_node()` — Compiles a single node, handling subgraphs recursively
- `compile_graph(state)` — Builds and compiles a new `StateGraph` from the virtual node chain
- `__getitem__()` — Lookup a node by name (supports `vg["name"]` and `vg["name", nodes_list]`)
- `__iter__()` — Iterates through the linked node chain

### `debugger/executor.py` — Executor

- Orchestrates graph execution with debugger hooks
- `set_virtual_graph(virtual_graph)` — Attaches a VirtualGraph and recompiles the runnable graph
- `_compile_graph()` — Recompiles using the state schema, populates virtual nodes from the original graph's builder
- `execute(state)` — Launches `graph.ainvoke()` as a background asyncio task with `stream_mode="updates"`
- `insert_state_hook(hook)` — Stores a `StateHook` for LIFO application during pre-execution
- `on_node_pre_executed(node)` — Applies matching state hooks, sends `running` packet
- `on_node_post_executed(node)` — Sends `success` or `error` packet

### `debugger/conditional_node.py` — ConditionalNode

- Extends `VirtualNode` to handle conditional/cyclical routing
- `next` property — Evaluates the condition by checking the source node's output state against condition mappings
- `next` setter — Stores the fallback `_next` node
- Used by `VirtualGraph.link_virtual_edges()` for conditional edges

### `debugger/types.py` — Type Definitions

- `StateHook(TypedDict)` — Describes a state mutation hook:
  - `nodeId: str` — Target node identifier
  - `updates: dict[str, Any]` — State key/value pairs to merge

### `schemas/chat.py` — Chat Schemas

- **CamelBaseModel** — Pydantic BaseModel with camelCase alias generation
- **Type Aliases**: `ChatModeType`, `AttachmentType`, `ToolIconType`, `ToolStatusType`, `RoleType`
- **Models**: `Attachment`, `ToolCall`, `ChatMessage`, `ChatSession`, `AIModel`, `ChatModeInfo`
- **Constants**: `CHAT_MODES` (5 modes), `DEFAULT_MODELS` (4 models)
- **Request/Response**: `SendMessageRequest` (with `model_name` aliased as `model`), `SendMessageResponse`

### `schemas/graph.py` — Graph Schemas

- **CamelBaseModel** — Duplicated from chat.py for separation of concerns
- **Type Aliases**: `NodeStatusType` (idle/running/success/error), `GraphNodeType` (start/agent/tool/end)
- **Models**: `GraphNodeData`, `NodePosition`, `NodeFlow`, `EdgeFlow`, `ExecutionStep`, `GraphData`

### `schemas/model.py` — Model Schema

- **AIModel** — Simple Pydantic model with `label`, `value`, `custom` fields

### `services/action_router.py` — WebSocket Action Router

- `route_action(action_ctx, context, send)` — Dispatches WebSocket actions via pattern matching:
  - `"fetch"` — Calls `get_graph_metadata()` and returns graph data
  - `"run"` — Calls `executor.execute()` with initial state
  - `"update_state"` — Calls `executor.insert_state_hook()`
  - `"set_breakpoint"` — Sets breakpoint on a VirtualNode
  - `"remove_breakpoint"` — Removes breakpoint from a VirtualNode
  - Default — Returns error for unknown actions
- `get_graph_metadata(graph, virtual_graph)` — Graph → React Flow layout engine:
  - BFS traversal to assign depth levels
  - Hierarchical positioning with centering at X=400
  - Node type mapping (start→"START", tool→"tool", others→"agent")
  - Edge styling with cycle detection (back-edges → smoothstep + orange)
  - Returns `GraphData` dict serialized with `by_alias=True`

---

## Client (`client/src/`)

### `App.tsx` — Root Component

- Sets up providers: `QueryClientProvider`, `TooltipProvider`, `GraphWsProvider`, `BrowserRouter`
- Renders `Toaster` (shadcn) and `Sonner` (toast library)
- Routes: `/` → `Index`, `*` → `NotFound`

### `main.tsx` — Entry Point

- Creates React root at `#root` and renders `<App />`
- Imports `index.css` for Tailwind

### `index.css` — Global Styles

- Imports Inter and JetBrains Mono fonts
- Tailwind directives (`@tailwind base/components/utilities`)
- CSS custom properties for light and dark themes
- Chat-specific colors (`--chat-user`, `--chat-ai`, `--chat-thinking`, etc.)
- React Flow theme overrides
- Custom utilities: `scrollbar-thin`, staggered animation delays, shimmer effect
- Smooth theme transition on `body`, `.bg-background`, `.bg-sidebar`, `.bg-card`

### `pages/Index.tsx` — Main Application Page

- Wraps everything in `ChatProvider`
- `ChatApp` component manages:
  - Sidebar open/close state
  - Settings modal visibility
  - Active view (chat vs graph) via `Tabs`
  - Theme via `useTheme` hook
- **Chat view**: Sidebar, message list (with empty state), `TypingIndicator`, `ChatInput`
- **Graph view**: `GraphDebugger` component
- Header with view switcher, model selector (chat), deploy button (graph)

### `pages/NotFound.tsx` — 404 Page

- Simple centered 404 page with link back to home
- Logs attempted path to console

### `components/GraphWsProvider.tsx` — WebSocket Provider

- Creates `GraphWsContext.Provider` using value from `useGraphWsProvider()`
- Wraps the entire app for WebSocket access

### `components/NavLink.tsx` — Navigation Link

- Wrapper around React Router's `NavLink` with `className` merging via `cn()`
- Supports `activeClassName` and `pendingClassName` props

### `components/graph/GraphDebugger.tsx` — Graph Debugger

- Main debugger orchestrator component
- Manages: `graphData`, `loading`, `currentStep`, `isPlaying`, `isPaused`, `selectedNode`, `breakpoints`
- Subscribes to WebSocket `graph_data` and `node_state_update` events
- Sends `"fetch"` action on WebSocket connect
- **Breakpoint toggle**: Sends `"set_breakpoint"` / `"remove_breakpoint"` actions
- **Execution controls**: Reset, step back, play/pause, step forward handlers
- **Keyboard shortcuts**: Space, ArrowLeft, ArrowRight, R, Escape
- **Auto-open error panel**: Automatically opens StateInspector when a node enters error state
- **Auto-play**: Advances steps every 1 second, pausing at breakpoints
- **React Flow**: Renders with custom `nodeTypes`, `Background`, `Controls`, `MiniMap`
- MiniMap node colors: error=red, success=green, running=blue, idle=muted

### `components/graph/GraphNode.tsx` — Custom React Flow Node

- Memoized component rendering a styled card for each graph node
- **Type config**: start→Play(green), agent→Bot(blue), tool→Wrench(amber), end→Square(gray)
- **Status styles**: running→blue pulse, success→green border, error→red border+shadow, idle→gray+opacity
- **Breakpoint indicator**: Circle button on the left side of agent/tool nodes
- **Handles**: Source on bottom, Target on top (except START/END)

### `components/graph/ExecutionControls.tsx` — Controls Bar

- Floating control bar positioned at the bottom center of the graph view
- **Controls**: Reset, Step Back, Play/Pause (with pulse animation), Step Forward
- **Connection indicator**: Green/red dot
- **Step counter**: `currentStep/totalSteps` with mini progress bar
- **Breakpoint badge**: Shows count when breakpoints are active, clickable to clear all
- Tooltips on all controls with keyboard shortcut hints

### `components/graph/StateInspector.tsx` — State Inspector Panel

- Side panel (320px width) displaying selected node's details
- **Header**: Node label, status dot, status badge, type badge, breakpoint badge
- **Error section**: Red card with stack trace (auto-opened on error)
- **Tabs**: Input (editable for agent/tool), Output (read-only)
- **JsonViewer**: Inline JSON editor with copy, edit, save, cancel
  - Edit mode: Validates JSON before saving, shows parse errors
  - Read mode: Copy button with checkmark feedback
- **Rerun button**: Re-executes the selected node
- Close button or Escape key to dismiss

### `components/chat/ChatInput.tsx` — Message Input

- Textarea with auto-resize (up to 200px)
- File attachment with drag-and-drop
- File type detection by extension (code, data, image, document)
- File badge display with type-specific icons and size
- Send button with loading spinner
- Enter to send, Shift+Enter for newline
- Visual feedback: focus ring, hover shadow, drag highlight

### `components/chat/ChatMessage.tsx` — Message Bubble

- Renders user and assistant messages with role-specific styling
- User: `User` icon, left-aligned
- Assistant: `Bot` icon with `Sparkles`, thinking block, tool calls, markdown content
- Attachment badges with type-specific icons
- Staggered animation delay based on message index

### `components/chat/ChatSidebar.tsx` — Session Sidebar

- Date-grouped conversation list
- Active session highlighting with blue accent
- New Chat button
- Theme toggle (cycles light/dark/system) with appropriate icons
- Settings gear button
- Animated slide-in with scroll area

### `components/chat/MarkdownRenderer.tsx` — Markdown Renderer

- Uses `react-markdown` with custom component overrides
- **Code blocks**: Syntax-highlighted with Prism (dracula theme), copy button with checkmark feedback
- **Inline code**: Muted background with border
- **Headings**, **paragraphs**, **lists**, **blockquotes**: Styled with consistent typography
- CodeBlock sub-component with language label and copy functionality

### `components/chat/ModelSelector.tsx` — Model Picker

- Dropdown select with model list
- Custom model support: "Add custom model" option opens a dialog
- Custom model management: Add via text input, delete with X button, badge display
- Visual indicators: "Custom" badge on user-added models

### `components/chat/ModeSelector.tsx` — Chat Mode Selector

- Dropdown menu with 5 chat modes
- Each mode has an icon (Brain, Search, Lightbulb, Zap, MessageSquare), label, and description
- Active mode highlighted in accent

### `components/chat/SettingsModal.tsx` — Settings Dialog

- Modal with system instructions textarea
- Default system prompt for AI behavior
- Dialog with title, description, and form

### `components/chat/ThinkingBlock.tsx` — AI Reasoning Block

- Collapsible section showing AI's step-by-step reasoning
- Toggle button with brain icon and "Thought for 12 seconds" label
- Animated expand/collapse with CSS grid transitions

### `components/chat/ToolCallBlock.tsx` — Tool Call Display

- Collapsible block for each tool call
- Type-specific icons (globe, code, database, search)
- Status badges: completed (green), running (blue, spinning), error (red)
- Expandable input/output JSON display in monospace pre blocks

### `hooks/use-chat.tsx` — Chat State Management

- React Context provider for all chat state
- Manages: sessions, active session, models, selected model, chat mode, loading/sending states
- **Initialization**: Fetches sessions and models on mount via `mockApi`
- **Operations**: `sendMessage`, `createNewChat`, `deleteChat`, `switchSession`, `addCustomModel`, `removeCustomModel`
- `sendMessage` appends both user and assistant messages to the active session
- `activeSession` computed from `sessions.find()` with empty fallback

### `hooks/use-graph-ws.ts` — WebSocket Hook

- Manages a single WebSocket connection to `ws://127.0.0.1:2026/ws/graph`
- **Auto-reconnect**: Exponential backoff from 2s to 30s, resets on successful connection
- **Subscription model**: `subscribe()` and `subscribeNodeState()` return unsubscribe functions
- Handles message types: `graph_data`, `node_state_update`, `status`, `error`
- `send()` action with payload serialization
- Cleanup on unmount with intentional close flag to prevent reconnection

### `hooks/use-theme.ts` — Theme Management

- Manages "light", "dark", "system" theme modes
- Persists to `localStorage`
- Applies theme by toggling `.dark` class on `<html>`
- Listens for system preference changes when in "system" mode

### `hooks/use-mobile.tsx` — Mobile Detection

- Checks window width against 768px breakpoint
- Uses `matchMedia` listener for reactive updates

### `hooks/use-toast.ts` — Toast System

- shadcn/ui toast implementation with reducer pattern
- `TOAST_LIMIT=1`, `TOAST_REMOVE_DELAY=1000000ms`
- Functions: `toast()`, `useToast()`, `dismiss()`
- Auto-removal queue with configurable delay

### `lib/utils.ts` — Utility

- `cn()` — Merges Tailwind classes using `clsx` and `tailwind-merge`

### `lib/mock-data.ts` — Type Definitions + Demo Data

- **Types**: `Attachment`, `ToolCall`, `ChatMessage`, `ChatSession`, `AIModel`, `ChatMode`
- **Constants**: `chatModes` (5 modes), `defaultModels` (4 models)
- **Demo data**: `demoMessages` (user + assistant with thinking+tool calls), `initialSessions` (6 sessions)

### `lib/mock-api.ts` — API Client

- Base URL: `http://127.0.0.1:2026`
- **In-memory store**: `_sessions` and `_models` for mock fallback
- Every function follows the pattern: try real API → catch → fallback to mock
- **Endpoints**: sessions (fetch, get, create, delete), messages (send), models (fetch, add, remove), graph (fetch, run, pause, rerun, breakpoints), health check
- **Graph fetch**: Merges node states from a separate `/graph/states` endpoint if available
- Exported as `api` object with organized namespace

### `lib/graph-data.ts` — Graph Types + Mock Data

- **Types**: `NodeStatus`, `GraphNodeData`
- **Mock nodes**: 5 nodes (start, routing_agent, web_search, formatter, end) with realistic data
- **Mock edges**: 4 edges showing linear flow + cycle detection demo
- **Mock execution steps**: 3 steps (start→success, routing_agent→success, web_search→error)

### `test/example.test.ts` — Sample Test

- Basic Vitest test: `expect(true).toBe(true)`
- Placeholder for future tests

### `test/setup.ts` — Test Environment

- Imports `@testing-library/jest-dom` for DOM matchers
- Mocks `window.matchMedia` for theme tests in jsdom

### `index.html` — HTML Entry

- Vite entry point with `#root` div
- Meta tags (OG, Twitter) for social sharing
- TODO notes for customizing title and description

### Configuration Files

| File | Purpose |
|---|---|
| `vite.config.ts` | Vite config: port 8080, `@/` path alias, lovable-tagger plugin |
| `vitest.config.ts` | Vitest: jsdom environment, globals, setup file, test patterns |
| `tailwind.config.ts` | Tailwind: custom colors (sidebar, chat, accent), fonts (Inter, JetBrains Mono), animations (20+ keyframes) |
| `tsconfig.json` | TypeScript project references (app + node) |
| `tsconfig.app.json` | TS config for source: ES2020, JSX react-jsx, bundler resolution, `@/` alias |
| `tsconfig.node.json` | TS config for Vite config file |
| `eslint.config.js` | ESLint 9 flat config: TS, React hooks, React refresh |
| `postcss.config.js` | PostCSS with Tailwind and autoprefixer |
| `components.json` | shadcn/ui configuration: default style, CSS variables, aliases |
| `package.json` | Dependencies (React, ReactFlow, TanStack Query, Tailwind, shadcn, etc.) |
| `client/.gitignore` | Node modules, dist, build artifacts |

### `.env` — Environment Variables

```
OPENROUTER_API_KEY=sk-or-v1-...
LLM_MODEL=deepseek/deepseek-v3.2
VISION_MODEL=qwen/qwen2.5-vl-32b-instruct
SUMMARIZATION_LLM=google/gemma-3-12b-it
```
