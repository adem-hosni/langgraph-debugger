# LangGraph Debugger

# LangGraph Debugger

LangGraph Debugger is a developer tool for building, running and
observing stateful execution graphs. It pairs a TypeScript/React
frontend with a Python ASGI backend that compiles and executes state
graphs while exposing debug hooks (breakpoints, state injection,
progress events) to the UI.

This repository contains two main projects:

- `client/` — the web-based UI (React + TypeScript + Vite).
- `server/` — Python backend with the execution engine and websocket
	API.

See the `docs/` folder for full documentation and setup instructions:

- `docs/index.md` — documentation entry point.

Quick start (development)

Client

```bash
cd client
npm install
npm run dev
```

Server

```bash
cd server
python -m venv .venv
. .venv/bin/activate   # on Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m src.dev
```

Contributing

See `docs/contributing.md` for contribution guidelines and PR
checklists.
