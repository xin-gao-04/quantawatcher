# Repository Guidelines

## Purpose
QuantaWatcher aims to be a long-running local service for A-share sector/stock monitoring with scheduled collection, indicator calculation, event detection, and push notifications (see `README.md` for the current PRD/architecture).

## Project Structure & Module Organization
Current repository contents are documentation-only:
- `README.md`: requirements + proposed architecture and modules.

When implementation is added, keep a predictable layout (adjust if the repo already standardizes differently):
- `src/` or `quanta_watcher/`: core service (API, scheduler/worker, storage, indicators, rules).
- `plugins/`: plugin implementations (collector/indicator/strategy/notifier/report).
- `tests/`: automated tests.
- `docs/`: additional specs/runbooks.
- `scripts/`: local dev helpers (PowerShell on Windows).

## Build, Test, and Development Commands
No build/test commands are checked in yet. If you add runtime code, also add a single “happy path” set of commands to `README.md` (and/or a `Makefile`/`scripts/` wrapper). Example targets to provide:
- `dev`: run the API + worker locally (e.g., FastAPI + scheduler).
- `test`: run the full test suite.
- `fmt` / `lint`: apply formatting and lint checks.

## Coding Style & Naming Conventions
The current technical direction in `README.md` references FastAPI and SQLite/PostgreSQL/Redis; if you introduce a different stack, document it explicitly.
- Indentation: 4 spaces; UTF-8; LF line endings.
- Naming: `snake_case` for functions/files, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants.
- Keep modules small and layered (connectors → storage → indicators → events/rules → notifiers → web console).

## Testing Guidelines
If adding tests, keep them fast and deterministic:
- Place tests under `tests/` and use `test_*.py`/`*_test.py` naming consistently.
- Prefer unit tests for indicators/rules; add integration tests for storage + notifier boundaries using fakes/mocks.

## Commit & Pull Request Guidelines
No commit history is available yet; use a consistent convention going forward:
- Commits: Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`).
- PRs: include a concise description, linked issue (if any), how to run/verify, and screenshots for any UI changes.

## Security & Configuration Tips
- Never commit secrets (API tokens, webhooks). Use environment variables and local `.env` files (gitignored), and provide a redacted example like `config.example.env`.
- Treat external data sources as unreliable: add timeouts, retries with backoff, and clear error logs.

## Agent-Specific Instructions
- Don’t invent tooling: when adding new commands/formatters/test runners, update this file and `README.md` in the same PR.
- Keep changes scoped and document any new configuration keys.
