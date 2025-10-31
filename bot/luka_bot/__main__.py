"""
luka_bot entry point
"""
import asyncio
from loguru import logger

# luka_bot core
from luka_bot.core.config import settings
from luka_bot.core.loader import app, bot, dp

# handlers
from luka_bot.handlers import get_llm_bot_router
from luka_bot.keyboards.default_commands import set_default_commands
from luka_bot.middlewares.i18n_middleware import UserProfileI18nMiddleware
from luka_bot.middlewares.form_input_middleware import FormInputMiddleware

# Webhook setup - import at module level for use in setup_webhook()
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from luka_bot.handlers.metrics import MetricsView
from luka_bot.middlewares.prometheus import prometheus_middleware_factory

# Global metrics server state (for polling mode)
_metrics_server_task = None
_metrics_runner = None


async def start_metrics_server() -> None:
    """
    Start a separate metrics server for polling mode.
    In webhook mode, metrics are served on the webhook port.
    """
    global _metrics_server_task, _metrics_runner
    
    if not settings.METRICS_ENABLED:
        logger.info("ℹ️  Metrics disabled (METRICS_ENABLED=False)")
        return
    
    if settings.USE_WEBHOOK:
        # In webhook mode, metrics are served on the webhook server
        # No need for separate server
        return
    
    logger.info(f"📊 Starting metrics server on {settings.METRICS_HOST}:{settings.METRICS_PORT}...")
    
    try:
        # Create a simple aiohttp app for metrics only
        metrics_app = web.Application()
        metrics_app.middlewares.append(prometheus_middleware_factory())
        metrics_app.router.add_route("GET", "/metrics", MetricsView)
        
        # Use AppRunner for graceful lifecycle management
        _metrics_runner = web.AppRunner(metrics_app)
        await _metrics_runner.setup()
        
        site = web.TCPSite(
            _metrics_runner,
            host=settings.METRICS_HOST,
            port=settings.METRICS_PORT
        )
        await site.start()
        
        logger.info(f"✅ Metrics server started on http://{settings.METRICS_HOST}:{settings.METRICS_PORT}/metrics")
        logger.info("   Prometheus can scrape metrics from this endpoint")
        
    except OSError as e:
        if "Address already in use" in str(e):
            logger.error(f"❌ Port {settings.METRICS_PORT} is already in use")
            logger.error("   Change METRICS_PORT in .env or disable METRICS_ENABLED")
        else:
            logger.error(f"❌ Failed to start metrics server: {e}")
    except Exception as e:
        logger.error(f"❌ Failed to start metrics server: {e}", exc_info=True)


async def stop_metrics_server() -> None:
    """Stop the metrics server (polling mode only)."""
    global _metrics_runner
    
    if _metrics_runner is None:
        return
    
    logger.info("🛑 Stopping metrics server...")
    
    try:
        await _metrics_runner.cleanup()
        _metrics_runner = None
        logger.info("✅ Metrics server stopped")
    except Exception as e:
        logger.error(f"❌ Failed to stop metrics server: {e}", exc_info=True)


async def on_startup() -> None:
    """Bot startup initialization."""
    logger.info("🚀 luka_bot starting...")
    
    # Initialize and check LLM providers
    try:
        from luka_bot.services.llm_provider_fallback import get_llm_provider_fallback
        fallback = get_llm_provider_fallback()
        
        # Perform unified startup check
        result = await fallback.initialize_on_startup()
        
        # Log provider availability
        if result["stats"]:
            stats = result["stats"]
            logger.info("")
            logger.info("🔍 LLM Provider Status:")
            logger.info(f"   Primary: {stats['primary_provider']}")
            logger.info(f"   Fallback: {stats['fallback_provider']}")
            logger.info("")
            
            for provider_name in fallback.ALL_PROVIDERS:
                health = stats['provider_health'][provider_name]
                status_emoji = "✅" if health['available'] else "❌"
                config_status = "configured" if health['configured'] else "not configured"
                health_status = "healthy" if health['healthy'] else "unhealthy"
                
                logger.info(
                    f"   {status_emoji} {provider_name.upper()}: "
                    f"{config_status}, {health_status}, "
                    f"available={health['available']}"
                )
        
        # Log active provider
        if result["active_provider"]:
            logger.info(f"✅ Active provider: {result['active_provider'].upper()} (cached for 30 minutes)")
        elif result["error"]:
            logger.error(f"❌ No providers available: {result['error']}")
        
    except Exception as e:
        logger.warning(f"⚠️  Failed to initialize LLM providers: {e}")
    
    # Register middlewares (ORDER MATTERS!)
    # 1. Password gate FIRST (if enabled, blocks unauthenticated users)
    if settings.LUKA_PASSWORD_ENABLED:
        from luka_bot.middlewares.password_middleware import PasswordMiddleware
        dp.message.middleware(PasswordMiddleware())
        dp.callback_query.middleware(PasswordMiddleware())
        logger.info("🔒 Password authentication middleware registered")
        logger.info(f"   Password protection: {'ENABLED ✅' if settings.LUKA_PASSWORD else 'ENABLED but NO PASSWORD SET ⚠️'}")
    
    # 2. Flow API auth SECOND (provides user context with Camunda credentials)
    from luka_bot.middlewares.flow_auth_middleware import FlowAuthMiddleware
    dp.message.middleware(FlowAuthMiddleware())
    dp.callback_query.middleware(FlowAuthMiddleware())
    logger.info("🔐 Flow API session-based auth middleware registered")
    
    # 3. Form input guard THIRD (prevents LLM handlers from consuming form messages)
    dp.message.middleware(FormInputMiddleware())
    logger.info("🛡️ Form input guard middleware registered")
    
    # 4. I18n FOURTH (can use user context from auth middleware)
    dp.message.middleware(UserProfileI18nMiddleware())
    dp.callback_query.middleware(UserProfileI18nMiddleware())
    logger.info(f"🌍 I18n middleware registered (default locale: {settings.DEFAULT_LOCALE})")
    
    # Log Privacy Mode status
    privacy_status = "ON (limited visibility)" if settings.BOT_PRIVACY_MODE_ENABLED else "OFF (sees all messages)"
    privacy_emoji = "🔒" if settings.BOT_PRIVACY_MODE_ENABLED else "👁️"
    logger.info(f"{privacy_emoji} Privacy Mode: {privacy_status}")
    
    # Load process definitions from Camunda (if available)
    if settings.CAMUNDA_ENABLED:
        try:
            from luka_bot.services.process_definition_cache import get_process_definition_cache
            from luka_bot.services.user_profile_service import get_user_profile_service

            # Get any valid user ID for loading definitions (use first available user or system user)
            profile_service = get_user_profile_service()

            # Try to get a system/admin user ID from config, or use a default
            # This user ID is only used for authentication, not for filtering
            system_user_id = settings.SYSTEM_USER_ID if hasattr(settings, 'SYSTEM_USER_ID') else 0

            if system_user_id == 0:
                # If no system user configured, get any existing user from profiles
                # This is just for auth - we load ALL process definitions
                logger.debug("No SYSTEM_USER_ID configured, using guest/default user for process definition loading")

            cache = get_process_definition_cache()
            await cache.load_definitions(telegram_user_id=system_user_id)

            if cache.is_loaded():
                chatbot_processes = cache.get_chatbot_processes()
                if chatbot_processes:
                    logger.info(f"✅ Chatbot processes available: {', '.join([p.key for p in chatbot_processes])}")
                else:
                    logger.warning("⚠️  No chatbot_* processes found - chatbot features may be limited")
            else:
                logger.warning("⚠️  Process definitions not loaded - process-based features disabled")

        except Exception as e:
            logger.warning(f"⚠️  Failed to load process definitions: {e}")
            logger.info("   Bot will continue without process-based features")
    else:
        logger.info("ℹ️  Camunda integration disabled (CAMUNDA_ENABLED=False)")
        logger.info("   Process-based features will not be available")

    # Register handlers
    dp.include_router(get_llm_bot_router())
    logger.info("📦 Handlers registered")

    # Start metrics server (polling mode only)
    # In webhook mode, metrics are served on the same port as webhook
    await start_metrics_server()
    
    # Start AG-UI Gateway server (if enabled)
    # In webhook mode: AG-UI was already mounted in setup_webhook() before aiogram setup
    # In polling mode: Start separate AG-UI server on port 8000
    if settings.AG_UI_ENABLED and not settings.USE_WEBHOOK:
        from luka_bot.core.ag_ui_integration import start_ag_ui_server
        await start_ag_ui_server(webhook_app=None)  # None = polling mode, separate server
    
    # Set default commands for the command menu
    logger.info("")
    logger.info("📋 Configuring default commands...")
    await set_default_commands(bot)
    
    # Display summary of configured commands
    from luka_bot.keyboards.default_commands import (
        private_commands_by_language,
        group_commands_by_language,
        admin_commands_by_language,
    )
    
    logger.info("")
    logger.info("📋 Command Summary:")
    logger.info("   Private Chats:")
    # Filter by LUKA_COMMANDS_ENABLED
    enabled_commands = settings.LUKA_COMMANDS_ENABLED
    for cmd in private_commands_by_language["en"].keys():
        if cmd in enabled_commands:
            logger.info(f"      /{cmd}")
    
    # Show disabled commands
    disabled_commands = [cmd for cmd in private_commands_by_language["en"].keys() if cmd not in enabled_commands]
    if disabled_commands:
        logger.info("   Disabled Commands:")
        for cmd in disabled_commands:
            logger.info(f"      /{cmd} (configure via LUKA_COMMANDS_ENABLED)")
    
    logger.info("   Groups:")
    for cmd in group_commands_by_language["en"].keys():
        logger.info(f"      /{cmd}")
    
    logger.info("   Group Admins (additional):")
    admin_only = set(admin_commands_by_language["en"].keys()) - set(group_commands_by_language["en"].keys())
    for cmd in admin_only:
        logger.info(f"      /{cmd}")
    
    logger.info("   Supported languages: en, ru")
    
    # Get bot info
    bot_info = await bot.get_me()
    logger.info(f"✅ Bot: {bot_info.full_name} (@{bot_info.username}, ID: {bot_info.id})")
    
    # Initialize WebSocket manager (if enabled)
    if settings.WAREHOUSE_ENABLED:
        try:
            from luka_bot.services.task_websocket_manager import get_websocket_manager
            ws_manager = get_websocket_manager()
            
            logger.info("")
            logger.info("🔌 WebSocket Task Notifications:")
            logger.info(f"   Warehouse URL: {settings.WAREHOUSE_WS_URL}")
            logger.info("   Per-user connections will be established on first interaction")
            logger.info("   Real-time task notifications enabled ✅")
            
        except Exception as e:
            logger.warning(f"⚠️  WebSocket manager initialization failed: {e}")
            logger.warning("   Bot will fall back to polling mode")
    else:
        logger.info("")
        logger.info("ℹ️  WebSocket disabled (WAREHOUSE_ENABLED=False)")
        logger.info("   Using polling mode for task detection")
    
    # Log metrics availability summary
    if settings.METRICS_ENABLED:
        logger.info("")
        logger.info("📊 Prometheus Metrics Summary:")
        if settings.USE_WEBHOOK:
            logger.info(f"   Mode: Webhook (same port as bot)")
            logger.info(f"   URL: http://{settings.WEBHOOK_HOST}:{settings.WEBHOOK_PORT}/metrics")
        else:
            logger.info(f"   Mode: Polling (separate metrics server)")
            logger.info(f"   URL: http://{settings.METRICS_HOST}:{settings.METRICS_PORT}/metrics")
        logger.info("   Status: Ready for Prometheus scraping ✅")
    
    logger.info("")
    logger.info("✅ luka_bot started successfully")


async def on_shutdown() -> None:
    """Bot shutdown cleanup."""
    logger.info("🛑 luka_bot stopping...")
    
    # Cancel all background tasks (Moderation)
    try:
        from luka_bot.utils.background_tasks import cancel_all_background_tasks
        await cancel_all_background_tasks()
    except Exception as e:
        logger.warning(f"⚠️ Error cancelling background tasks: {e}")
    
    # Shutdown WebSocket manager
    if settings.WAREHOUSE_ENABLED:
        try:
            from luka_bot.services.task_websocket_manager import shutdown_websocket_manager
            await shutdown_websocket_manager()
            logger.info("✅ WebSocket manager shut down")
        except Exception as e:
            logger.warning(f"⚠️  Error shutting down WebSocket manager: {e}")
    
    # Stop metrics server (polling mode only)
    await stop_metrics_server()
    
    # Stop AG-UI Gateway server (if enabled)
    if settings.AG_UI_ENABLED:
        try:
            from luka_bot.core.ag_ui_integration import stop_ag_ui_server
            await stop_ag_ui_server()
        except Exception as e:
            logger.warning(f"⚠️  Error stopping AG-UI server: {e}")
    
    # Close bot session
    await bot.session.close()
    
    # Close storage
    await dp.storage.close()
    await dp.fsm.storage.close()
    
    logger.info("✅ luka_bot stopped")


async def setup_webhook() -> None:
    """Setup webhook for production (Phase 8)."""
    webhook_url = settings.webhook_url
    logger.info(f"Setting up webhook: {webhook_url}")

    # CRITICAL: Route registration order matters in aiohttp!
    # Specific routes MUST be registered before catch-all routes.
    #
    # Correct order:
    # 1. Metrics (specific: /metrics)
    # 2. Webhook handler (specific: /webhook or configured path)
    # 3. AG-UI catch-all (last: /* catches everything else)

    # Step 1: Initialize AG-UI (starts internal server, returns proxy handler)
    ag_ui_proxy_handler = None
    if settings.AG_UI_ENABLED:
        logger.info("🔧 Initializing AG-UI Gateway...")
        from luka_bot.core.ag_ui_integration import mount_ag_ui_on_webhook
        ag_ui_proxy_handler = await mount_ag_ui_on_webhook(app)

    # Step 2: Setup metrics endpoint (specific route)
    if settings.METRICS_ENABLED:
        logger.info("📊 Setting up Prometheus metrics...")
        app.middlewares.append(prometheus_middleware_factory())
        app.router.add_route("GET", "/metrics", MetricsView)
        logger.info("✅ Metrics endpoint registered at /metrics")
    else:
        logger.info("ℹ️  Metrics disabled (METRICS_ENABLED=False)")

    # Step 3: Register webhook handler (specific route)
    await bot.set_webhook(
        url=webhook_url,
        drop_pending_updates=True,
        secret_token=settings.WEBHOOK_SECRET
    )

    webhook_request_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=settings.WEBHOOK_SECRET,
    )
    webhook_request_handler.register(app, path=settings.WEBHOOK_PATH)
    logger.info(f"✅ Telegram webhook registered at {settings.WEBHOOK_PATH}")

    # Step 4: Setup aiogram application lifecycle
    setup_application(app, dp, bot=bot)

    # Step 5: Register AG-UI catch-all proxy LAST (after all specific routes)
    if ag_ui_proxy_handler is not None:
        app.router.add_route("*", "/{path_info:.*}", ag_ui_proxy_handler, name="ag_ui_proxy")
        logger.info("✅ AG-UI catch-all proxy registered (handles all non-webhook/metrics routes)")
        logger.info("📌 Route priority: /metrics → /webhook → /* (AG-UI)")

    # Log all registered routes for verification
    logger.info("")
    logger.info("🗺️  Registered routes on webhook server:")
    for route in app.router.routes():
        route_info = route.resource
        if hasattr(route_info, 'canonical'):
            logger.info(f"   {route.method:6s} {route_info.canonical}")
        else:
            logger.info(f"   {route.method:6s} {route_info}")
    logger.info("")
    
    # Use AppRunner instead of run_app to avoid nested event loop
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=settings.WEBHOOK_HOST, port=settings.WEBHOOK_PORT)
    await site.start()
    
    logger.info(f"🌐 Webhook server started on {settings.WEBHOOK_HOST}:{settings.WEBHOOK_PORT}")
    
    # Keep the server running indefinitely
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 Received exit signal")
    finally:
        await runner.cleanup()


async def main() -> None:
    """Main entry point."""
    # Register startup/shutdown handlers
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    if settings.USE_WEBHOOK:
        # setup_application() will automatically call registered startup/shutdown handlers
        await setup_webhook()
    else:
        # Delete webhook and start polling (Phase 1)
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("📡 Using polling mode")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
