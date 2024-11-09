from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
)


def main_keyboard() -> ReplyKeyboardMarkup:
    """Use in main menu."""

    buttons = []
    buttons.append(
        [
            KeyboardButton(
                text="Generate Meme",
                callback_data=f"generate_meme",
            )
        ]
    )

    keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

    # keyboard.adjust(1, 1, 2)

    return keyboard
