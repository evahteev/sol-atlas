import asyncio
import logging
import re

import httpx
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, ForceReply, Message
from eth_utils import is_checksum_address

from bot_server.core.config import settings
from bot_server.handlers.tasks import (
    fetch_camunda_tasks,
    get_task,
    get_task_form_variables,
    complete_task,
)
from bot_server.handlers.user_inputs import (
    start_process_instance,
    download_telegram_photo,
    upload_file_to_s3_binary,
)
from bot_server.keyboards.inline.review_meme import review_meme_keyboard
from camunda_client import CamundaEngineClient
from camunda_client.clients.dto import AuthData
from camunda_client.clients.engine.schemas import ProcessInstanceQuerySchema
from flow_client import FlowClient

router = Router()


class Form(StatesGroup):
    waiting_for_input = State()
    prompt_for_meme = State()


def reply_prompt_filter(message: types.Message):
    return (
        message.reply_to_message
        and message.reply_to_message.text
        and message.reply_to_message.text.endswith("Wallet address 0x...")
    )


@router.callback_query(F.data.startswith("faucet"))
async def generate_meme_callback(callback_query: CallbackQuery, state: FSMContext):
    """Generate meme callback. Ask user for the prompt."""
    await state.set_state(Form.prompt_for_meme)
    username = f'@{callback_query.from_user.username}' if callback_query.from_user.username else ""
    await callback_query.message.answer(
        f"Hey {username}! To Get 100 XFI Testnet Tokens just reply with your EVM Wallet address 0x...",
        reply_markup=ForceReply(selective=True),
    )


@router.message(Command(commands=["faucet"]))
async def generate_meme_callback(message: Message, state: FSMContext):
    """Generate meme callback. Ask user for the prompt."""
    await state.set_state(Form.prompt_for_meme)
    username = f'@{message.from_user.username}' if message.from_user.username else ""
    await message.answer(
        f"Hey {username}! To Get 100 XFI Testnet Tokens just reply with your EVM Wallet address 0x...",
        reply_markup=ForceReply(selective=True),
    )


async def post_art_details(img_art_thumbnail: str, art_details: dict):
    """Post the art details to the API."""
    async with httpx.AsyncClient() as client:
        headers = {
            "Content-Type": "application/json",
            "X-SYS-KEY": settings.FLOW_SYS_KEY,
        }
        art_details["img_picture"] = img_art_thumbnail

        response = await client.post(
            f"{settings.FLOW_API}/api/art", json=art_details, headers=headers
        )
        if response.status_code >= 400:
            error_msg = f"HTTP error response: {response.status_code} {response.text}"
            logging.error(error_msg)
            raise Exception(error_msg)

        logging.info(f"Art operation response status code: {response.status_code}")
        logging.info(f"Art operation response body: {response.text}")
        return response.json()


@router.message(reply_prompt_filter)
async def events_handler(
    message: types.Message,
    state: FSMContext,
    prompt: str = None,
):
    msg = await message.answer("Sending Tokens...")
    try:
        user_data = await state.get_data()
        user_info = user_data.get("user")
        camunda_user_id = user_info.get("camunda_user_id")
        if not camunda_user_id:
            await message.answer("You are not registered, /start to register")
            return
        camunda_key = user_info.get("camunda_key")
        business_key = (
            f'{user_info.get("id")}'
        )
        if not prompt:
            prompt = message.text

        src1_art_id = None

        await state.update_data(
            promt=message.text, user=user_info, src1_art_id=src1_art_id
        )
        await message.answer(f"Checking your wallet address {prompt} ...")

        if not is_checksum_address(prompt):
            await message.answer(f"Invalid EVM address {prompt} , please provide a valid EVM address.")
            return

        await message.answer(f"Puring the Faucet into {prompt} ...")

        resulting_variables = [
            {"name": "form_wallet_address", "value": prompt, "type": "String"},
            {"name": "def_rewardAmount", "value": 100, "type": "Long"},
        ]

        logging.info(f"Starting faucet process instance with business key: {business_key}, variables: {resulting_variables}")
        await state.update_data(resulting_variables=resulting_variables)
        async with httpx.AsyncHTTPTransport() as transport:
            camunda_client = CamundaEngineClient(
                auth_data=AuthData(username=camunda_user_id, password=camunda_key),
                base_url=settings.ENGINE_URL,
                transport=transport,
            )
            # Start the process instance with the collected variables
            process_instance = await camunda_client.get_process_instances(
                params=ProcessInstanceQuerySchema(
                    business_key=business_key,
                    process_definition_key="faucet_send",
                )
            )
            await camunda_client.close()
        if process_instance:
            logging.info("Faucet was already used today, please wait 24h.")
            await message.answer(
                "Faucet was already used today, please wait 24h."
            )
            process_instance = process_instance[0]
        else:
            logging.info(
                f"Starting generate process instance with business key: {business_key}"
            )
            process_instance = await start_process_instance(
                state,
                business_key=business_key,
                process_definition_key="faucet_send",
                camunda_user_id=user_info.get("camunda_user_id"),
                camunda_key=user_info.get("camunda_key"),
            )
        process_instance_id = process_instance.id
        while True:
            await message.bot.send_chat_action(
                message.chat.id,
                "upload_photo",
                message_thread_id=message.message_thread_id,
            )
            await asyncio.sleep(5)
            tasks = await fetch_camunda_tasks(
                root_process_instance_id=process_instance_id,
                camunda_user_id=user_info.get("camunda_user_id"),
            )
            generate_task = None
            for task in tasks:
                if (
                    task["task"].task_definition_key
                    == "success_message"
                ):
                    generate_task = task["task"]
                    break
            if generate_task:
                break
        variables = await get_variables_generate_task(generate_task.id, state)
        await state.update_data(resulting_variables=variables)
        tx_hash = await get_txhash_rewards(state)
        await msg.delete()
        caption = f"tx_hash: {tx_hash}\nExplorer link: https://scan.xfi.ms/tx/{tx_hash}"
        await message.answer(caption)
        await complete_task(
            state,
            generate_task.id,
            camunda_user_id,
            camunda_key,
        )
    except Exception as e:
        logging.error(f"Error starting faucet: {e}")
        await message.answer(f"Error sending tokens")


@router.callback_query(F.data.startswith("regenerate_meme"))
async def review_meme_callback(callback_query: CallbackQuery, state: FSMContext):
    """Regenerate meme based on art prompt callback. It starts new process instance."""
    art_id = callback_query.data.split(":")[1]
    async with FlowClient(
        base_url=settings.FLOW_API, sys_key=settings.FLOW_SYS_KEY
    ) as flow_client:
        art = await flow_client.get_art_by_id(art_id)

    await callback_query.message.reply(
    "✨ Your new image is cooking in the meme factory! 🔥 We’ll give you a shout when it’s ready. Stay tuned! 🎨"
    )
    await events_handler(callback_query.message, state, prompt=art.description_prompt)


async def get_txhash_rewards(state: FSMContext):
    data = await state.get_data()
    variables = data.get("resulting_variables", [])
    for variable in variables:
        if variable["name"] == "txhash_rewards":
            txhash_rewards = variable["value"]
            return txhash_rewards


async def get_variables_generate_task(task_id, state: FSMContext):
    task_info, task_variables = await asyncio.gather(
        get_task(task_id, state), get_task_form_variables(task_id, state)
    )
    task_variables_list = []
    task_variables_dict = {}

    for variable in task_variables:
        task_variables_list.append(variable.model_dump())
        task_variables_dict[variable.name] = variable.model_dump()

    data = await state.get_data()
    resulting_variables = data.get("resulting_variables", [])
    resulting_variables_dict = {var["name"]: var for var in resulting_variables}

    for variable in task_variables_list:
        name = variable["name"]
        value = variable["value"]["value"]
        var_type = variable["value"]["type"]
        if var_type == "Boolean":
            value = bool(value)
        if name in resulting_variables_dict:
            # Update the existing variable
            resulting_variables_dict[name]["value"] = value
            resulting_variables_dict[name]["type"] = var_type
        else:
            # Append the new variable
            resulting_variables_dict[name] = {
                "name": name,
                "value": value,
                "type": var_type,
            }
    resulting_variables = list(resulting_variables_dict.values())
    return resulting_variables


@router.callback_query(F.data.startswith("how_voting_works"))
async def handle_voting_explanation(callback_query: CallbackQuery, state: FSMContext):
    explanation_message = (
        "🔥🗳️ How Voting Works 🗳️🔥\n\n"
        "Hey, Burner! Ready to wield your BURNS powerfully? Here's how voting shapes the fate of each meme:\n\n"
        "👉 **Voting with BURNS:** Each vote is your stake in the meme's future!\n"
        "- ⛔️ **Burn 10 (Destroy the Meme):** Choose this to deduct 10 BURNS to the Burners' pool, voting to eliminate the meme.\n"
        "- ✅ **Boost 10 (Turn the Meme into Memecoin):** Opt for this to allocate 10 BURNS to the Boosters' pool, voting to transform the meme into a fresh Memecoin.\n\n"
        "🏁 **Battle of the BURNS:** Voting concludes on the due date. The team (Burners vs. Boosters) with the most BURNS staked claims victory and receive BURNS from the losing side.\n"
        "- **Boosters Win:** The BURNS staked by the Boosters are transformed into the memecoin, once this token is deployed!\n\n"
        "Gear up, choose wisely, and may the best team win! 🔥💸"
    )
    await callback_query.answer()  # Acknowledge the callback without showing a notification.
    await callback_query.message.answer(explanation_message, parse_mode="Markdown")


@router.callback_query(F.data.startswith("change_meme_name"))
async def change_meme_name_callback(callback_query: CallbackQuery, state: FSMContext):
    """Ask user to provide a new name for the meme."""
    await state.set_state(Form.waiting_for_input)
    await state.update_data(change_type="name")
    await callback_query.message.answer(
        f"@{callback_query.from_user.username} provide a new name for your meme",
        reply_markup=ForceReply(selective=True),
    )


@router.callback_query(F.data.startswith("change_meme_description"))
async def change_meme_description_callback(callback_query: CallbackQuery, state: FSMContext):
    """Ask user to provide a new description for the meme."""
    await state.set_state(Form.waiting_for_input)
    await state.update_data(change_type="description")
    await callback_query.message.answer(
        f"@{callback_query.from_user.username} provide a new description for your meme",
        reply_markup=ForceReply(selective=True),
    )


@router.message(Form.waiting_for_input)
async def handle_user_input(message: types.Message, state: FSMContext):
    """Handle the user's input for changing meme name or description."""
    user_data = await state.get_data()
    change_type = user_data.get("change_type")

    if change_type == "name":
        await message.answer(f"Meme name has been updated to: {message.text}")
        # Here you would handle updating the meme name in your backend or state

    elif change_type == "description":
        await message.answer(f"Meme description has been updated to: {message.text}")
        # Here you would handle updating the meme description in your backend or state

    await state.clear()  # Clear the state after processing the input