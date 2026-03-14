# Setup / Developer Environment

This project contains a TypeScript React client and a Python server. Use
the following steps to prepare a development machine.

Prerequisites

- Node.js (v18+) and `npm` or `bun` for the client.
- Python 3.11+ and virtual environment tooling for the server.
- Git and a GitHub account (to push branches and open PRs).

Client

1. Change to the `client/` directory.
2. Install dependencies with your package manager (example using npm):

```bash
cd client
npm install
```

3. Start the dev server (Vite):

```bash
npm run dev
```

Server

1. Create and activate a Python virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # on Windows: .venv\Scripts\Activate.ps1
```

2. Install dependencies:

```bash
cd server
pip install -r requirements.txt
```

3. Run the server (development):

```bash
python -m src.dev
```

Notes

- The repo includes `run.bat` scripts for quick startup on Windows.
- If you modify server or client ports, update the client websocket
  configuration in `client/src/lib` accordingly.
