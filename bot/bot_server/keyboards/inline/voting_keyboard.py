from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from urllib.parse import quote_plus

from bot_server.core.config import settings
from bot_server.utils.common import remove_hyphens_from_uuid


def voting_started_keyboard(art_id: str, minted: int = 0, burned: int = 0):
    art = remove_hyphens_from_uuid(art_id)
    url = f"{settings.TELEGRAM_APP_LINK}?startapp=gen{art}"
    base_message = "Check out this meme!"
    encoded_base_message = quote_plus(base_message)

    share_url = f"https://t.me/share/url?url={url}&text={encoded_base_message}"

    voting_started_buttons = [
        [
            InlineKeyboardButton(
                text="🚀 Open App and Booost Your Meme",
                url=url,
            ),
        ],
        [
            InlineKeyboardButton(
                text="🔗 Share Link to this meme",
                url=share_url,
            ),
        ],
        # [
        #     InlineKeyboardButton(
        #         text="⛔️ Vote Burn 100 🔥",
        #         callback_data=f"vote:burns:{art_id}",
        #     ),
        #     InlineKeyboardButton(
        #         text="✅ Vote Boost 100 🔥",
        #         callback_data=f"vote:mints:{art_id}",
        #     ),
        # ],
        # [
        #     InlineKeyboardButton(
        #         text="❓ How Voting Works",
        #         callback_data="how_voting_works",
        #     ),
        #     InlineKeyboardButton(
        #         text="🎲 Next Meme",
        #         callback_data="next_meme",
        #     ),
        # ],
    ]
    if minted > 0 or burned > 0:
        voting_started_buttons.append(
            [
                InlineKeyboardButton(
                    text=f"Burned: {burned}",
                    url=url,
                ),
                InlineKeyboardButton(
                    text=f"Boosted: {minted}",
                    url=url,
                ),
            ],
        )
    voting_started_kb = InlineKeyboardBuilder(markup=voting_started_buttons).as_markup()
    return voting_started_kb


def voting_ended_keyboard(art_id: str):
    art = remove_hyphens_from_uuid(art_id)
    url = f"{settings.TELEGRAM_APP_LINK}?startapp=gen{art}"

    voting_ended_button = [
        [
            InlineKeyboardButton(
                text="Check Meme",
                url=url,
            ),
        ]
    ]
    voting_ended_kb = InlineKeyboardBuilder(markup=voting_ended_button).as_markup()
    return voting_ended_kb
