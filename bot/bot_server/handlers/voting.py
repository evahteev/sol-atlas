import asyncio
import logging
from time import time

import httpx
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from bot_server.core.config import settings
from bot_server.handlers.tasks import fetch_camunda_tasks, complete_task
from bot_server.handlers.user_inputs import (
    start_process_instance,
)
from bot_server.keyboards.inline.voting_keyboard import (
    voting_started_keyboard,
    voting_ended_keyboard,
)
from bot_server.services.blockchain import (
    get_burn_total_supply,
    get_mint_total_supply,
    get_voting_end_timestamp,
)
from camunda_client import CamundaEngineClient
from camunda_client.clients.dto import AuthData
from camunda_client.clients.engine.schemas import ProcessInstanceQuerySchema
from flow_client import FlowClient
from flow_client.clients.flow.schemas.response import ArtSchema

router = Router()


async def get_art_by_id(art_id: str) -> ArtSchema:
    async with FlowClient(
        base_url=settings.FLOW_API, sys_key=settings.FLOW_SYS_KEY
    ) as flow_client:
        art = await flow_client.get_art_by_id(art_id)
        return art


def check_start_voting_allowance(user_info, art):
    if not user_info.get("camunda_user_id"):
        return False
    if str(art.user_id) == user_info.get("id"):
        return True
    return False


@router.callback_query(F.data.startswith("start_voting"))
async def start_voting_callback(callback_query: CallbackQuery, state: FSMContext):
    """Generate meme callback. Ask user for the prompt."""
    art_id = callback_query.data.split(":")[1]
    message = callback_query.message
    await state.update_data(art_id=art_id)
    art = await get_art_by_id(art_id)
    if not art:
        await callback_query.answer("Meme not found")
        return
    state_dict = await state.get_data()
    user_info = state_dict.get("user")
    voted_meme_ids = state_dict.get("memes_voted_on", [])
    if not check_start_voting_allowance(user_info, art):
        await callback_query.answer("You are not allowed to vote on this meme")
        return

    try:
        camunda_user_id = user_info.get("camunda_user_id")
        camunda_key = user_info.get("camunda_key")
        business_key = f'{user_info.get("id")}:{art_id}'
        resulting_variables = [
            {"name": "gen_art_id", "value": art_id, "type": "String"},
            {
                "name": "vote_duration",
                # 7 days
                "value": "P7D",
                "type": "String",
            },
        ]
        await state.update_data(
            resulting_variables=resulting_variables,
            memes_voted_on=voted_meme_ids + [art_id],
        )
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
                    process_definition_key="meme_voting",
                )
            )
            await camunda_client.close()
        if process_instance:
            process_instance = process_instance[0]
            await callback_query.answer("Voting already started!")
        else:
            process_instance = await start_process_instance(
                state,
                business_key=business_key,
                process_definition_key="meme_voting",
                camunda_user_id=user_info.get("camunda_user_id"),
                camunda_key=user_info.get("camunda_key"),
            )
            await asyncio.sleep(5)  # wait for deploy token
        await message.reply(
            # "Your meme could be the next big memecoin! But first, it needs to survive the Burn/Boost game. Here's the deal: the community votes with their BURNS to either Burn or Boost your meme. When the clock runs out, the winning team snags the other side's BURNS. If the Boosters win, they'll get a share of your memecoin, and you'll gain the initial community and the right to launch it. Share your meme link with friends and the community, and be the first to vote Boost!",
            "🔥 Your meme has just entered the Meme Arena! Now your goal is to help it survive and become a Memecoin! Boost it now and share with friends! 🚀",
            reply_markup=voting_started_keyboard(art_id),
        )
    except Exception as e:
        logging.error(f"Error starting voting: {e}")
        await callback_query.answer("Error starting voting, try again later")


@router.callback_query(F.data.startswith("vote"))
async def vote_callback(callback_query: CallbackQuery, state: FSMContext):
    """Generate meme callback. Ask user for the prompt."""
    default_vote_value = 100
    _, action, art_id = callback_query.data.split(":")
    art = await get_art_by_id(art_id)
    if not art:
        await callback_query.message.answer("Meme not found")
        return
    end_ts = await get_voting_end_timestamp(art.token_address)
    if end_ts < time():
        await callback_query.message.edit_caption(
            "Voting is over", reply_markup=voting_ended_keyboard(art_id)
        )
        await callback_query.answer("Voting is over")
        return
    state_dict = await state.get_data()
    user_info = state_dict.get("user")
    voted_meme_ids = state_dict.get("memes_voted_on", [])
    try:
        camunda_user_id = user_info.get("camunda_user_id")
        camunda_key = user_info.get("camunda_key")
        business_key = f'{user_info.get("id")}:{art_id}'
        resulting_variables = [
            {"name": "gen_art_id", "value": art_id, "type": "String"},
            {
                "name": action,
                "value": default_vote_value,
                "type": "Long",
            },
        ]
        await state.update_data(
            resulting_variables=resulting_variables,
            memes_voted_on=voted_meme_ids + [art_id],
        )
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
                    process_definition_key="meme_voting",
                )
            )
            await camunda_client.close()
        if process_instance:
            process_instance = process_instance[0]
        else:
            process_instance = await start_process_instance(
                state,
                business_key=business_key,
                process_definition_key="meme_voting",
                camunda_user_id=user_info.get("camunda_user_id"),
                camunda_key=user_info.get("camunda_key"),
            )
            await asyncio.sleep(3)  # wait for the process to start
        tasks = await fetch_camunda_tasks(
            root_process_instance_id=process_instance.id,
            camunda_user_id=camunda_user_id,
        )
        for task in tasks:
            if task["task"].task_definition_key == "vote_form":
                await complete_task(
                    state, task["task"].id, camunda_user_id, camunda_key
                )
                break
        await callback_query.answer("Voted!")
        mint_supply, burn_supply = await asyncio.gather(
            get_mint_total_supply(art.token_address),
            get_burn_total_supply(art.token_address),
        )
        await callback_query.message.edit_reply_markup(
            reply_markup=voting_started_keyboard(
                art_id,
                minted=(
                    mint_supply + default_vote_value
                    if action == "mints"
                    else mint_supply
                ),
                burned=(
                    burn_supply + default_vote_value
                    if action == "burns"
                    else burn_supply
                ),
            )
        )
    except Exception as e:
        logging.error(f"Error voting: {e}")


@router.callback_query(F.data.startswith("how_voting_works"))
async def handle_voting_explanation(callback_query: CallbackQuery, state: FSMContext):
    explanation_message = (
        "🔥🗳️ How Voting Works 🗳️🔥\n\n"
        "Hey, Burner! Ready to wield your BURNS powerfully? Here's how voting shapes the fate of each meme:\n\n"
        "👉 **Voting with BURNS:** Each vote is your stake in the meme's future!\n"
        "- ⛔️ **Burn 100 (Destroy the Meme):** Choose this to deduct 100 BURNS to the Burners' pool, voting to eliminate the meme.\n"
        "- ✅ **Boost 100 (Turn the Meme into Memecoin):** Opt for this to allocate 100 BURNS to the Boosters' pool, voting to transform the meme into a fresh Memecoin.\n\n"
        "🏁 **Battle of the BURNS:** Voting concludes on the due date. The team (Burners vs. Boosters) with the most BURNS staked claims victory and receive BURNS from the losing side.\n"
        "- **Boosters Win:** The BURNS staked by the Boosters are transformed into the memecoin, once this token is deployed!\n\n"
        "Gear up, choose wisely, and may the best team win! 🔥💸"
    )
    await callback_query.answer()  # Acknowledge the callback without showing a notification.
    await callback_query.message.answer(explanation_message, parse_mode="Markdown")

    await callback_query.message.answer(explanation_message, parse_mode="Markdown")


@router.callback_query(F.data == "next_meme")
async def next_meme_callback(callback_query: CallbackQuery, state: FSMContext):
    """Handle 'Next Meme' button click."""
    state_dict = await state.get_data()
    memes_voted_on = state_dict.get("memes_voted_on", [])

    try:
        # Fetch the next meme (implement the logic as needed to get the next meme)
        next_art = await get_next_meme(exclude_ids=memes_voted_on)

        if not next_art:
            await callback_query.message.answer("No more memes to vote on!")
            return
        await state.update_data(memes_voted_on=memes_voted_on + [str(next_art.id)])
        # Send the next meme for voting
        await callback_query.message.answer_photo(
            photo=next_art.img_picture,  # Assuming img_picture is the image URL
            reply_markup=voting_started_keyboard(str(next_art.id)),
            caption="Burn or Boost this meme?",
        )
        await callback_query.answer()

    except Exception as e:
        logging.error(f"Error fetching next meme: {e}")
        await callback_query.answer("Error fetching next meme, try again later")


async def get_next_meme(exclude_ids: list[str]) -> ArtSchema:
    """Fetch the next meme for voting."""
    # Implement your logic to fetch the next meme here
    # For example, you could use a database query or an API call.
    async with FlowClient(
        base_url=settings.FLOW_API, sys_key=settings.FLOW_SYS_KEY
    ) as flow_client:
        next_art = await flow_client.get_random_art_for_vote(exclude_ids=exclude_ids)
        return next_art
