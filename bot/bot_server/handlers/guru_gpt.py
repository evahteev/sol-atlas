import asyncio
import logging
import uuid

import httpx
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, ForceReply, Message

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
        and message.reply_to_message.text.endswith("service! 🧙‍♂️✨")
    )


@router.callback_query(F.data.startswith("guru"))
async def guru_gpt_meme_callback(callback_query: CallbackQuery, state: FSMContext):
    """guru_gpt callback. Ask user for the prompt."""
    await state.set_state(Form.prompt_for_meme)
    username = f'@{callback_query.from_user.username}' if callback_query.from_user.username else ""
    await callback_query.message.answer(
        f"Hey {username}! Guru GPT is at your service! 🧙‍♂️✨",
        reply_markup=ForceReply(selective=True),
    )


@router.message(Command(commands=["guru"]))
async def guru_gpt_meme_callback(message: Message, state: FSMContext):
    """guru_gpt callback. Ask user for the prompt."""
    await state.set_state(Form.prompt_for_meme)
    username = f'@{message.from_user.username}' if message.from_user.username else ""
    await message.answer(
        f"Hey {username}! Guru GPT is at your service! 🧙‍♂️✨",
        reply_markup=ForceReply(selective=True),
    )

@router.message(reply_prompt_filter)
async def events_handler(
    message: types.Message,
    state: FSMContext,
    prompt: str = None,
):
    msg = await message.answer("Thinking...")
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
        resulting_variables = [
            {"name": "form_message", "value": prompt, "type": "String"},
            {"name": "action_userClose", "value": True, "type": "Boolean"},

        ]
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
                    process_definition_key="guru_gpt",
                )
            )
            await camunda_client.close()
        if process_instance:
            await message.answer(
                "Guru GPT is already running, please wait."
            )
            process_instance = process_instance[0]
        else:
            logging.info(
                f"Starting Guru GPT process instance with business key: {business_key}"
            )
            process_instance = await start_process_instance(
                state,
                business_key=business_key,
                process_definition_key="guru_gpt",
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
            guru_gpt_task = None
            for task in tasks:
                if task["task"].task_definition_key == "support_answer":
                    guru_gpt_task = task["task"]
                    break
                elif task["task"].task_definition_key == "start_gpt_thread":
                    try:
                        await complete_task(
                            state,
                            task["task"].id,
                            camunda_user_id,
                            camunda_key,
                        )
                    except Exception as e:
                        logging.error(f"Error completing task: {e}")
            if guru_gpt_task:
                break
        variables = await get_variables_guru_gpt_task(guru_gpt_task.id, state)

        gpt_reply = [v for v in variables if v["name"] == "gpt_reply"]

        gpt_parsed_reply = None
        if gpt_reply:
            gpt_parsed_reply = gpt_reply[0]['value']
        if not gpt_parsed_reply:
            raise Exception("Guru GPT did not return a reply")

        await message.reply(
            text=gpt_parsed_reply
        )
        await complete_task(
            state,
            guru_gpt_task.id,
            camunda_user_id,
            camunda_key,
        )
    except Exception as e:
        logging.error(f"Error starting Guru GPT: {e}")
        await message.answer(f"Error starting Guru GPT, {str(e)}")


async def get_variables_guru_gpt_task(task_id, state: FSMContext):
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

