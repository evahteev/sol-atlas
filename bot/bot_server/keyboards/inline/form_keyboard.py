from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def form_keyboard(variables: list[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for var in variables:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f'✍️ {var["label"]}',
                    callback_data=f'form:{var["name"]}:{var["label"]}',
                )
            ]
        )
    buttons.append(
        [
            InlineKeyboardButton(
                text="✅ Complete",
                callback_data=f"form_complete",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons, resize_keyboard=True)
