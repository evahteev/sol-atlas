from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot_server.core.config import settings


def review_meme_keyboard(form_key: str):
    buttons = [
        # [
        #     InlineKeyboardButton(
        #         text="✨ Generate New Meme",
        #         callback_data="generate_meme",
        #     ),
        #     InlineKeyboardButton(
        #         text="🔄 Regenerate",
        #         callback_data=f"regenerate_meme:{form_key}",
        #     )
        # ],
        [
            InlineKeyboardButton(
                text="Go to App for mint", url=f"{settings.TELEGRAM_APP_LINK}?startapp"
            )
        ],
        # [
        #     InlineKeyboardButton(
        #         text="🔄 Regenerate",
        #         callback_data=f"regenerate_meme:{form_key}",
        #     )
        # ],
        # [
        #     InlineKeyboardButton(
        #         text="📝 Change Name!",
        #         callback_data=f"change_meme_name:{form_key}",
        #     ),
        #     InlineKeyboardButton(
        #         text="📝 Change Description!",
        #         callback_data=f"change_meme_description:{form_key}",
        #     )
        # ],
        # [
        #     InlineKeyboardButton(
        #         text="❓ How Voting Works",
        #         callback_data="how_voting_works",
        #     )
        # ],
    ]
    keyboard = InlineKeyboardBuilder(markup=buttons)
    return keyboard.as_markup()
