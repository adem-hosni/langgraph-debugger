# Contributing

Thank you for considering contributing to LangGraph Debugger! This document outlines the process and expectations for contributions.

---

## Getting Started

1. **Fork** the repository
2. **Clone** your fork: `git clone https://github.com/YOUR-USERNAME/langgraph-debugger.git`
3. **Create a topic branch** with a descriptive name:
   - `feat/your-feature-name` for new features
   - `fix/your-bug-fix` for bug fixes
   - `docs/your-doc-change` for documentation updates
4. **Make your changes**
5. **Run linters and tests** locally
6. **Open a pull request**

---

## Pull Request Checklist

- [ ] Branch created from `main` (or the default branch)
- [ ] Commits are small, focused, and well-described
- [ ] Code follows existing conventions and style
- [ ] Tests added or updated for new functionality (frontend: Vitest; backend: pytest)
- [ ] Documentation updated (API docs, schemas, codebase overview)
- [ ] Lint passes (`npm run lint` for frontend, `ruff check` for backend)
- [ ] No new warnings introduced

---

## Code Style

### Frontend (TypeScript/React)
- Follow the existing component patterns (hooks, types, `cn()` utility for styling)
- Use TypeScript strict mode-compatible code (the project uses `strict: false` but prefers type safety)
- Run `npm run lint` before committing
- Name files in `kebab-case.tsx` for components, `camelCase.ts` for utilities

### Backend (Python)
- Follow PEP 8 conventions
- Use type hints for all function signatures
- Use SQLAlchemy 2.0 `Mapped` syntax for new models
- Use Pydantic `CamelBaseModel` for request/response schemas

---

## Documentation

When making changes that affect any of the following, update the corresponding documentation:

| Change | Doc to Update |
|---|---|
| New API endpoint | `docs/api.md` |
| New WebSocket action | `docs/websocket.md` |
| New database model | `docs/database.md` |
| New Pydantic schema | `docs/schemas.md` |
| New component | `docs/client-components.md` |
| New hook | `docs/client-hooks.md` |
| New configuration | `docs/config.md` |
| Architecture change | `docs/architecture.md` |

---

## Commit Messages

Follow conventional commit format:

```
feat: add node rerun capability
fix: correct WebSocket reconnection backoff
docs: update API reference with new endpoint
refactor: simplify StateHook merging logic
test: add GraphDebugger component tests
```

---

## Questions?

Open a [GitHub Issue](https://github.com/your-org/langgraph-debugger/issues) for questions, feature requests, or bug reports.
