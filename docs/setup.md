# Setup Guide

## Prerequisites

- **Node.js** 18+ and **npm** (or **bun**)
- **Python** 3.11+
- **Git**
- A terminal (PowerShell, bash, zsh)

---

## Client Setup

```bash
# Navigate to the client directory
cd client

# Install dependencies
npm install

# Start the development server
npm run dev
```

The client runs on `http://localhost:8080` by default (configured in `vite.config.ts`).

### Available Scripts

| Command | Description |
|---|---|
| `npm run dev` | Start Vite dev server with HMR |
| `npm run build` | Production build to `client/dist/` |
| `npm run preview` | Preview the production build |
| `npm run test` | Run Vitest unit tests |
| `npm run lint` | Run ESLint across all source files |

---

## Server Setup

### 1. Create a Virtual Environment

```bash
cd server
python -m venv .venv

# Windows (PowerShell):
.venv\Scripts\Activate.ps1

# Windows (CMD):
.venv\Scripts\activate.bat

# macOS/Linux:
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
# Install the required packages
pip install langgraph fastapi uvicorn sqlalchemy pydantic pydantic-settings
```

> **Note**: The `pyproject.toml` does not yet list dependencies. Install them manually as above, or create a `requirements.txt`.

### 3. Run the Development Server

```bash
python -m src.dev
```

The server starts on `http://127.0.0.1:2026` with hot-reload enabled.

### Windows Helper Script

```bash
# From the repository root:
server\run.bat
```

---

## Environment Variables

Copy or create a `.env` file in the repository root. The server's `Settings` class reads from environment variables if set.

| Variable | Default | Description |
|---|---|---|
| `PROJECT_NAME` | `Agent Studio` | Application name for OpenAPI docs |
| `VERSION` | `0.1.0` | Application version |
| `DEBUG` | `True` | Enable debug mode |
| `BACKEND_CORS_ORIGINS` | `["http://localhost:8080", "http://127.0.0.1:8080"]` | Allowed CORS origins |
| `SQLALCHEMY_DATABASE_URL` | `sqlite:///./database.db` | Database connection string |
| `OPENROUTER_API_KEY` | — | API key for OpenRouter |
| `LLM_MODEL` | — | Default LLM model identifier |

---

## Verify Setup

1. Start the server and confirm: `INFO: Uvicorn running on http://127.0.0.1:2026`
2. Start the client and confirm: `VITE v7.x.x ready in ...ms`
3. Open `http://localhost:8080` in your browser
4. You should see the LangGraph Studio interface with **Chat View** active
5. Toggle to **Graph Debugger** to see the demo graph visualization
6. If the backend is running, the WebSocket connects and the graph loads with real data; if not, mock data is used
