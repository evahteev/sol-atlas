from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.deep_linking import create_start_link

from bot_server.core.config import settings


async def main_keyboard(bot, user_id_no_hyphens: str = None):
    kb_link = InlineKeyboardButton(
        text="🚀 Launch Guru Network App",
        url=f"{settings.TELEGRAM_APP_LINK}?startapp",
    )
    kb1 = [InlineKeyboardButton(text="✨ Generate NFT", callback_data="generate_meme")]
    # kb2 = InlineKeyboardButton(text="💎 My BURNS Balance", callback_data="burn_balance")
    # kb3 = InlineKeyboardButton(text="🔥 Burn / Boost Voting", callback_data="next_meme")
    kb4 = InlineKeyboardButton(text="👥 Join Community", url="https://t.me/dexguru")
    # kb3 = InlineKeyboardButton(text="Vote", callback_data="vote")
    # kb4 = InlineKeyboardButton(text="Invite Friends", callback_data="invite")
    # kb5 = InlineKeyboardButton(text="Leaderboard", callback_data="leaderboard")
    # kb6 = InlineKeyboardButton(text="Quests", callback_data="quests")

    # kb_add_to_group = InlineKeyboardButton(
    #     text="🤖 Add Bot to Your Group",
    #     url=f"https://t.me/{settings.TELEGRAM_BOT_NAME}?startgroup=true",
    # )
    start_link = await create_start_link(bot, f"ref{user_id_no_hyphens}", encode=False)
    kb_share_bot = InlineKeyboardButton(
        text="🎁 Share referral link & Get GURU!",
        url=f"https://t.me/share/url?url={start_link}",
    )
    # quests_button = InlineKeyboardButton(text="🎮 Quests", callback_data="quests_list")
    # button_line1 = [kb1]
    button_line2 = [kb_share_bot]
    # button_line3 = [kb_add_to_group, kb_share_bot]
    # button_line4 = [quests_button]
    launch_app = [kb_link]
    new_project_kb = [
        InlineKeyboardButton(
            text="Create New Project",
            callback_data="new_project",
        )
    ]
    main_kb = InlineKeyboardMarkup(
        inline_keyboard=[launch_app, button_line2, kb1, new_project_kb],
        resize_keyboard=True,
    )
    return main_kb
