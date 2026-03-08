# LangGraph Debugger

A lightweight monorepo containing a Vite/Bun React client and a Python server for graph debugging and chat UI.

## Layout
- `client/` — frontend (Vite + TypeScript + React)
- `server/` — backend (Python; see `pyproject.toml`)

## Prerequisites
- Node 18+ (or Bun if you prefer)
- Python 3.10+
- Git

## Quickstart
### Client (frontend)
1. Change into the client folder:

```bash
cd client
```

2. Install dependencies and run dev server:

```bash
# using npm
npm install
npm run dev

# -- or using bun --
bun install
bun run dev
```

### Server (backend)
The server's dependencies are declared in `server/pyproject.toml`.

Windows (convenience): run the included batch script:

```powershell
# from repo root
server\run.bat
```

Or run in a virtual environment:

```bash
cd server
python -m venv .venv
.\.venv\Scripts\activate  # Windows
pip install -r requirements.txt  # if you generated one from pyproject.toml
python -m src.dev
```

## Development notes
- Frontend uses Vite + TypeScript. See `client/package.json` for scripts.
- Backend uses a `pyproject.toml` (choose pip/Poetry/other to install).

## Contributing
Open an issue or submit a PR with a concise description of your change.
