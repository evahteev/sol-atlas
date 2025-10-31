# Operations Guide

This guide covers how to run Luka Bot in production, monitor health, and respond to common operational tasks within the SOL Atlas ecosystem.

## Deployment Profiles

### Polling Mode (Default)
- **Use for** internal staging environments or when webhook infrastructure is unavailable.
- **Run via** `python -m luka_bot` or the `bot` service in `docker-compose.yml`.
- **Scaling**: Single instance recommended; enable webhook mode when horizontal scaling is required.

### Webhook Mode
- **Use for** production clusters where webhook delivery reduces latency and load.
- **Prerequisites**: Public HTTPS endpoint, TLS termination, `USE_WEBHOOK=True`, `WEBHOOK_BASE_URL`, `WEBHOOK_SECRET`.
- **Recommended stack**: Nginx or Traefik → Luka Bot (aiohttp webhook) → Redis/Elasticsearch.

### Container Orchestration
- Build containers from the provided `Dockerfile`.
- Supply `BOT_TOKEN`, Redis, and provider credentials via environment variables or secrets.
- Mount `/usr/src/app/luka_bot/locales` as read-only in production; publish `/metrics` over an internal network.

## Observability

### Metrics
- Endpoint: `/metrics` (shared with webhook server or standalone aiohttp app in polling mode).
- Key metrics:
  - `luka_updates_total{type}` – processed updates by update type.
  - `luka_llm_request_seconds_bucket` – latency histogram per provider.
  - `luka_workflow_active_total` – active Camunda workflows tracked.
- Scrape via Prometheus (compose file provides scaffolding). Integrate dashboards in Grafana using the sample configs in `configs/grafana`.

### Logging
- Structured via Loguru; default stdout sink.
- Recommended practice: set `LOGURU_LEVEL=INFO` in production and direct stdout to your logging stack (ELK, Loki, etc.).
- Sensitive fields (tokens, secrets) are redacted before logging; custom sinks should preserve this behaviour.

### Alerts
- Wire Sentry (`SENTRY_DSN`) for exception reporting.
- Add Prometheus alert rules for:
  - sustained webhook errors,
  - LLM provider fallback lasting >5 minutes,
  - Redis connection failures,
  - workflow queue backlog growth.

## Security
- **Secrets management**: inject tokens using secret stores (Vault, AWS Secrets Manager) and map them to environment variables.
- **Password gate**: enable `LUKA_PASSWORD_ENABLED` and set `LUKA_PASSWORD` for restricted beta environments.
- **Rate limiting**: adjust `RATE_LIMIT` and integrate with Telegram flood controls for public deployments.
- **Data retention**: configure S3 lifecycle policies for knowledge-base attachments and ensure Elasticsearch indices have retention windows aligned with compliance requirements.

## Upgrade Playbook
1. **Prep**
   - Freeze inbound updates with `/reset` or by disabling webhook.
   - Snapshot Redis (if persistence enabled) and ensure S3 versioning is active.
2. **Deploy**
   - Build new container or pull latest image.
   - Run database migrations (Alembic) if gateway components changed.
   - Warm workflow caches (`workflow_service.initialize()`).
3. **Verify**
   - Check `/metrics` for `luka_handlers_success_total`.
   - Run smoke tests: `/start`, `/groups`, knowledge search, workflow launch.
   - Confirm LLM provider status log shows healthy provider.
4. **Resume**
   - Re-enable webhook or resume polling.
   - Monitor for anomalies for 30 minutes.

## Incident Response
- **LLM provider outage**: Fallback automatically shifts from Ollama to OpenAI. If both fail, handlers send apologetic fallback message; monitor `luka_llm_provider_health` logs and rotate API keys if needed.
- **Redis failure**: Bot continues serving stateless commands but loses FSM/thread state. Restore Redis and restart Luka to rehydrate caches.
- **Flow API downtime**: JWT acquisition fails gracefully; workflows pause. Operators can use the Atlas UI to recover tasks once service resumes.
- **Camunda errors**: Workflow handlers capture REST exceptions and notify moderators. Inspect `camunda_client` logs, replay messages using `/tasks` once resolved.

## Backups & Data Hygiene
- **Redis**: enable snapshotting to retain thread state; for stateless deployments, rely on knowledge base rehydration instead.
- **Elasticsearch**: use snapshot lifecycle policies to archive indexed documents; configure index templates for retention.
- **S3**: apply bucket policies for encryption and lifecycle cleanup of orphaned files.

## Compliance Notes
- Ensure GDPR/PII handling aligns with SOL Atlas policies; knowledge ingestion filters should exclude regulated content.
- Keep audit logs for moderation actions by forwarding relevant Loguru events to your SIEM.
- Document consent flows in onboarding workflows when capturing user-provided data via Camunda forms.
