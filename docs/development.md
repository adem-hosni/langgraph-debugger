# Development Guide

## Project Layout

```
langgraph-debugger/
├── client/          # React/TypeScript frontend (Vite)
├── server/          # Python backend (FastAPI)
└── docs/            # Documentation
```

---

## Server Development

### Code Organization

```
server/src/
├── app.py              # FastAPI app factory + lifespan
├── dev.py              # Demo graph + local runner
├── api/routes/         # Route handlers
│   ├── chat.py         # POST /chat/send
│   ├── graph.py        # WebSocket /ws/graph + HTTP /ws/info
│   ├── history.py      # GET /history/*
│   └── aimodels.py     # CRUD /models/*
├── core/               # Configuration
│   └── config.py       # Pydantic Settings
├── db/                 # Database
│   ├── models.py       # SQLAlchemy ORM models
│   └── session.py      # Engine + session dependency
├── debugger/           # Graph debugger engine
│   ├── virtual_node.py # VirtualNode wrapper
│   ├── virtual_graph.py # VirtualGraph compiler
│   ├── executor.py     # Execution orchestrator
│   ├── conditional_node.py # Conditional routing
│   └── types.py        # Type definitions
├── schemas/            # Pydantic models
│   ├── chat.py         # Chat request/response
│   ├── graph.py        # Graph data models
│   └── model.py        # AI model schema
└── services/           # Business logic
    └── action_router.py # WebSocket action dispatcher
```

### Adding a New API Route

1. Create the route file in `server/src/api/routes/`
2. Define an `APIRouter` and `prefix`
3. Import and register it in `server/src/api/routes/__init__.py`
4. Define Pydantic models in `server/src/schemas/` if needed

### Adding a New WebSocket Action

1. Add a new `case` to the `match` block in `services/action_router.py`
2. Implement handler logic, accessing `context` for `virtual_graph`, `executor`, and `graph`
3. Return a result dict with `type`, `message`, and `data` keys

### Working with the Demo Graph

The `dev.py` file contains a writing workflow graph that demonstrates:
- State initialization, drafting, review cycles
- Conditional routing with iteration limits
- Cycle detection (the `fix_errors → review` back-edge)

To customize: modify the node functions, state schema, or edge logic in `dev.py`.

---

## Client Development

### Code Organization

```
client/src/
├── components/
│   ├── chat/           # Chat UI components
│   ├── graph/          # Graph debugger components
│   └── ui/             # shadcn/ui primitives (50+ components)
├── hooks/              # React hooks
│   ├── use-chat.tsx    # Chat state (Context provider)
│   ├── use-graph-ws.ts # WebSocket connection
│   ├── use-theme.ts    # Theme management
│   ├── use-mobile.tsx  # Responsive detection
│   └── use-toast.ts    # Toast notifications
├── lib/                # Utilities
│   ├── graph-data.ts   # Graph node/edge types + mock data
│   ├── mock-api.ts     # API client with mock fallback
│   ├── mock-data.ts    # Type definitions + demo data
│   └── utils.ts        # cn() utility
├── pages/
│   ├── Index.tsx       # Main app layout
│   └── NotFound.tsx    # 404 page
└── test/               # Tests
```

### Adding a New Component

1. Determine if it belongs in `chat/`, `graph/`, or `ui/`
2. Follow existing patterns for imports, styling (Tailwind + `cn()`), and animations
3. Add type definitions to `lib/mock-data.ts` or `lib/graph-data.ts` if needed
4. Wire up state via the appropriate hook context

### The Mock API Fallback Pattern

The `mock-api.ts` module implements a **graceful fallback** pattern:

```typescript
export async function fetchSessions(): Promise<ChatSession[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/history/threads`);
    if (!response.ok) throw new Error("Endpoint not found");
    return await response.json();
  } catch (error) {
    console.warn("Server unavailable. Falling back to mock data.");
    return structuredClone(_sessions);
  }
}
```

Every API function first attempts a real HTTP call, then falls back to mock data. This allows the frontend to work fully without the backend running.

---

## Linting & Formatting

### Frontend
```bash
cd client
npm run lint           # ESLint
# Formatting: Prettier (if configured)
```

### Backend
```bash
cd server
# Python formatting
pip install black ruff
black src/
ruff check src/
```

---

## Testing

### Frontend
```bash
cd client
npm run test           # Vitest (jsdom environment)
npm run test:watch     # Watch mode
```

Tests are in `client/src/test/`. The setup file configures `@testing-library/jest-dom` and mocks `window.matchMedia` for theme tests.

### Backend
No backend tests exist yet. To add them:
1. Create a `server/tests/` directory
2. Add `pytest` test files
3. Run with: `pytest server/tests/`

---

## Common Development Tasks

### Adding a New Database Model

1. Define the class in `server/src/db/models.py` inheriting from `Base`
2. Define columns using SQLAlchemy 2.0 `Mapped` syntax
3. Add relationships and override `serialize()` if needed
4. Tables are auto-created on server startup via `Base.metadata.create_all()`

### Adding a New Chat Mode

1. Add the mode to the `ChatModeType` literal in `server/src/schemas/chat.py`
2. Add it to `CHAT_MODES` list in the same file
3. Add it to `chatModes` in `client/src/lib/mock-data.ts`
4. Add an icon mapping in `client/src/components/chat/ModeSelector.tsx`

### Adding a New Graph Node Type

1. Add the type to `GraphNodeType` literal in `server/src/schemas/graph.py`
2. Add it to `typeConfig` in `client/src/components/graph/GraphNode.tsx`
3. Update the style mapping in the auto-layout engine in `services/action_router.py`

---

## Debugging Tips

- **Server logs**: Watch the terminal running the server; `print()` statements in node functions and action handlers appear there
- **WebSocket messages**: The server prints WebSocket disconnect events; client logs parse errors to `console.warn`
- **Mock data**: If the UI works but the backend doesn't, check `mock-api.ts` fallback logs in the browser console
- **Database**: The SQLite file `server/database.db` can be inspected with any SQLite browser
- **Graph layout**: The BFS layout engine logs node levels; inspect the `positions` dict in `get_graph_metadata()` to debug layout issues
