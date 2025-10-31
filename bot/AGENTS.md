# Repository Guidelines

## Project Structure & Module Organization
- `luka_bot/` contains the production Telegram agent, grouped into `core/` (settings, bootstrapping), `handlers/` (feature routers), `services/` (external integrations), and `utils/`. Place new middlewares in `luka_bot/middlewares/` and reusable schemas in `luka_bot/schemas/`.
- `ag_ui_gateway/` hosts the admin web UI and REST gateway; `flow_client/` and `camunda_client/` provide client libraries and protocol objects shared with the bot.
- Infrastructure lives at the top level (`docker-compose.yml`, `Dockerfile`, `.env.example`, `alembic.ini`, `requirements.txt`). Keep docs alongside their module (for example `*/docs/` folders) and store scripts in `luka_bot/scripts/`.

## Build, Test, and Development Commands
- `python -m venv .venv && source .venv/bin/activate` — create and activate the recommended virtualenv.
- `pip install -r requirements.txt` — install the shared dependency set for all agents and services.
- `python -m luka_bot` — start the Telegram agent in polling mode using the configuration from `.env`.
- `python -m ag_ui_gateway.main` — run the admin gateway locally; export `FLASK_ENV=development` for hot reload.
- `docker compose up -d --build` — launch the full stack (bot, Redis, and optional monitoring) with production-like settings.

## Coding Style & Naming Conventions
- Follow PEP 8 with 4-space indents, type hints for public functions, and `snake_case` module/function names; keep classes in `PascalCase`.
- Run `ruff check .` and `ruff format .` (configured via `.pre-commit-config.yaml`) before committing; commit only lint-clean code.
- Keep handlers small and declarative: route definitions in `handlers/`, business logic in `services/`, and configuration in `core/`.

## Testing Guidelines
- Use `pytest` (asyncio mode is preconfigured in `pytest.ini`). Run `pytest luka_bot` before pushing; target coverage above 80 % for new features.
- Prefer unit tests near the code under test (`<module>/tests/`) and add integration checks for cross-service flows (e.g., bot ↔ flow-client).
- Mock external APIs and queues; rely on Docker services only for explicit integration suites.

## Commit & Pull Request Guidelines
- Match the existing history: concise, present-tense messages (`adding token app launcher`) with optional scope prefixes like `handlers:` when clarity helps.
- Include a PR description that states the problem, the approach, and links to tracking issues; attach screenshots or terminal output for UI or CLI-facing changes.
- Ensure CI-lint and pytest pass locally, mention any skipped checks, and flag configuration changes that require `.env` updates.

## Environment & Configuration Tips
- Copy `.env.example` and fill in bot tokens, Redis/Postgres endpoints, and optional LLM provider keys; defaults live in `luka_bot/core/config.py`.
- For webhook deployments, align `WEBHOOK_*` settings with your public endpoint and expose the bot container port in `docker-compose.yml`.
- When enabling metrics, verify `METRICS_ENABLED` and ensure the Prometheus scraping endpoint is reachable from your monitoring stack.
