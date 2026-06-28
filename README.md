# LangGraph Debugger

<p align="center">
  <img src="https://img.shields.io/badge/python-3.13+-blue.svg" alt="Python version">
  <img src="https://img.shields.io/badge/react-18.3-61dafb.svg" alt="React version">
  <img src="https://img.shields.io/badge/fastapi-latest-009688.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License">
</p>

**LangGraph Debugger** is a real-time visual debugger and development environment for [LangGraph](https://langchain-ai.github.io/langgraph/) stateful execution graphs. It combines a Python ASGI backend with a React/TypeScript frontend to provide step-through execution, breakpoints, state inspection, and a chat interface — all in one tool.

---

## Features

### Graph Debugger
- **Visual graph rendering** — Auto-generated React Flow diagrams with hierarchical BFS layout
- **Step-through execution** — Play, pause, step forward/back, and reset controls
- **Breakpoints** — Toggle breakpoints on any agent or tool node; execution pauses before the node runs
- **Real-time state updates** — WebSocket-driven node status streaming (idle, running, success, error)
- **State Inspector** — Side panel showing node input/output state with editable JSON viewer
- **Error detection** — Auto-opens the error panel on exception with full stack traces
- **Node re-execution** — Rerun individual nodes from the inspector
- **State injection** — Modify node input state mid-execution via the editor
- **Cycle handling** — Detects cyclical back-edges and renders them with smoothstep routing in orange
- **Keyboard shortcuts** — Space (play/pause), Arrow keys (step), R (reset), Escape (close inspector)
- **Mini-map & zoom controls** — Built-in React Flow navigation

### Chat Interface
- **Multi-session management** — Sidebar with date-grouped conversation history
- **AI model selection** — GPT-4o, Claude, Gemini, and custom model endpoints
- **Chat modes** — Default, Deep Thinking, Research, Creative, Concise
- **File attachments** — Drag-and-drop with visual file badges (code, data, image, document)
- **Rich markdown rendering** — Syntax-highlighted code blocks with copy, collapsible thinking/tool-call blocks
- **System prompt configuration** — Customizable AI behavior instructions

### Backend
- **WebSocket API** — Real-time graph execution control and state streaming
- **REST API** — Chat, history, model management, and graph metadata endpoints
- **Virtual Graph** — Instrumented node wrappers with pre/post execution hooks and breakpoints
- **SQLite persistence** — Chat history and model configuration stored in a local database
- **Auto-layout engine** — BFS hierarchical layout with cycle detection
- **Graceful fallback** — Frontend falls back to mock data when the backend is unreachable

---

## Architecture

```
                  ┌─────────────────────────────────────────────┐
                  │              React Frontend                 │
                  │  ┌──────────┐  ┌─────────────────────────┐  │
                  │  │ Chat UI  │  │    Graph Debugger       │  │
                  │  │ (Sessions,│  │ - ReactFlow diagram     │  │
                  │  │  Messages,│  │ - Execution controls    │  │
                  │  │  Models)  │  │ - State inspector       │  │
                  │  └────┬─────┘  └───────────┬─────────────┘  │
                  │       │                    │                │
                  │       └────────┬───────────┘                │
                  │           Mock API Layer                    │
                  └────────────────┼────────────────────────────┘
                                   │ HTTP / WebSocket
                  ┌────────────────┼────────────────────────────┐
                  │      FastAPI Server (Python)                │
                  │  ┌─────────────┴──────────────┐             │
                  │  │   API Routes              │             │
                  │  │  - /chat/send             │             │
                  │  │  - /history/*             │             │
                  │  │  - /models/*              │             │
                  │  │  - /ws/graph (WebSocket)  │             │
                  │  └─────────────┬──────────────┘             │
                  │                │                            │
                  │  ┌─────────────┴──────────────┐             │
                  │  │   Debugger Engine          │             │
                  │  │  - VirtualNode wrappers    │             │
                  │  │  - VirtualGraph compiler   │             │
                  │  │  - Executor with hooks     │             │
                  │  │  - Action router (WS)      │             │
                  │  └─────────────┬──────────────┘             │
                  │                │                            │
                  │  ┌─────────────┴──────────────┐             │
                  │  │   LangGraph Runtime        │             │
                  │  │  - CompiledStateGraph       │             │
                  │  │  - StateGraph builder       │             │
                  │  └────────────────────────────┘             │
                  │                │                            │
                  │  ┌─────────────┴──────────────┐             │
                  │  │   SQLite Database          │             │
                  │  │  - Sessions, Messages      │             │
                  │  │  - AI Models               │             │
                  │  └────────────────────────────┘             │
                  └─────────────────────────────────────────────┘
```

---

## Project Structure

```
langgraph-debugger/
├── client/                          # React/TypeScript frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── chat/                # Chat UI components
│   │   │   │   ├── ChatInput.tsx    # Message input with drag-and-drop
│   │   │   │   ├── ChatMessage.tsx  # Message bubble renderer
│   │   │   │   ├── ChatSidebar.tsx  # Session list sidebar
│   │   │   │   ├── MarkdownRenderer.tsx  # Markdown + code blocks
│   │   │   │   ├── ModelSelector.tsx     # AI model picker
│   │   │   │   ├── ModeSelector.tsx      # Chat mode selector
│   │   │   │   ├── SettingsModal.tsx     # System prompt editor
│   │   │   │   ├── ThinkingBlock.tsx     # Collapsible reasoning
│   │   │   │   └── ToolCallBlock.tsx     # Tool call display
│   │   │   ├── graph/               # Graph debugger components
│   │   │   │   ├── ExecutionControls.tsx # Play/pause/step controls
│   │   │   │   ├── GraphDebugger.tsx     # Main debugger orchestrator
│   │   │   │   ├── GraphNode.tsx         # Custom React Flow node
│   │   │   │   └── StateInspector.tsx    # Side panel state viewer
│   │   │   ├── ui/                  # 50+ shadcn/ui components
│   │   │   ├── GraphWsProvider.tsx  # WebSocket context provider
│   │   │   └── NavLink.tsx          # Navigation link wrapper
│   │   ├── hooks/
│   │   │   ├── use-chat.tsx         # Chat state management (Context)
│   │   │   ├── use-graph-ws.ts      # WebSocket connection hook
│   │   │   ├── use-mobile.tsx       # Responsive breakpoint hook
│   │   │   ├── use-theme.ts         # Light/dark/system theme hook
│   │   │   └── use-toast.ts         # Toast notification system
│   │   ├── lib/
│   │   │   ├── graph-data.ts        # Graph node/edge types
│   │   │   ├── mock-api.ts          # API client with mock fallbacks
│   │   │   ├── mock-data.ts         # Demo data and type definitions
│   │   │   └── utils.ts             # cn() utility function
│   │   ├── pages/
│   │   │   ├── Index.tsx            # Main app layout + view switching
│   │   │   └── NotFound.tsx         # 404 page
│   │   ├── test/
│   │   │   ├── example.test.ts      # Sample Vitest test
│   │   │   └── setup.ts             # Test environment setup
│   │   ├── App.tsx                  # Root React component
│   │   ├── main.tsx                 # Entry point
│   │   └── index.css                # Tailwind + CSS variables
│   ├── index.html
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   └── package.json
├── server/                          # Python FastAPI backend
│   └── src/
│       ├── app.py                   # FastAPI app factory + lifespan
│       ├── dev.py                   # Demo graph + local runner
│       ├── api/routes/
│       │   ├── __init__.py          # Route registry
│       │   ├── chat.py              # POST /chat/send
│       │   ├── graph.py             # WebSocket /ws/graph + HTTP /ws/info
│       │   ├── history.py           # GET /history/threads, /{id}, /{id}/latest
│       │   └── aimodels.py          # CRUD /models/add, /fetch, /delete
│       ├── core/
│       │   ├── config.py            # Pydantic BaseSettings
│       │   └── logging.py           # (empty, ready for config)
│       ├── db/
│       │   ├── models.py            # SQLAlchemy 2.0 models
│       │   └── session.py           # Engine + session dependency
│       ├── debugger/
│       │   ├── virtual_node.py      # Node wrapper with hooks
│       │   ├── virtual_graph.py     # Graph recompiler with VirtualNodes
│       │   ├── executor.py          # Execution orchestrator
│       │   ├── conditional_node.py  # Conditional routing node
│       │   └── types.py             # StateHook TypedDict
│       ├── schemas/
│       │   ├── chat.py              # Chat request/response models
│       │   ├── graph.py             # Graph data Pydantic models
│       │   └── model.py             # AI model schema
│       └── services/
│           └── action_router.py     # WebSocket action dispatcher
└── docs/                            # Full documentation (see below)
```

---

## Quick Start

### Prerequisites
- **Node.js** 18+ and **npm** (or **bun**)
- **Python** 3.11+
- **Git**

### Client (Frontend)

```bash
cd client
npm install
npm run dev
```

The Vite dev server starts at `http://localhost:8080`.

### Server (Backend)

```bash
cd server
python -m venv .venv
# Windows:
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

pip install langgraph fastapi uvicorn sqlalchemy pydantic pydantic-settings

python -m src.dev
```

The FastAPI server starts at `http://127.0.0.1:2026`.

### Running Together

1. Start the server (terminal 1)
2. Start the client (terminal 2)
3. Open `http://localhost:8080` in your browser
4. Toggle between **Chat View** and **Graph Debugger** using the top navigation tabs

---

## Documentation

Full documentation is available in the [`docs/`](docs/) folder:

| Document | Description |
|---|---|
| [Architecture](docs/architecture.md) | System architecture, data flow, core concepts |
| [Setup Guide](docs/setup.md) | Environment setup and local development |
| [Usage Guide](docs/usage.md) | How to use the chat and debugger interfaces |
| [Development Guide](docs/development.md) | Code structure, linting, testing |
| [Contributing](docs/contributing.md) | PR checklist and contribution guidelines |
| [API Reference](docs/api.md) | REST endpoint documentation |
| [WebSocket Reference](docs/websocket.md) | WebSocket protocol and message formats |
| [Codebase Overview](docs/codebase.md) | Detailed file-by-file walkthrough |
| [Server Debugger](docs/server-debugger.md) | VirtualNode, VirtualGraph, Executor internals |
| [Client Components](docs/client-components.md) | Frontend component architecture |
| [Client Hooks](docs/client-hooks.md) | React hooks and state management |
| [Database Schema](docs/database.md) | SQLAlchemy models and relationships |
| [Pydantic Schemas](docs/schemas.md) | Request/response model documentation |
| [Configuration](docs/config.md) | Environment variables and settings |

---

## Tech Stack

### Frontend
| Technology | Purpose |
|---|---|
| React 18.3 | UI framework |
| TypeScript 5.8 | Type safety |
| Vite 7.3 | Build tool |
| React Flow 11.11 | Graph visualization |
| Tailwind CSS 3.4 | Styling |
| shadcn/ui | Component library (50+ components) |
| TanStack React Query 5 | Server state management |
| react-markdown | Markdown rendering |
| Vitest | Unit testing |

### Backend
| Technology | Purpose |
|---|---|
| Python 3.13 | Runtime |
| FastAPI | ASGI web framework |
| Uvicorn | ASGI server |
| SQLAlchemy 2.0 | ORM |
| SQLite | Database |
| Pydantic 2 | Validation |
| LangGraph | Graph execution engine |

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
