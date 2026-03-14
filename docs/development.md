# Development Guide

This guide is aimed at contributors who want to modify or extend the
project.

Project layout (high level)

- `client/` — React + TypeScript app that implements the UI.
- `server/` — Python ASGI server implementing the graph executor and
  websocket API.
- `docs/` — project documentation (this folder).

Editing the server

- Server code lives in `server/src/`. Key packages are organized as
  `debugger`, `core`, `api`, and `services`.
- The debugger wrappers are located in `server/src/debugger`.
- Add unit tests next to implementation files or in `server/tests` and
  run them with `pytest`.

Editing the client

- Client components are under `client/src/components`.
- UI state flows through React hooks in `client/src/hooks`.

Style and linting

- Use `prettier` and `eslint` rules present in the `client/` folder for
  frontend changes.
- Follow Python formatting using `black` and static checks with
  `ruff`/`flake8` for backend changes.

Testing

- Run frontend tests using `npm test` inside `client/`.
- Run backend tests with `pytest` from the `server/` directory.

Submitting changes

- Create a feature branch and open a PR describing the change.
- Include tests and update docs where relevant.
