# Server

Backend code lives in `server/` (see `server/src`). The project uses a Python toolchain declared in `server/pyproject.toml`.

## Quickstart (Windows)

Run the convenience script:

```powershell
# from repo root
server\run.bat
```

## Quickstart (venv)

```bash
cd server
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# Install dependencies using your chosen tool (pip, poetry). See pyproject.toml for details.
# If you generated requirements.txt, use:
# pip install -r requirements.txt

# Run development server (example)
python -m src.dev
```

## Notes
- Use `pyproject.toml` to inspect dependencies and scripts.
- Add a `requirements.txt` if you prefer pip-only installs.
