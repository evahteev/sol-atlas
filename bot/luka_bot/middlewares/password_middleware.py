"""
Password authentication middleware for bot access control.

When LUKA_PASSWORD_ENABLED is True, users must authenticate with the correct
password before they can interact with the bot.
"""
import html
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery, ForceReply
from aiogram.fsm.context import FSMContext
from loguru import logger

from luka_bot.core.config import settings
from luka_bot.core.loader import bot, redis_client
from aiogram.enums import ChatType, MessageEntityType


PASSWORD_TEXTS = {
    "en": {
        "prompt_private": "🔐 <b>Password required</b>\n\nSend the access password or type /skip to cancel.",
        "prompt_group": "🔐 <b>Password required for {group_name}</b>\n\nSend the access password here or type /skip to cancel.",
        "placeholder": "Password or /skip",
        "incorrect_dm": "❌ <b>Incorrect password.</b>\n\nTry again or type /skip to cancel.",
        "success_dm": "✅ <b>Password accepted!</b>\n\nYou can now use the bot.",
        "success_dm_group": "✅ <b>Password accepted!</b>\n\nGroup {group_name} unlocked for all team members.",
        "success_group": "✅ {user_mention} unlocked the group for all members.",
        "skip_ack": "👌 No problem. Send the password whenever you're ready.",
    },
    "ru": {
        "prompt_private": "🔐 <b>Нужен пароль</b>\n\nОтправьте пароль доступа или введите /skip, чтобы отменить.",
        "prompt_group": "🔐 <b>Нужен пароль для {group_name}</b>\n\nОтправьте пароль здесь или введите /skip, чтобы отменить.",
        "placeholder": "Пароль или /skip",
        "incorrect_dm": "❌ <b>Неверный пароль.</b>\n\nПопробуйте ещё раз или введите /skip, чтобы отменить.",
        "success_dm": "✅ <b>Пароль принят!</b>\n\nТеперь можно пользоваться ботом.",
        "success_dm_group": "✅ <b>Пароль принят!</b>\n\nГруппа {group_name} разблокирована для всех участников.",
        "success_group": "✅ {user_mention} разблокировал группу для всех участников.",
        "skip_ack": "👌 Хорошо. Как будете готовы — просто отправьте пароль.",
    },
}

class PasswordMiddleware(BaseMiddleware):
    """
    Password-gate middleware that blocks unauthenticated users.
    
    Workflow:
    1. Check if password protection is enabled
    2. If not enabled, pass through to next handler
    3. If enabled, check if user has authenticated (stored in FSM state)
    4. If authenticated, pass through
    5. If not authenticated:
       - Send password prompt
       - Block further processing
       - Wait for password input
    
    Password verification happens in FSM state management.
    Once authenticated, user's state is marked and they can proceed.
    """
    
    # Redis key prefix for tracking authenticated users
    REDIS_KEY_PREFIX = "password_auth:"
    # Session timeout (7 days in seconds)
    AUTH_TIMEOUT = 60 * 60 * 24 * 7
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Check password authentication before allowing access."""
        
        # Skip if password protection is disabled
        if not settings.LUKA_PASSWORD_ENABLED:
            return await handler(event, data)
        
        # Skip if no password is configured
        if not settings.LUKA_PASSWORD:
            logger.warning("⚠️ LUKA_PASSWORD_ENABLED=True but LUKA_PASSWORD is empty!")
            return await handler(event, data)
        
        # Extract user and message from event
        user = None
        message = None
        
        if isinstance(event, Message):
            user = event.from_user
            message = event
        elif isinstance(event, CallbackQuery):
            user = event.from_user
            message = event.message
        
        if not user:
            # No user context, skip
            return await handler(event, data)
        
        targeted_group_message = False
        # In group chats: only enforce password when user targets the bot
        if isinstance(message, Message) and message.chat and message.chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):
            try:
                me = await bot.get_me()
                targeted = False
                # Reply to the bot
                if message.reply_to_message and message.reply_to_message.from_user and message.reply_to_message.from_user.id == me.id:
                    targeted = True
                # Mention of the bot (including in bot_command like /start@BotName)
                if not targeted and message.text and message.entities:
                    for ent in message.entities:
                        if ent.type in (MessageEntityType.MENTION, MessageEntityType.BOT_COMMAND):
                            piece = message.text[ent.offset: ent.offset + ent.length]
                            if f"@{me.username}" in piece:
                                targeted = True
                                break
                if targeted:
                    targeted_group_message = True
                else:
                    return await handler(event, data)
            except Exception as e:
                logger.error(f"Group targeting check failed: {e}")
                # On failure, do not block the message
                return await handler(event, data)

        user_id = user.id
        
        # Check authentication status from Redis (primary) and FSM storage (secondary)
        # Redis is the source of truth for authentication state
        state: FSMContext | None = data.get("state")
        state_data = await state.get_data() if state else {}
        awaiting_password = state_data.get("password_prompt_sent", False)
        
        # Check global authentication from Redis (primary source of truth)
        global_auth = await self._is_user_authenticated(user_id)
        
        # FSM state is only used for awaiting_password, not for authentication status
        # Authentication status comes from Redis to survive /reset commands
        is_authenticated = global_auth
        
        logger.debug(f"🔐 State data for user {user_id}: {state_data}")
        logger.debug(f"🔐 Auth check for user {user_id}: global_auth={global_auth}, targeted_group_message={targeted_group_message}, awaiting_password={awaiting_password}")

        if targeted_group_message:
            # For groups, check if group is unlocked (any user has authenticated for it)
            group_unlocked = await self._is_group_unlocked(message.chat.id)
            logger.debug(f"🔐 Group unlock check for group {message.chat.id}: group_unlocked={group_unlocked}")
            logger.debug(f"🔑 Checked Redis key: password_auth:group_unlocked:{message.chat.id}")
            
            if not group_unlocked:
                # Need group authentication - only ask the first user who mentions the bot
                if state and not awaiting_password:
                    await state.update_data(password_prompt_sent=True)
                await self._send_group_password_request_to_dm(message, user_id, message.chat.id, state)
                return None
            
            # Group is unlocked, allow access for all users
            if state and state_data.get("password_prompt_sent"):
                await state.update_data(password_prompt_sent=False)
            return await handler(event, data)

        # Check if user is in DM and awaiting password (from group context)
        if (
            isinstance(event, Message)
            and message
            and message.chat
            and message.chat.type == ChatType.PRIVATE
            and awaiting_password
        ):
            # User is in DM and awaiting password (from group context)
            logger.debug(f"🔐 User {user_id} in DM awaiting password from group context")
            # Let the password verification logic handle this - don't return here
        elif is_authenticated:
            return await handler(event, data)
        elif (
            isinstance(event, Message)
            and message
            and message.chat
            and message.chat.type == ChatType.PRIVATE
            and not global_auth
            and not awaiting_password  # Don't send prompt if already awaiting password
        ):
            # User is in DM but not globally authenticated - send password prompt
            logger.debug(f"🔐 User {user_id} in DM but not globally authenticated - sending password prompt")
            if state:
                await state.update_data(
                    password_prompt_sent=True,
                    password_prompt_context=None,
                )
            await message.answer(
                self._t(user, "prompt_private"),
                parse_mode="HTML",
                reply_markup=ForceReply(
                    force_reply=True,
                    selective=False,
                    input_field_placeholder=self._t(user, "placeholder"),
                ),
            )
            return None

        # If user is in group but needs to enter password in DM, block the message
        if (
            isinstance(event, Message)
            and message
            and message.chat
            and message.chat.type in (ChatType.GROUP, ChatType.SUPERGROUP)
            and awaiting_password
        ):
            logger.info(f"🔐 User {user_id} is in group but needs to enter password in DM")
            await message.reply(
                "🔐 <b>Password Required</b>\n\n"
                "Please check your private messages to enter the password.",
                parse_mode="HTML"
            )
            return None

        # User not authenticated - handle password verification in DM
        if (
            isinstance(event, Message)
            and event.text
            and message
            and message.chat
            and message.chat.type == ChatType.PRIVATE
            and awaiting_password
        ):
            password_attempt = event.text.strip()
            logger.info(f"🔐 Processing password attempt from user {user_id} in DM: {password_attempt[:10]}...")
            logger.info(f"🔐 State data: {state_data}")

            if password_attempt.lower() == "/skip":
                if state:
                    await state.update_data(password_prompt_sent=False, password_prompt_context=None)
                await message.answer(
                    self._t(user, "skip_ack"),
                    parse_mode="HTML",
                )
                return None

            if password_attempt == settings.LUKA_PASSWORD:
                # STEP 1: Read context FIRST from state_data (before clearing)
                scope_context = state_data.get("password_prompt_context") if state_data else None
                group_title = None
                group_id = None
                
                if scope_context:
                    group_title = scope_context.get("group_title")
                    group_id = scope_context.get("group_id")
                
                # STEP 2: Mark global authentication in Redis (source of truth)
                await self._mark_user_authenticated(user_id)
                logger.info(f"✅ User {user_id} authenticated successfully")

                # STEP 3: Mark group-specific authentication if context exists
                if group_title and group_id:
                    # Mark this user as authenticated for the group (for tracking purposes)
                    await self._mark_group_authenticated(user_id, group_id)
                    # Mark the group as unlocked for all users
                    await self._mark_group_unlocked(group_id)
                    logger.info(f"✅ User {user_id} authenticated for group {group_id}")
                    logger.info(f"🔓 Group {group_id} unlocked for all users")
                    logger.debug(f"🔑 Set Redis key: password_auth:group_unlocked:{group_id}")
                    
                    # Check if this was via deep link
                    deep_link_accessed = scope_context.get("deep_link_accessed", False) if scope_context else False
                    user_from = scope_context.get("user_from") if scope_context else None
                    thread_id = scope_context.get("thread_id") if scope_context else None
                    
                    if deep_link_accessed:
                        logger.info(f"🔗 Deep link authentication completed - user {user_id} authenticated for group {group_id} via deep link")
                        if user_from:
                            logger.info(f"🔗 Deep link originated from user {user_from}")
                        if thread_id:
                            logger.info(f"🔗 Deep link thread context: {thread_id}")
                    
                    # Enhanced success message for deep link users
                    if deep_link_accessed:
                        success_text = f"🎉 <b>Authentication successful!</b>\n\n"
                        success_text += f"✅ <b>Group:</b> {group_title}\n"
                        success_text += f"🆔 <b>Group ID:</b> <code>{group_id}</code>\n"
                        if user_from:
                            success_text += f"👤 <b>From user:</b> {user_from}\n"
                        if thread_id:
                            success_text += f"🧵 <b>Thread ID:</b> {thread_id}\n"
                        success_text += f"\n🚀 <b>Group unlocked for all team members!</b>\n\n"
                        success_text += f"All members can now use the bot in this group without entering passwords.\n"
                        success_text += f"Go back to the group and mention me to get started."
                        
                        await message.answer(success_text, parse_mode="HTML")
                    else:
                        # Regular group authentication (not via deep link)
                        await message.answer(
                            self._t(user, "success_dm_group", group_name=html.escape(group_title)),
                            parse_mode="HTML",
                        )
                    
                    try:
                        # Send group notification that group is now unlocked for all members
                        group_notification = f"🔓 <b>Group unlocked!</b>\n\n"
                        group_notification += f"✅ {self._mention(user)} has authenticated and unlocked this group.\n"
                        group_notification += f"🚀 <b>All team members can now use the bot without passwords!</b>"
                        
                        await message.bot.send_message(
                            chat_id=group_id,
                            text=group_notification,
                            parse_mode="HTML",
                        )
                    except Exception as exc:
                        logger.warning(f"Failed to send group success notice: {exc}")
                else:
                    # Global authentication only (no group context)
                    await message.answer(
                        self._t(user, "success_dm"),
                        parse_mode="HTML",
                    )
                
                # STEP 4: NOW clear state (after auth is marked in Redis)
                if state:
                    await state.update_data(
                        password_prompt_sent=False,
                        password_prompt_context=None,
                    )
                return None

            logger.warning(f"❌ User {user_id} failed password authentication")
            await message.answer(
                self._t(user, "incorrect_dm"),
                parse_mode="HTML",
                # Remove ForceReply to avoid double password prompts
            )
            return None

        # Block further processing until authenticated
        return None

    async def _send_group_password_request_to_dm(self, message: Message, user_id: int, group_id: int, state: FSMContext | None):
        """Send password request to user's DM and notify group."""
        try:
            # Get group info for the DM message
            group_title = message.chat.title or f"Group {group_id}"

            logger.info(f"🔐 Sending password request to DM for user {user_id} in group {group_id} ({group_title})")

            # Send password request to user's DM
            await message.bot.send_message(
                chat_id=user_id,
                text=self._t(message.from_user, "prompt_group", group_name=html.escape(group_title), group_id=group_id),
                parse_mode="HTML",
                reply_markup=ForceReply(
                    force_reply=True,
                    selective=False,
                    input_field_placeholder=self._t(message.from_user, "placeholder"),
                ),
            )

            logger.info(f"✅ DM message sent successfully to user {user_id}")

            # Send simple group notification with direct deep link
            bot_info = await message.bot.get_me()
            bot_username = bot_info.username
            deep_link = f"https://t.me/{bot_username}?start=group_{abs(group_id)}_auth&user_from={user_id}&group_connect={abs(group_id)}"
            
            await message.reply(
                f"🔐 <b>Password required</b>\n\n"
                f"🔗 <a href='{deep_link}'>Click here to enter password</a>",
                parse_mode="HTML",
            )

            logger.info(f"✅ Group notification sent for user {user_id} in group {group_id}")

            if state:
                await state.update_data(
                    password_prompt_sent=True,
                    password_prompt_context={
                        "group_id": group_id,
                        "group_title": group_title,
                    },
                )

        except Exception as e:
            logger.error(f"Failed to send password request to DM: {e}", exc_info=True)
            # DM failed - user hasn't started bot
            # Send deep link in group
            try:
                bot_info = await message.bot.get_me()
                bot_username = bot_info.username
                # Enhanced deep link with metadata
                deep_link = f"https://t.me/{bot_username}?start=group_{abs(group_id)}_auth&user_from={user_id}&group_connect={abs(group_id)}"
                
                logger.info(f"🔗 Generated deep link for user {user_id} in group {group_id}: {deep_link}")
                
                await message.reply(
                    f"🔐 <b>Password required</b>\n\n"
                    f"🔗 <a href='{deep_link}'>Click here to enter password</a>",
                    parse_mode="HTML"
                )
                logger.info(f"✅ Deep link sent to group {group_id} for user {user_id}")
            except Exception as link_error:
                logger.error(f"Failed to send deep link: {link_error}")
                # Final fallback: send basic message to group
                await message.answer(
                    self._t(message.from_user, "prompt_private"),
                    parse_mode="HTML",
                )

    @classmethod
    def _auth_key(cls, user_id: int) -> str:
        """Redis key for globally authenticated users."""
        return f"{cls.REDIS_KEY_PREFIX}user:{user_id}"
    
    @classmethod
    def _group_auth_key(cls, user_id: int, group_id: int) -> str:
        """Redis key for group-specific authenticated users."""
        return f"{cls.REDIS_KEY_PREFIX}group:{user_id}:{group_id}"

    async def _mark_user_authenticated(self, user_id: int) -> None:
        """Persist authenticated flag so group chats unlock immediately."""
        try:
            await redis_client.set(
                name=self._auth_key(user_id),
                value="1",
                ex=self.AUTH_TIMEOUT,
            )
        except Exception as exc:
            logger.warning(f"Could not persist password auth for user {user_id}: {exc}")

    async def _is_user_authenticated(self, user_id: int) -> bool:
        """Check global authentication flag from Redis."""
        try:
            cached = await redis_client.get(self._auth_key(user_id))
            return bool(cached)
        except Exception as exc:
            logger.warning(f"Could not fetch password auth for user {user_id}: {exc}")
            return False
    
    async def _mark_group_authenticated(self, user_id: int, group_id: int) -> None:
        """Persist group-specific authenticated flag."""
        try:
            await redis_client.set(
                name=self._group_auth_key(user_id, group_id),
                value="1",
                ex=self.AUTH_TIMEOUT,
            )
        except Exception as exc:
            logger.warning(f"Could not persist group password auth for user {user_id} in group {group_id}: {exc}")
    
    async def _is_group_authenticated(self, user_id: int, group_id: int) -> bool:
        """Check group-specific authentication flag from Redis."""
        try:
            cached = await redis_client.get(self._group_auth_key(user_id, group_id))
            return bool(cached)
        except Exception as exc:
            logger.warning(f"Could not fetch group password auth for user {user_id} in group {group_id}: {exc}")
            return False

    @classmethod
    def _group_unlocked_key(cls, group_id: int) -> str:
        """Redis key for group unlock status (any user has authenticated for this group)."""
        return f"{cls.REDIS_KEY_PREFIX}group_unlocked:{group_id}"

    async def _mark_group_unlocked(self, group_id: int) -> None:
        """Mark group as unlocked (any user has authenticated for this group)."""
        try:
            await redis_client.set(
                name=self._group_unlocked_key(group_id),
                value="1",
                ex=self.AUTH_TIMEOUT,
            )
            logger.info(f"🔓 Group {group_id} unlocked for all users")
        except Exception as exc:
            logger.warning(f"Could not mark group {group_id} as unlocked: {exc}")

    async def _is_group_unlocked(self, group_id: int) -> bool:
        """Check if group is unlocked (any user has authenticated for this group)."""
        try:
            cached = await redis_client.get(self._group_unlocked_key(group_id))
            return bool(cached)
        except Exception as exc:
            logger.warning(f"Could not check if group {group_id} is unlocked: {exc}")
            return False
    def _t(self, user, key: str, **kwargs) -> str:
        language = (getattr(user, "language_code", None) or "en").split("-")[0].lower()
        texts = PASSWORD_TEXTS.get(language, PASSWORD_TEXTS["en"])
        return texts[key].format(**kwargs)

    def _mention(self, user) -> str:
        name = user.full_name or user.username or str(user.id)
        return f'<a href="tg://user?id={user.id}">{html.escape(name)}</a>'
