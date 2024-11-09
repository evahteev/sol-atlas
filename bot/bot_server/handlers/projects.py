import logging

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
import websockets
from aiogram.types import CallbackQuery, ForceReply, Message

from bot_server.core.config import settings
from bot_server.handlers.tasks import fetch_camunda_tasks, complete_task
from bot_server.keyboards.inline.form_keyboard import form_keyboard
from bot_server.services.camunda import get_or_create_process_instance
from flow_client import FlowClient

logger = logging.getLogger(__name__)

router = Router()
reply_message_prefix = "Reply to this message with your desired "
complete_message = "Your application accepted! Bot will DM you about the app status.\nThank you for contribution!"


class Form(StatesGroup):
    form_application_name = State()
    form_application_description = State()
    form_tg_bot_name = State()
    form_tg_bot_api_key = State()


@router.callback_query(F.data == "new_project")
async def events_handler(
    callback_query: types.CallbackQuery,
    state: FSMContext,
):
    process_definition_name = "new_project_flow"
    user_task_id = "form_newProject"
    if callback_query.message.chat.type != "private":
        return await callback_query.answer("Can be called in private chat only")
    user_data = await state.get_data()
    user_info = user_data.get("user")
    camunda_user_id = user_info.get("camunda_user_id")
    if not camunda_user_id:
        await callback_query.answer("You are not registered, /start to register")
        return
    camunda_key = user_info.get("camunda_key")
    business_key = f'{user_info.get("id")}'
    await callback_query.answer()
    try:
        process_instance = await get_or_create_process_instance(
            user_id=camunda_user_id,
            password=camunda_key,
            process_definition_name=process_definition_name,
            variables=[],
            business_key=business_key,
        )
        process_instance_id = process_instance.id

        # uri = f"wss://warehouse-stage.gurunetwork.ai/api/ws/{process_instance_id}"
        # while True:
        #     async with websockets.connect(uri) as websocket:
        #         ws_data = await websocket.recv()
        #         print(ws_data)
        while True:
            tasks = await fetch_camunda_tasks(
                root_process_instance_id=process_instance_id,
                camunda_user_id=user_info.get("camunda_user_id"),
            )
            user_task = None
            for task in tasks:
                if task["task"].task_definition_key == user_task_id:
                    user_task = task
                    break
            if user_task:
                break
        await state.update_data(current_task_id=str(user_task["id"]))
        async with FlowClient(settings.FLOW_API, settings.FLOW_SYS_KEY) as flow_client:
            form_variables = await flow_client.get_camunda_form_variables(
                user_info.get("webapp_user_id"),
                task_id=user_task["id"],
            )
        # form_variables = await get_task_form_variables(user_task["id"], state)
        variables = []
        text = "Fill up the Form"
        for k, v in form_variables.items():
            if k.startswith("text_"):
                text = v["value"]
            elif k.startswith("form_"):
                variables.append({"name": k, **v})
        await callback_query.message.answer(
            text,
            reply_markup=form_keyboard(variables),
        )
    except Exception as e:
        logger.exception(e, exc_info=True, stack_info=True)
        await callback_query.message.answer("Something went wrong... Please, try again")


@router.callback_query(F.data.startswith("form:"))
async def form_handler(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    _, var_name, var_label = callback_query.data.split(":")
    if not getattr(Form, var_name, None):
        return await callback_query.answer("Wrong for variable")
    await state.set_state(var_name)

    await callback_query.message.answer(
        f"{reply_message_prefix}{var_label}",
        reply_markup=ForceReply(selective=True),
    )


def reply_form_filter(message: types.Message):
    return (
        message.reply_to_message
        and message.reply_to_message.text
        and message.reply_to_message.text.startswith(reply_message_prefix)
    )


@router.message(reply_form_filter)
async def handle_form_input(message: Message, state: FSMContext):
    var_name = await state.get_state()
    state_data = await state.get_data()
    var_label = message.reply_to_message.text.removeprefix(reply_message_prefix)
    form_variables = state_data.get("resulting_variables", [])
    form_variables.append({"name": var_name, "value": message.text, "type": "String"})
    await state.update_data(resulting_variables=form_variables)
    await message.delete()
    await message.reply_to_message.delete()
    await message.answer(f"✅ Changed {var_label}")


@router.callback_query(F.data == "form_complete")
async def complete_form_task(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    state_data = await state.get_data()
    task_id = state_data.get("current_task_id")
    user_info = state_data.get("user")
    camunda_user_id = user_info.get("camunda_user_id")
    camunda_key = user_info.get("camunda_key")
    try:
        await complete_task(
            state,
            task_id=task_id,
            camunda_user_id=camunda_user_id,
            camunda_key=camunda_key,
        )
    except Exception as e:
        logger.exception(e, exc_info=True, stack_info=True)
        await state.clear()
        await callback_query.message.answer("Something went wrong... Please, try again")
    await state.clear()
    return await callback_query.message.answer(complete_message)
