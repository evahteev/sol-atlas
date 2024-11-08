import asyncio
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.deep_linking import create_start_link
from aiogram import Bot


async def balance_keyboard(wallet_address: str, bot: Bot, ref: str) -> InlineKeyboardMarkup:
    kb_wallet = InlineKeyboardButton(
        text="⛓ Check your wallet on Guru Network",
        url=f"https://scan.gurunetwork.ai/address/{wallet_address}",
    )

    start_link = await create_start_link(bot, f"ref:{ref}", encode=True)

    kb_share_bot = InlineKeyboardButton(
        text="🎁 Invite & Get more BURNS!",
        url=f"https://t.me/share/url?url={start_link if start_link else ''}",
    )

    return InlineKeyboardMarkup(inline_keyboard=[[kb_wallet], [kb_share_bot]], resize_keyboard=True)
