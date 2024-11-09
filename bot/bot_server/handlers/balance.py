from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from bot_server.keyboards.inline.balance_keyboard import balance_keyboard
from bot_server.services.blockchain import get_balance

router = Router()


@router.callback_query(F.data.startswith("burn_balance"))
async def burn_balance_callback(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    user_info = user_data.get("user")
    wallets = user_info.get("web3_wallets", [])
    if not wallets:
        await callback_query.message.answer("No wallet addresses found")
        return callback_query.message.answer("No wallet addresses found attached")
    wallet_address = wallets[-1]["wallet_address"]
    balance = await get_balance(wallet_address)
    await callback_query.message.answer(
        f"@{callback_query.from_user.username} Your BURNS balance: {round(balance / 1e18, 2)} 🔥",
        reply_markup=await balance_keyboard(wallet_address, bot=callback_query.bot, ref=user_info.get("id")),
    )
