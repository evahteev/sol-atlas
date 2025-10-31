"""
Prometheus metrics handler for Luka bot monitoring.
Provides metrics endpoint for Prometheus scraping.
"""

import prometheus_client
from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from loguru import logger


class MetricsView(web.View):
    """HTTP endpoint for Prometheus metrics collection."""
    
    def __init__(
        self, request: Request, registry: prometheus_client.CollectorRegistry = prometheus_client.REGISTRY
    ) -> None:
        self._request = request
        self.registry = registry

    async def get(self) -> Response:
        """Return current metrics in Prometheus format."""
        try:
            metrics_data = prometheus_client.generate_latest(self.registry)
            response = Response(body=metrics_data)
            response.content_type = prometheus_client.CONTENT_TYPE_LATEST
            # Removed debug log to reduce noise (metrics scraped every ~30s)
            return response
        except Exception as e:
            logger.error(f"Error generating metrics: {e}")
            return Response(text=f"Error generating metrics: {str(e)}", status=500)


# Define custom metrics for Luka bot monitoring
bot_messages_total = prometheus_client.Counter(
    'luka_bot_messages_total', 
    'Total number of messages processed by the bot',
    ['chat_type', 'handler']
)

bot_commands_total = prometheus_client.Counter(
    'luka_bot_commands_total',
    'Total number of commands executed',
    ['command']
)

bot_threads_total = prometheus_client.Gauge(
    'luka_bot_threads_total',
    'Total number of conversation threads',
    ['user_id']
)

bot_active_users = prometheus_client.Gauge(
    'luka_bot_active_users',
    'Number of active bot users'
)

bot_response_time = prometheus_client.Histogram(
    'luka_bot_response_time_seconds',
    'Bot response time in seconds',
    ['handler']
)

bot_llm_requests_total = prometheus_client.Counter(
    'luka_bot_llm_requests_total',
    'Total number of LLM requests',
    ['model', 'provider', 'status']
)

bot_llm_response_time = prometheus_client.Histogram(
    'luka_bot_llm_response_time_seconds',
    'LLM response time in seconds',
    ['model', 'provider']
)

bot_kb_searches_total = prometheus_client.Counter(
    'luka_bot_kb_searches_total',
    'Total number of knowledge base searches',
    ['kb_type', 'status']
)

bot_kb_search_time = prometheus_client.Histogram(
    'luka_bot_kb_search_time_seconds',
    'Knowledge base search time in seconds',
    ['kb_type']
)

bot_youtube_transcripts_total = prometheus_client.Counter(
    'luka_bot_youtube_transcripts_total',
    'Total number of YouTube transcript requests',
    ['status']
)


def setup_metrics_endpoint(app: web.Application, path: str = '/metrics'):
    """Setup the metrics endpoint in the web application."""
    app.router.add_view(path, MetricsView)
    logger.info(f"Metrics endpoint configured at {path}")

