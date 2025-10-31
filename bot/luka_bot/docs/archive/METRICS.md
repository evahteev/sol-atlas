# Prometheus Metrics for Luka Bot

This document describes the Prometheus metrics endpoint for monitoring Luka bot.

## Overview

The `/metrics` endpoint provides Prometheus-compatible metrics for monitoring bot performance, usage, and health. This endpoint is **available in both webhook and polling modes**.

### Webhook Mode
- Metrics are served on the **same port** as the webhook handler
- Default: `http://0.0.0.0:8080/metrics`

### Polling Mode
- Metrics are served on a **separate port** (default: 9090)
- Default: `http://0.0.0.0:9090/metrics`

## Accessing Metrics

### Webhook Mode (`USE_WEBHOOK=true`)
```
http://<WEBHOOK_HOST>:<WEBHOOK_PORT>/metrics
```
Default: `http://0.0.0.0:8080/metrics`

### Polling Mode (`USE_WEBHOOK=false`)
```
http://<METRICS_HOST>:<METRICS_PORT>/metrics
```
Default: `http://0.0.0.0:9090/metrics`

## Configuration

### Basic Configuration

```bash
# Enable/disable metrics (enabled by default)
METRICS_ENABLED=true
```

### Webhook Mode Configuration

Set these environment variables in your `.env` file:

```bash
# Enable webhook mode
USE_WEBHOOK=true

# Webhook configuration
WEBHOOK_BASE_URL=https://your-domain.com  # Public URL for Telegram webhooks
WEBHOOK_PATH=/webhook                      # Path for webhook endpoint
WEBHOOK_SECRET=your-secret-token           # Secret for webhook validation

# Local server binding (for metrics and webhook handler)
WEBHOOK_HOST=0.0.0.0  # Bind to all interfaces (or use "localhost" for local only)
WEBHOOK_PORT=8080      # Port for HTTP server

# Metrics will be available at http://0.0.0.0:8080/metrics
```

### Polling Mode Configuration

```bash
# Use polling mode (default)
USE_WEBHOOK=false

# Metrics server configuration (polling mode only)
METRICS_ENABLED=true      # Enable metrics endpoint
METRICS_HOST=0.0.0.0      # Bind to all interfaces
METRICS_PORT=9090         # Separate port for metrics

# Metrics will be available at http://0.0.0.0:9090/metrics
```

**Important:** `WEBHOOK_HOST` and `METRICS_HOST` must be a hostname or IP address (e.g., `0.0.0.0`, `localhost`, `127.0.0.1`), **not a full URL**.

## Available Metrics

### HTTP Request Metrics (Middleware)

These metrics track all HTTP requests to the webhook server:

- **`luka_bot_requests`** (Counter)
  - Total requests by method, scheme, remote, and path template
  - Labels: `method`, `scheme`, `remote`, `path_template`

- **`luka_bot_responses`** (Counter)
  - Total responses by method, scheme, remote, path template, and status code
  - Labels: `method`, `scheme`, `remote`, `path_template`, `status_code`

- **`luka_bot_request_duration`** (Histogram)
  - Request processing time in seconds
  - Labels: `method`, `scheme`, `remote`, `path_template`, `status_code`

- **`luka_bot_requests_in_progress`** (Gauge)
  - Number of requests currently being processed
  - Labels: `method`, `scheme`, `remote`, `path_template`

- **`luka_bot_exceptions`** (Counter)
  - Total exceptions raised during request processing
  - Labels: `method`, `scheme`, `remote`, `path_template`, `exception_type`

### Bot-Specific Metrics

These metrics track bot-specific operations:

- **`luka_bot_messages_total`** (Counter)
  - Total messages processed by the bot
  - Labels: `chat_type`, `handler`

- **`luka_bot_commands_total`** (Counter)
  - Total commands executed
  - Labels: `command`

- **`luka_bot_threads_total`** (Gauge)
  - Total number of conversation threads
  - Labels: `user_id`

- **`luka_bot_active_users`** (Gauge)
  - Number of active bot users

- **`luka_bot_response_time_seconds`** (Histogram)
  - Bot response time in seconds
  - Labels: `handler`

### LLM Metrics

Track LLM/AI model usage:

- **`luka_bot_llm_requests_total`** (Counter)
  - Total LLM requests
  - Labels: `model`, `provider`, `status`

- **`luka_bot_llm_response_time_seconds`** (Histogram)
  - LLM response time in seconds
  - Labels: `model`, `provider`

### Knowledge Base Metrics

Track knowledge base searches:

- **`luka_bot_kb_searches_total`** (Counter)
  - Total knowledge base searches
  - Labels: `kb_type`, `status`

- **`luka_bot_kb_search_time_seconds`** (Histogram)
  - Knowledge base search time in seconds
  - Labels: `kb_type`

### YouTube Metrics

Track YouTube transcript requests:

- **`luka_bot_youtube_transcripts_total`** (Counter)
  - Total YouTube transcript requests
  - Labels: `status`

## Using Metrics

### Example: Prometheus Configuration

Add this to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'luka_bot'
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:8080']
    metrics_path: /metrics
```

### Example: Grafana Queries

**Average LLM Response Time:**
```promql
rate(luka_bot_llm_response_time_seconds_sum[5m]) / rate(luka_bot_llm_response_time_seconds_count[5m])
```

**Messages Per Second:**
```promql
rate(luka_bot_messages_total[1m])
```

**Request Success Rate:**
```promql
sum(rate(luka_bot_responses{status_code=~"2.."}[5m])) / sum(rate(luka_bot_responses[5m]))
```

**Active Users:**
```promql
luka_bot_active_users
```

## Instrumenting Your Code

To add custom metrics tracking in your handlers:

```python
from luka_bot.handlers.metrics import (
    bot_commands_total,
    bot_llm_requests_total,
    bot_response_time
)

# Count command execution
bot_commands_total.labels(command="start").inc()

# Track LLM requests
bot_llm_requests_total.labels(model="llama3.2", provider="ollama", status="success").inc()

# Measure response time
with bot_response_time.labels(handler="chat").time():
    # Your handler code here
    pass
```

## Architecture

The metrics implementation consists of:

1. **`luka_bot/handlers/metrics.py`** - MetricsView handler and metric definitions
2. **`luka_bot/middlewares/prometheus.py`** - Prometheus middleware for HTTP tracking
3. **`luka_bot/__main__.py`** - Integration into bot startup

The middleware automatically tracks all HTTP requests, while bot-specific metrics need to be manually instrumented in handlers.

## Troubleshooting

### Metrics endpoint not available

- Ensure `USE_WEBHOOK=true` in your `.env` file
- Check that the bot is running in webhook mode
- Verify `WEBHOOK_HOST` and `WEBHOOK_PORT` are correctly configured

### "label empty or too long" error

- Make sure `WEBHOOK_HOST` is set to a hostname or IP (e.g., `0.0.0.0`, `localhost`)
- Do NOT use a full URL (e.g., `https://example.com`) for `WEBHOOK_HOST`

### Metrics not updating

- Check logs for any errors during metric recording
- Ensure handlers are properly instrumented
- Verify Prometheus is successfully scraping the endpoint

## Security Considerations

The `/metrics` endpoint is publicly accessible when running in webhook mode. Consider:

- Running behind a reverse proxy (nginx, Caddy) with authentication
- Using firewall rules to restrict access to the metrics endpoint
- Only exposing metrics on localhost and using SSH tunneling for remote access

## See Also

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Dashboards](https://grafana.com/docs/)
- [Python Prometheus Client](https://github.com/prometheus/client_python)

