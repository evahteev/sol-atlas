"""
luka_bot loader - bot, dispatcher, and i18n initialization.

Completely independent from bot_server.
"""
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import DefaultKeyBuilder, RedisStorage
from aiogram.utils.i18n.core import I18n
from aiohttp import web
from redis.asyncio import ConnectionPool, Redis

from luka_bot.core.config import I18N_DOMAIN, LOCALES_DIR, settings

# AIOHTTP app for webhook (Phase 1: not used, but prepared for Phase 8)
app = web.Application()

# Telegram Bot
bot = Bot(
    token=settings.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)

# Redis client for FSM storage
redis_client = Redis(
    connection_pool=ConnectionPool(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASS,
        db=settings.REDIS_DATABASE,
        retry_on_timeout=True,
        retry_on_error=[
            ConnectionError,
            TimeoutError,
            ConnectionResetError,
            ConnectionRefusedError,
            ConnectionAbortedError,
        ],
        health_check_interval=30,
    ),
)

# Redis-based FSM storage
storage = RedisStorage(
    redis=redis_client,
    key_builder=DefaultKeyBuilder(with_bot_id=True),
)

# Dispatcher
dp = Dispatcher(storage=storage)

# I18n (internationalization)
i18n: I18n = I18n(path=LOCALES_DIR, default_locale=settings.DEFAULT_LOCALE, domain=I18N_DOMAIN)

# Debug flag
DEBUG = settings.DEBUG
