**Codebase Overview**

This document summarizes the repository layout, runtime configuration, development workflows, and key implementation details to help contributors and integrators quickly understand and work with the project.

**Repository layout (top-level)**
- `client/` — Frontend (Vite + React + TypeScript). See `client/package.json` for scripts and dependencies.
- `server/` — Backend Python app (FastAPI). Main code under `server/src`.
- `docs/` — Documentation files (this file, API + WebSocket docs).

**Frontend (`client`)**
- Entry: `client/src/main.tsx` and `client/index.html`.
- Scripts: `dev`, `build`, `preview`, `test` (see `client/package.json`).
- Major libraries: React, React Flow, Tailwind, Vitest for testing.
- Quickstart:
  - Install: `npm install` or `bun install` (in `client` folder).
  - Dev server: `npm run dev` (starts Vite).
  - Build: `npm run build`.

**Backend (`server`)**
- Entrypoints:
  - `server/src/app.py` — Factory `create_app(graph, initial_graph_state)` and `serve()` helper.
  - `server/src/dev.py` — Example graph + local runner used for manual testing.
- Routing: `server/src/api/routes/*` with routers assembled in `server/src/api/routes/__init__.py`.
  - `chat.py` — `/chat` endpoints (send messages, persists to DB).
  - `history.py` — `/history` endpoints (threads, history snapshots).
  - `graph.py` — WebSocket handler (`/ws/graph`) and HTTP `/ws/info` metadata endpoint.
  - `aimodels.py` — `/models` endpoints for managing AI model entries.
- Schemas: Pydantic models in `server/src/schemas` provide typed request/response contracts. They use a `CamelBaseModel` to emit camelCase for the client.
- Services: `server/src/services/graph_executor.py` contains WebSocket action dispatching and graph metadata composition.

**Configuration & Settings**
- `server/src/core/config.py` exposes `settings` (Pydantic BaseSettings):
  - `PROJECT_NAME`, `DESCRIPTION`, `VERSION`, `API_V1_STR`
  - `BACKEND_CORS_ORIGINS` (list)
  - `DEBUG` (bool)
  - `SQLALCHEMY_DATABASE_URL` (default `sqlite:///./database.db`)

Environment: `Settings` reads environment variables if set; override any value with standard Pydantic environment variable names (e.g. `PROJECT_NAME`, `SQLALCHEMY_DATABASE_URL`).

**Database**
- Models in `server/src/db/models.py`.
  - `sessions`, `human_messages`, `ai_messages`, `attachments`, `tool_calls`, `ai_models`.
- `server/src/db/session.py` provides `get_db` dependency and engine initialization.
- Default DB: SQLite file at `database.db` (configurable via `SQLALCHEMY_DATABASE_URL`).

**Graph & Execution**
- The project integrates with `langgraph` graph library (expected installed in the environment). Graphs are compiled to `CompiledStateGraph` objects.
- `create_app(graph, initial_state)` injects the compiled graph into `app.state.graph` and `app.state.graph_state` for route access.
- `server/src/services/graph_executor.py` transforms a compiled graph into React Flow friendly JSON. The `route_action` function handles WebSocket actions (currently `fetch` implemented; `run` is a placeholder).

**WebSocket protocol**
- Socket URL: `ws://<host>:<port>/ws/graph`.
- Envelope: JSON objects with `action` and optional `payload`. Responses use `type`, `message`, `data` envelope. See `docs/websocket.md` for full details.

**How to run (developer-friendly)**
- Frontend (project root → `client`):
```bash
cd client
npm install
npm run dev
```
- Backend (Windows helper):
```powershell
# from repo root
server\run.bat
```
- Backend (venv/pip):
```bash
cd server
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# Install dependencies via your tool (pyproject currently empty); if you have requirements.txt, use pip
# Run example dev app:
python -m src.dev
```

**Testing**
- Frontend: unit tests with `vitest` via `npm run test` in `client`.
- Backend: there are no included backend unit tests in this repo; add PyTest files under `server/tests` to enable CI.

**Development notes & extension points**
- Implement `route_action`'s `run` branch to support execution streaming and node-level control.
- Add authentication/middleware in `server/src/app.py` if exposing beyond local/dev.
- Add production DB configuration and migrations (Alembic) if you plan persistent long-term storage.
- If you want typed clients, consider generating an OpenAPI/Swagger client from FastAPI's schema (FastAPI auto-generates OpenAPI at `/docs` when running).

**Important files to review when contributing**
- `server/src/app.py` — app factory and CORS setup.
- `server/src/api/routes/*.py` — route implementations and docs mapping.
- `server/src/schemas/*.py` — Pydantic models for API contracts.
- `server/src/services/graph_executor.py` — graph -> UI payload renderer and WebSocket router.
- `client/src/components/graph/GraphDebugger.tsx` — client integration for rendering graph (frontend wiring).

**Next steps (suggested)**
- Add a `requirements.txt` or populate `pyproject.toml` for reliable Python installs.
- Add backend tests and CI job that runs `python -m pytest` (after adding tests).
- Expand WebSocket `run` action for live execution streaming and tool-call events.

If you'd like, I can: add a `requirements.txt`, implement the `run` WebSocket action with streaming, or generate an OpenAPI YAML file for client SDK generation.
