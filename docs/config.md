# Configuration Reference

## Server Configuration (`server/src/core/config.py`)

The `Settings` class uses Pydantic's `BaseSettings` to read configuration. Values can be set via environment variables or a `.env` file.

```python
class Settings(BaseSettings):
    PROJECT_NAME: str = "Agent Studio"
    DESCRIPTION: str = "Real-time debugger and visualizer for LangGraph"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ]
    DEBUG: bool = True
    SQLALCHEMY_DATABASE_URL: str = "sqlite:///./database.db"
```

### All Settings

| Variable | Default | Description |
|---|---|---|
| `PROJECT_NAME` | `Agent Studio` | Application name used in OpenAPI docs and logging |
| `DESCRIPTION` | `Real-time debugger and visualizer for LangGraph` | Application description |
| `VERSION` | `0.1.0` | Application version string |
| `API_V1_STR` | `/api/v1` | API version prefix (currently unused by routes) |
| `BACKEND_CORS_ORIGINS` | `["http://localhost:8080", "http://127.0.0.1:8080"]` | Allowed CORS origins (space-separated in env var) |
| `DEBUG` | `True` | Enable debug mode and detailed error responses |
| `SQLALCHEMY_DATABASE_URL` | `sqlite:///./database.db` | Database connection string |

### Environment Variables

Override any setting by setting the corresponding environment variable:

```bash
# Windows (PowerShell)
$env:PROJECT_NAME = "My Debugger"
$env:SQLALCHEMY_DATABASE_URL = "sqlite:///./custom.db"
$env:DEBUG = "false"

# macOS/Linux
export PROJECT_NAME="My Debugger"
export SQLALCHEMY_DATABASE_URL="sqlite:///./custom.db"
export DEBUG="false"
```

For `BACKEND_CORS_ORIGINS`, use a comma-separated string:

```bash
export BACKEND_CORS_ORIGINS="http://localhost:3000,http://localhost:8080"
```

---

## Environment Variables (`.env`)

The `.env` file in the repository root stores API keys and model selections:

```
OPENROUTER_API_KEY=sk-or-v1-...
LLM_MODEL=deepseek/deepseek-v3.2
VISION_MODEL=qwen/qwen2.5-vl-32b-instruct
SUMMARIZATION_LLM=google/gemma-3-12b-it
```

| Variable | Purpose |
|---|---|
| `OPENROUTER_API_KEY` | API key for OpenRouter (LLM gateway) |
| `LLM_MODEL` | Default model identifier for chat completion |
| `VISION_MODEL` | Model identifier for vision/image tasks |
| `SUMMARIZATION_LLM` | Model identifier for summarization tasks |

> **Security**: The `.env` file is listed in `.gitignore` and should never be committed. These values are not currently read by the `Settings` class — they are used directly by the LangGraph application that imports the debugger.

---

## Frontend Configuration

### Vite (`client/vite.config.ts`)

| Setting | Value | Description |
|---|---|---|
| `server.host` | `"::"` | Listen on all network interfaces |
| `server.port` | `8080` | Development server port |
| `resolve.alias["@"]` | `"./src"` | Path alias for imports |

### API Base URL (`client/src/lib/mock-api.ts`)

```typescript
const API_BASE_URL = "http://127.0.0.1:2026";
```

All API calls target this URL. Change it to match your server's address and port.

### WebSocket URL (`client/src/hooks/use-graph-ws.ts`)

```typescript
const WS_URL = "ws://127.0.0.1:2026/ws/graph";
```

The WebSocket connection URL. Update if the server runs on a different host or port.

### Reconnection Settings

```typescript
const INITIAL_RECONNECT_DELAY = 2000;  // 2 seconds
const MAX_RECONNECT_DELAY = 30000;     // 30 seconds
```

---

## Demo Graph Configuration (`server/src/dev.py`)

The demo graph runs on port **2026** with hot-reload:

```python
serve("dev:app", port=2026, reload=True)
```

The initial state can be modified:

```python
initial_state = {
    "topic": "LangGraph Advanced Routing",
    "draft": "",
    "iterations": 0,
    "feedback": [],
    "status": "pending",
}
```

---

## shadcn/ui Configuration (`client/components.json`)

```json
{
  "style": "default",
  "rsc": false,
  "tsx": true,
  "tailwind": {
    "config": "tailwind.config.ts",
    "css": "src/index.css",
    "baseColor": "slate",
    "cssVariables": true
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils",
    "ui": "@/components/ui",
    "lib": "@/lib",
    "hooks": "@/hooks"
  }
}
```

### Tailwind Theme Extensions

| Custom Color Group | CSS Variables | Purpose |
|---|---|---|
| `sidebar` | `--sidebar-*` | Sidebar background, foreground, accent, border |
| `chat` | `--chat-*` | Chat bubbles, thinking blocks, tool calls, code |
| `accent-blue` | `--accent-blue` | Primary accent (links, icons, running state) |
| `accent-green` | `--accent-green` | Success accent (completed, connected) |

### Custom Animations

| Animation | Duration | Purpose |
|---|---|---|
| `fade-in` | 0.4s | General entrance |
| `fade-in-up` | 0.5s | Messages and containers |
| `fade-in-left/right` | 0.3s | Tool calls, sidebar |
| `scale-in` | 0.3s | Code blocks, badges |
| `slide-in-left` | 0.3s | Sidebar |
| `typing-dot` | 1.4s | Typing indicator |
| `glow-pulse` | 2s | Empty state icon |
| `shimmer` | 2s | Loading states |
