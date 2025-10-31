"""
Group command handlers - commands available in groups.
"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ChatType
from loguru import logger

from luka_bot.core.config import settings
from luka_bot.services.group_service import get_group_service
from luka_bot.utils.permissions import is_user_admin_in_group
from luka_bot.keyboards.group_admin import create_group_admin_menu
from luka_bot.utils.i18n_helper import _

router = Router()


@router.message(lambda msg: msg.chat.type in ("group", "supergroup"), Command("help"))
async def handle_help_in_group(message: Message):
    """
    Enhanced /help command - shows comprehensive group profile card.
    
    Displays:
    - Group photo and description
    - Full statistics (members, messages, activity)
    - Administrator list
    - Bot interaction prompts
    - Quick action buttons
    """
    try:
        group_id = message.chat.id
        
        # Get services
        group_service = await get_group_service()
        language = await group_service.get_group_language(group_id)
        
        # Get group metadata and settings
        metadata = await group_service.get_cached_group_metadata(group_id)
        
        if not metadata:
            # Group not initialized - show simple help
            await _show_simple_help(message, language)
            return
        
        from luka_bot.services.moderation_service import get_moderation_service
        from luka_bot.services.elasticsearch_service import get_elasticsearch_service
        from luka_bot.services.group_description_generator import generate_group_description
        
        moderation_service = await get_moderation_service()
        settings_obj = await moderation_service.get_group_settings(group_id)
        
        # ===================================================================
        # 1. GROUP HEADER (Title + Description)
        # ===================================================================
        
        group_title = metadata.group_title or message.chat.title or f"Group {group_id}"
        
        # Get or generate description
        description = None
        if settings_obj and settings_obj.custom_description:
            description = settings_obj.custom_description
        elif settings_obj and settings_obj.generated_tagline:
            description = settings_obj.generated_tagline
        else:
            # Generate new description
            metadata_dict = {
                "description": metadata.description,
                "member_count": metadata.total_member_count,
                "message_count": metadata.total_messages_received,
                "group_type": metadata.group_type,
            }
            description = await generate_group_description(
                group_title,
                metadata_dict,
                language
            )
            
            # Cache it
            if settings_obj:
                settings_obj.generated_tagline = description
                from datetime import datetime
                settings_obj.generated_tagline_updated = datetime.utcnow()
                await moderation_service.save_group_settings(settings_obj)
        
        # ===================================================================
        # 2. GROUP STATISTICS (Same format as stats page)
        # ===================================================================
        
        kb_index = await group_service.get_group_kb_index(group_id)
        
        # Get live member count
        member_count = metadata.total_member_count
        try:
            member_count = await message.bot.get_chat_member_count(group_id)
        except Exception as e:
            logger.debug(f"Could not get live member count: {e}")
        
        # Get KB stats
        message_count = 0
        size_mb = 0.0
        unique_users_week = 0
        messages_week = 0
        
        if kb_index:
            try:
                es_service = await get_elasticsearch_service()
                
                # Get index stats
                index_stats = await es_service.get_index_stats(kb_index)
                message_count = index_stats.get("message_count", 0)
                size_mb = index_stats.get("size_mb", 0.0)
                
                # Get weekly stats
                weekly_stats = await es_service.get_group_weekly_stats(kb_index)
                unique_users_week = weekly_stats.get("unique_users_week", 0)
                messages_week = weekly_stats.get("total_messages_week", 0)
            except Exception as e:
                logger.debug(f"Could not get KB stats: {e}")
        
        # ===================================================================
        # 3. ADMINISTRATORS LIST
        # ===================================================================
        
        admin_section = ""
        if metadata.admin_list:
            # Show top 5 admins
            admins_display = []
            for i, admin in enumerate(metadata.admin_list[:5], 1):
                name = admin.get("full_name", "Unknown")
                custom_title = admin.get("custom_title")
                status = admin.get("status", "admin")
                
                # Icon based on role
                if status == "creator":
                    icon = "👑"
                elif custom_title:
                    icon = "⭐"
                else:
                    icon = "👤"
                
                # Format
                if custom_title:
                    admins_display.append(f"{icon} {name} • {custom_title}")
                else:
                    admins_display.append(f"{icon} {name}")
            
            if language == "ru":
                admin_header = "\n\n👥 <b>Администраторы:</b>"
                if len(metadata.admin_list) > 5:
                    admin_footer = f"\n<i>... и ещё {len(metadata.admin_list) - 5}</i>"
                else:
                    admin_footer = ""
            else:
                admin_header = "\n\n👥 <b>Administrators:</b>"
                if len(metadata.admin_list) > 5:
                    admin_footer = f"\n<i>... and {len(metadata.admin_list) - 5} more</i>"
                else:
                    admin_footer = ""
            
            admin_section = admin_header + "\n" + "\n".join(admins_display) + admin_footer
        
        # ===================================================================
        # 4. BUILD COMPLETE MESSAGE
        # ===================================================================
        
        # Translations
        bot_info = await message.bot.get_me()
        bot_username = bot_info.username
        
        if language == "ru":
            stats_header = "📊 <b>Статистика:</b>"
            members_label = "👥 Участников"
            messages_label = "📝 Сообщений в БЗ"
            kb_size_label = "💾 Размер БЗ"
            activity_header = "\n<b>За последние 7 дней:</b>"
            active_users_label = "👤 Активных"
            messages_sent_label = "💬 Отправлено"
            
            bot_section = f"""
💬 <b>Как взаимодействовать со мной:</b>
• Упомяните @{bot_username} с вашим вопросом
• Используйте /search для поиска в истории группы
• Администраторы могут использовать /settings для настройки

<i>💡 Напишите мне в личку для расширенных функций!</i>"""
        else:
            stats_header = "📊 <b>Statistics:</b>"
            members_label = "👥 Members"
            messages_label = "📝 KB Messages"
            kb_size_label = "💾 KB Size"
            activity_header = "\n<b>Last 7 Days:</b>"
            active_users_label = "👤 Active"
            messages_sent_label = "💬 Sent"
            
            bot_section = f"""
💬 <b>How to interact with me:</b>
• Mention @{bot_username} with your question
• Use /search to find messages in group history
• Admins can use /settings to configure

<i>💡 Message me privately for advanced features!</i>"""
        
        # Build stats text
        stats_text = f"""{stats_header}
{members_label}: <b>{member_count:,}</b>
{messages_label}: <b>{message_count:,}</b>
{kb_size_label}: <b>{size_mb:.2f} MB</b>"""
        
        # Add weekly activity if there's data
        if message_count > 0 and messages_week > 0:
            stats_text += f"""{activity_header}
{active_users_label}: <b>{unique_users_week}</b>
{messages_sent_label}: <b>{messages_week:,}</b>"""
        
        # Complete message
        help_text = f"""🏠 <b>{group_title}</b>
<i>{description}</i>

{stats_text}{admin_section}

{bot_section}"""
        
        # ===================================================================
        # 5. INLINE KEYBOARD WITH ACTIONS
        # ===================================================================
        
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        if language == "ru":
            buttons = [
                [
                    InlineKeyboardButton(
                        text="📊 Подробная статистика",
                        callback_data=f"group_stats:{group_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="💬 Написать боту",
                        url=f"https://t.me/{bot_username}?start=help"
                    )
                ],
            ]
            
            # Add settings button for admins
            if message.from_user:
                is_admin = await is_user_admin_in_group(message.bot, group_id, message.from_user.id)
                if is_admin:
                    buttons.insert(1, [
                        InlineKeyboardButton(
                            text="⚙️ Настройки группы",
                            callback_data=f"group_admin_menu:{group_id}"
                        )
                    ])
        else:
            buttons = [
                [
                    InlineKeyboardButton(
                        text="📊 Detailed Statistics",
                        callback_data=f"group_stats:{group_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="💬 Message Bot",
                        url=f"https://t.me/{bot_username}?start=help"
                    )
                ],
            ]
            
            # Add settings button for admins
            if message.from_user:
                is_admin = await is_user_admin_in_group(message.bot, group_id, message.from_user.id)
                if is_admin:
                    buttons.insert(1, [
                        InlineKeyboardButton(
                            text="⚙️ Group Settings",
                            callback_data=f"group_admin_menu:{group_id}"
                        )
                    ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        
        # ===================================================================
        # 6. SEND MESSAGE (with photo if available)
        # ===================================================================
        
        # Try to send with group photo
        photo_sent = False
        if metadata.photo_big_file_id or (settings_obj and settings_obj.custom_avatar_file_id):
            try:
                photo_id = (settings_obj.custom_avatar_file_id 
                           if settings_obj and settings_obj.custom_avatar_file_id 
                           else metadata.photo_big_file_id)
                
                await message.answer_photo(
                    photo=photo_id,
                    caption=help_text,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
                photo_sent = True
                logger.info(f"📸 Sent /help with photo for group {group_id}")
            except Exception as e:
                logger.debug(f"Could not send photo: {e}")
        
        # Fallback to text-only
        if not photo_sent:
            await message.answer(
                help_text,
                parse_mode="HTML",
                reply_markup=keyboard,
                disable_web_page_preview=True
            )
            logger.info(f"📖 Sent /help for group {group_id}")
        
    except Exception as e:
        logger.error(f"Failed to handle /help in group: {e}", exc_info=True)
        # Fallback to simple help
        try:
            await _show_simple_help(message, "en")
        except:
            pass


async def _show_simple_help(message: Message, language: str):
    """Fallback simple help message when group not fully initialized."""
    try:
        bot_info = await message.bot.get_me()
        bot_username = bot_info.username
        bot_name = settings.LUKA_NAME
        
        if language == "ru":
            help_text = f"""👋 Привет! Я <b>{bot_name}</b>

Упомяните меня (@{bot_username}) с вопросом, и я помогу!
Или используйте /search для поиска в истории группы.

💡 Напишите мне в личку для расширенных функций:
https://t.me/{bot_username}?start=help"""
        else:
            help_text = f"""👋 Hi! I'm <b>{bot_name}</b>

Mention me (@{bot_username}) with your question and I'll help!
Or use /search to find messages in group history.

💡 Message me privately for advanced features:
https://t.me/{bot_username}?start=help"""
        
        await message.answer(help_text, parse_mode="HTML", disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"Failed to send simple help: {e}")


@router.message(lambda msg: msg.chat.type in ("group", "supergroup"), Command("stats"))
async def handle_stats_in_group(message: Message):
    """
    Handle /stats command in groups.
    Shows group statistics (basic info for now).
    """
    try:
        group_id = message.chat.id
        group_title = message.chat.title or f"Group {group_id}"
        
        # Get group KB info and language
        group_service = await get_group_service()
        kb_index = await group_service.get_group_kb_index(group_id)
        language = await group_service.get_group_language(group_id)
        
        if not kb_index:
            await message.answer(
                _('group.cmd.stats.not_setup', language),
                parse_mode="HTML"
            )
            return
        
        # Get group link info
        links = await group_service.list_user_groups(message.from_user.id, active_only=True)
        group_link = None
        for link in links:
            if link.group_id == group_id:
                group_link = link
                break
        
        # Build stats message
        stats_text = _('group.cmd.stats.title', language,
                      group_title=group_title,
                      group_id=group_id,
                      kb_index=kb_index)
        
        await message.answer(stats_text, parse_mode="HTML")
        logger.info(f"📊 /stats command in group {group_id}")
        
    except Exception as e:
        logger.error(f"Failed to handle /stats in group: {e}")


@router.message(lambda msg: msg.chat.type in ("group", "supergroup"), Command("settings"))
async def handle_settings_in_group(message: Message):
    """
    Handle /settings command in groups (admin only).
    Sends admin controls menu to user's DM.
    """
    try:
        if not message.from_user:
            return
        
        user_id = message.from_user.id
        group_id = message.chat.id
        group_title = message.chat.title or f"Group {group_id}"
        
        # Get group language
        group_service = await get_group_service()
        language = await group_service.get_group_language(group_id)
        
        # Check if admin
        is_admin = await is_user_admin_in_group(message.bot, group_id, user_id)
        
        if not is_admin:
            await message.answer(
                _('group.cmd.admin_only', language),
                parse_mode="HTML"
            )
            return
        
        # Send settings menu in DM
        try:
            from luka_bot.services.moderation_service import get_moderation_service
            
            moderation_service = await get_moderation_service()
            settings_obj = await moderation_service.get_group_settings(group_id)
            moderation_enabled = settings_obj.moderation_enabled if settings_obj else True
            stoplist_count = len(settings_obj.stoplist_words) if settings_obj else 0
            current_language = await group_service.get_group_language(group_id)
            
            admin_menu = create_group_admin_menu(
                group_id, 
                group_title,
                moderation_enabled,
                stoplist_count,
                current_language,
                silent_mode=settings_obj.silent_mode if settings_obj else False,
                ai_assistant_enabled=settings_obj.ai_assistant_enabled if settings_obj else True,
                kb_indexation_enabled=settings_obj.kb_indexation_enabled if settings_obj else True,
                moderate_admins_enabled=settings_obj.moderate_admins_enabled if settings_obj else False
            )
            await message.bot.send_message(
                user_id,
                f"🛡️ <b>Group Moderation & Filters</b>\n\n"
                f"Group: <b>{group_title}</b>\n\n"
                f"<i>Configure moderation and content filters below:</i>",
                reply_markup=admin_menu,
                parse_mode="HTML"
            )
            await message.answer(_('group.cmd.settings_sent', language))
            logger.info(f"⚙️ Sent settings menu to admin {user_id} for group {group_id}")
        except Exception as e:
            logger.error(f"Failed to send DM: {e}")
            await message.answer(
                _('group.cmd.dm_failed', language),
                parse_mode="HTML"
            )
        
    except Exception as e:
        logger.error(f"Failed to handle /settings in group: {e}")


@router.message(lambda msg: msg.chat.type in ("group", "supergroup"), Command("search"))
async def handle_search_in_group(message: Message):
    """
    Handle /search command in groups.
    
    Usage:
    - /search → Shows instruction to provide keyword
    - /search <keyword> → Direct search in current group's KB
    
    Searches only the current group's knowledge base and returns
    formatted results with deeplinks.
    """
    try:
        if not message.from_user:
            return
        
        user_id = message.from_user.id
        group_id = message.chat.id
        group_title = message.chat.title or f"Group {group_id}"
        
        # Get group language
        group_service = await get_group_service()
        language = await group_service.get_group_language(group_id)
        
        logger.info(f"🔍 /search in group {group_id} by user {user_id}")
        
        # Parse command with args (using aiogram's built-in parsing)
        from aiogram.filters import CommandObject
        from aiogram import Bot
        
        # Extract command args manually
        command_text = message.text or ""
        command_args = command_text.split(maxsplit=1)
        keyword = command_args[1].strip() if len(command_args) > 1 else None
        
        # Check if keyword provided
        if not keyword:
            # No keyword - show instruction
            instruction_text = {
                "en": (
                    "🔍 <b>Search Group Messages</b>\n\n"
                    "Use this command to search through this group's message history.\n\n"
                    "<b>Usage:</b>\n"
                    "<code>/search keyword or phrase</code>\n\n"
                    "<b>Examples:</b>\n"
                    "• <code>/search Bitcoin</code>\n"
                    "• <code>/search deployment issues</code>\n"
                    "• <code>/search @username</code>\n\n"
                    f"💡 I'll search through <b>{group_title}</b>'s knowledge base and show you relevant messages with direct links!"
                ),
                "ru": (
                    "🔍 <b>Поиск по сообщениям группы</b>\n\n"
                    "Используйте эту команду для поиска в истории сообщений группы.\n\n"
                    "<b>Использование:</b>\n"
                    "<code>/search ключевое слово или фраза</code>\n\n"
                    "<b>Примеры:</b>\n"
                    "• <code>/search Bitcoin</code>\n"
                    "• <code>/search проблемы с развертыванием</code>\n"
                    "• <code>/search @username</code>\n\n"
                    f"💡 Я найду в базе знаний группы <b>{group_title}</b> релевантные сообщения с прямыми ссылками!"
                )
            }
            
            await message.answer(
                instruction_text.get(language, instruction_text["en"]),
                parse_mode="HTML"
            )
            return
        
        # Keyword provided - perform search
        logger.info(f"🔍 Group search: group={group_id}, keyword='{keyword}'")
        
        # Send searching indicator
        from luka_bot.utils.formatting import escape_html
        search_msg = f"🔍 " + (
            f"Searching for: <b>{escape_html(keyword)}</b>" if language == "en"
            else f"Ищу: <b>{escape_html(keyword)}</b>"
        )
        status_message = await message.answer(search_msg, parse_mode="HTML")
        
        # Get group's KB index from Thread (proper way)
        from luka_bot.services.elasticsearch_service import get_elasticsearch_service
        from datetime import datetime
        
        # Use group service to get the actual KB index
        group_kb_index = await group_service.get_group_kb_index(group_id)
        
        # Check if KB exists
        if not group_kb_index:
            no_kb_text = {
                "en": f"❌ No knowledge base found for this group. Messages need to be indexed first.",
                "ru": f"❌ База знаний для этой группы не найдена. Сначала нужно проиндексировать сообщения."
            }
            await status_message.edit_text(
                no_kb_text.get(language, no_kb_text["en"]),
                parse_mode="HTML"
            )
            return
        
        # Get ES service
        es_service = await get_elasticsearch_service()
        
        # Perform search
        try:
            results = await es_service.search_messages_text(
                index_name=group_kb_index,
                query_text=keyword,
                max_results=10
            )
        except Exception as e:
            logger.warning(f"Search failed for KB {group_kb_index}: {e}")
            error_text = {
                "en": f"❌ Search failed. Please try again.",
                "ru": f"❌ Ошибка поиска. Попробуйте снова."
            }
            await status_message.edit_text(
                error_text.get(language, error_text["en"]),
                parse_mode="HTML"
            )
            return
        
        # Format results
        if not results:
            no_results_msg = f"❌ " + (
                f"No messages found for '<b>{escape_html(keyword)}</b>'. Try different keywords."
                if language == "en"
                else f"Сообщения по запросу '<b>{escape_html(keyword)}</b>' не найдены. Попробуйте другие ключевые слова."
            )
            await status_message.edit_text(no_results_msg, parse_mode="HTML")
            return
        
        # Sort by score and limit
        results.sort(key=lambda x: x.get('score', 0), reverse=True)
        results = results[:5]  # Show top 5 results
        
        # Build response with card format
        intro_text = (
            f"I've found relevant messages for '<b>{escape_html(keyword)}</b>'.\n"
            if language == "en"
            else f"Нашёл сообщения по запросу '<b>{escape_html(keyword)}</b>'.\n"
        )
        
        # Header
        message_word = "message" if len(results) == 1 else "messages"
        if language == "ru":
            message_word = "сообщение" if len(results) == 1 else "сообщения" if len(results) < 5 else "сообщений"
        
        response_parts = [
            intro_text,
            "━━━━━━━━━━━━━━━━━━━━",
            f"📚 Found {len(results)} {message_word}\n" if language == "en"
            else f"📚 Найдено {len(results)} {message_word}\n"
        ]
        
        # Build message cards
        for i, result in enumerate(results, 1):
            doc = result.get('doc', result)
            
            sender = doc.get('sender_name', 'Unknown')
            text = doc.get('message_text', '')
            date = doc.get('message_date', '')
            message_id = doc.get('message_id', '')
            
            # Format date
            if date:
                try:
                    dt = datetime.fromisoformat(date.replace('Z', '+00:00'))
                    date_str = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    date_str = date[:16]
            else:
                date_str = "Unknown date"
            
            # Clean text: replace newlines with spaces and truncate
            text = text.replace('\n', ' ').replace('\r', ' ')
            max_text_length = 150
            if len(text) > max_text_length:
                text = text[:max_text_length] + "..."
            
            # Build deeplink
            deeplink_url = None
            if message_id:
                try:
                    parts = message_id.split('_')
                    telegram_msg_id = parts[-1] if parts else None
                    
                    if telegram_msg_id and telegram_msg_id.isdigit():
                        group_id_str = str(group_id)
                        if group_id_str.startswith('-100'):
                            chat_id_for_link = group_id_str[4:]
                            if chat_id_for_link and telegram_msg_id:
                                deeplink_url = f"https://t.me/c/{chat_id_for_link}/{telegram_msg_id}"
                except Exception as e:
                    logger.debug(f"Failed to generate deeplink: {e}")
            
            # Build card with simple box decoration
            card_lines = [
                f"┌─ 👤 <b>{sender}</b> • {date_str}",
                f"\"{escape_html(text)}\""
            ]
            
            # Add raw URL link if available
            if deeplink_url:
                card_lines.append(f"🔗 {deeplink_url}")
            
            # Add divider after each message
            card_lines.append("└─────")
            
            response_parts.append("\n".join(card_lines) + "\n")
        
        response_parts.append("━━━━━━━━━━━━━━━━━━━━")
        
        # Send results
        final_response = "\n".join(response_parts)
        await status_message.edit_text(final_response, parse_mode="HTML")
        
        logger.info(f"✅ Group search for '{keyword}' returned {len(results)} results")
        
    except Exception as e:
        logger.error(f"Error in /search (group): {e}", exc_info=True)
        try:
            group_service = await get_group_service()
            language = await group_service.get_group_language(group_id)
            error_msg = "❌ Search error. Please try again." if language == "en" else "❌ Ошибка поиска. Попробуйте снова."
        except:
            error_msg = "❌ Search error. Please try again."
        await message.answer(error_msg, parse_mode="HTML")


@router.message(lambda msg: msg.chat.type in ("group", "supergroup"), Command("import"))
async def handle_import_in_group(message: Message):
    """
    Handle /import command in groups (admin only).
    Placeholder for history import feature.
    """
    try:
        if not message.from_user:
            return
        
        user_id = message.from_user.id
        group_id = message.chat.id
        
        # Get group language
        group_service = await get_group_service()
        language = await group_service.get_group_language(group_id)
        
        # Check if admin
        is_admin = await is_user_admin_in_group(message.bot, group_id, user_id)
        
        if not is_admin:
            await message.answer(
                _('group.cmd.admin_only', language),
                parse_mode="HTML"
            )
            return
        
        if language == "en":
            await message.answer(
                "📚 <b>History Import (Coming Soon)</b>\n\n"
                "This feature will allow admins to:\n"
                "• Import past group messages\n"
                "• Build comprehensive knowledge base\n"
                "• Make history searchable\n\n"
                "<i>Use /groups command in DM when available!</i>",
                parse_mode="HTML"
            )
        else:  # Russian
            await message.answer(
                "📚 <b>Импорт истории (скоро)</b>\n\n"
                "Эта функция позволит админам:\n"
                "• Импортировать прошлые сообщения группы\n"
                "• Создать полную базу знаний\n"
                "• Сделать историю доступной для поиска\n\n"
                "<i>Используйте команду /groups в ЛС, когда будет доступно!</i>",
                parse_mode="HTML"
            )
        logger.info(f"📚 /import command in group {group_id} by admin {user_id}")
        
    except Exception as e:
        logger.error(f"Failed to handle /import in group: {e}")


@router.message(lambda msg: msg.chat.type in ("group", "supergroup"), Command("reset"))
async def handle_reset_in_group(message: Message):
    """
    Handle /reset command in groups (admin only).
    Resets bot data for the group with confirmation.
    """
    try:
        if not message.from_user:
            return
        
        user_id = message.from_user.id
        group_id = message.chat.id
        group_title = message.chat.title or f"Group {group_id}"
        
        # Get group KB info and language
        group_service = await get_group_service()
        kb_index = await group_service.get_group_kb_index(group_id)
        language = await group_service.get_group_language(group_id)
        
        # Check if admin
        is_admin = await is_user_admin_in_group(message.bot, group_id, user_id)
        
        if not is_admin:
            await message.answer(
                _('group.cmd.admin_only', language),
                parse_mode="HTML"
            )
            return
        
        if not kb_index:
            if language == "en":
                await message.answer(
                    "ℹ️ <b>No data to reset.</b>\n\n"
                    "This group hasn't been set up yet.",
                    parse_mode="HTML"
                )
            else:  # Russian
                await message.answer(
                    "ℹ️ <b>Нет данных для сброса.</b>\n\n"
                    "Эта группа еще не настроена.",
                    parse_mode="HTML"
                )
            return
        
        # Send confirmation request with inline keyboard
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        if language == "en":
            confirm_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="⚠️ Yes, Reset Everything",
                        callback_data=f"group_reset_confirm:{group_id}:{user_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Cancel",
                        callback_data="group_reset_cancel"
                    )
                ]
            ])
            
            warning_text = f"""⚠️ <b>WARNING: Reset Group Data</b>

<b>Group:</b> {group_title}
<b>KB Index:</b> <code>{kb_index}</code>

<b>This will:</b>
• ❌ Delete all indexed messages
• ❌ Clear group knowledge base
• ❌ Remove group configuration
• ❌ Reset all group settings

<b>This action CANNOT be undone!</b>

Are you sure you want to reset all bot data for this group?"""
        else:  # Russian
            confirm_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="⚠️ Да, сбросить всё",
                        callback_data=f"group_reset_confirm:{group_id}:{user_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌",
                        callback_data="group_reset_cancel"
                    )
                ]
            ])
            
            warning_text = f"""⚠️ <b>ВНИМАНИЕ: Сброс данных группы</b>

<b>Группа:</b> {group_title}
<b>KB Index:</b> <code>{kb_index}</code>

<b>Это приведет к:</b>
• ❌ Удалению всех проиндексированных сообщений
• ❌ Очистке базы знаний группы
• ❌ Удалению конфигурации группы
• ❌ Сбросу всех настроек группы

<b>Это действие НЕВОЗМОЖНО отменить!</b>

Вы уверены, что хотите сбросить все данные бота для этой группы?"""
        
        await message.answer(
            warning_text,
            reply_markup=confirm_keyboard,
            parse_mode="HTML"
        )
        
        logger.info(f"⚠️  /reset requested in group {group_id} by admin {user_id}")
        
    except Exception as e:
        logger.error(f"Failed to handle /reset in group: {e}")


# Callback handlers for group reset confirmation
from aiogram.types import CallbackQuery

@router.callback_query(lambda c: c.data and c.data.startswith("group_reset_confirm:"))
async def handle_reset_confirmation(callback: CallbackQuery):
    """Handle group reset confirmation."""
    try:
        # Parse callback data
        parts = callback.data.split(":")
        if len(parts) != 3:
            await callback.answer("❌ Invalid request", show_alert=True)
            return
        
        group_id = int(parts[1])
        requesting_user_id = int(parts[2])
        current_user_id = callback.from_user.id
        
        # Get group language
        group_service = await get_group_service()
        language = await group_service.get_group_language(group_id)
        
        # Verify the user clicking is the same user who requested reset
        if current_user_id != requesting_user_id:
            if language == "en":
                await callback.answer(
                    "⚠️ Only the admin who requested the reset can confirm it.",
                    show_alert=True
                )
            else:  # Russian
                await callback.answer(
                    "⚠️ Только админ, запросивший сброс, может подтвердить его.",
                    show_alert=True
                )
            return
        
        # Double-check admin status
        is_admin = await is_user_admin_in_group(callback.bot, group_id, current_user_id)
        if not is_admin:
            if language == "en":
                await callback.answer(
                    "⚠️ You must be an admin to reset group data.",
                    show_alert=True
                )
            else:  # Russian
                await callback.answer(
                    "⚠️ Вы должны быть администратором для сброса данных группы.",
                    show_alert=True
                )
            return
        
        # Perform the reset (group_service already retrieved above)
        
        # Get KB index before deleting
        kb_index = await group_service.get_group_kb_index(group_id)
        
        # Get all users in this group
        from luka_bot.models.group_link import GroupLink
        from luka_bot.core.loader import redis_client
        
        group_set_key = GroupLink.get_group_users_key(group_id)
        user_ids_bytes = await redis_client.smembers(group_set_key)
        user_ids = [int(uid.decode() if isinstance(uid, bytes) else uid) for uid in user_ids_bytes]
        
        logger.info(f"🗑️  Deleting group links for {len(user_ids)} users in group {group_id}")
        
        # Delete all group links for this group (complete removal, not just deactivation)
        deleted_count = 0
        for uid in user_ids:
            success = await group_service.delete_group_link(uid, group_id)
            if success:
                deleted_count += 1
        
        logger.info(f"🗑️  Deleted {deleted_count}/{len(user_ids)} group links")
        
        # Delete the group Thread
        from luka_bot.services.thread_service import get_thread_service
        thread_service = get_thread_service()
        thread = await thread_service.get_group_thread(group_id)
        
        if thread:
            # Delete thread directly from Redis
            thread_key = f"thread:{thread.thread_id}"
            await redis_client.delete(thread_key)
            
            # Delete thread history if exists
            history_key = f"thread_history:{thread.thread_id}"
            await redis_client.delete(history_key)
            
            logger.info(f"🗑️  Deleted group thread: {thread.thread_id}")
        
        # Delete GroupSettings and UserReputation data
        from luka_bot.services.moderation_service import get_moderation_service
        moderation_service = await get_moderation_service()
        
        # Delete GroupSettings
        settings_deleted = await moderation_service.delete_group_settings(group_id)
        if settings_deleted:
            logger.info(f"🗑️  Deleted GroupSettings for group {group_id}")
        
        # Delete all UserReputation data for this group
        reputation_count = await moderation_service.delete_all_group_reputations(group_id)
        if reputation_count > 0:
            logger.info(f"🗑️  Deleted {reputation_count} UserReputation records for group {group_id}")
        
        # Delete Elasticsearch KB index if it exists
        kb_deleted = False
        if kb_index:
            try:
                from luka_bot.services.elasticsearch_service import get_elasticsearch_service
                from luka_bot.core.config import settings
                
                if settings.ELASTICSEARCH_ENABLED:
                    es_service = await get_elasticsearch_service()
                    await es_service.delete_index(kb_index)
                    kb_deleted = True
                    logger.info(f"🗑️  Deleted ES KB index: {kb_index}")
            except Exception as e:
                logger.warning(f"⚠️  Failed to delete ES index {kb_index}: {e}")
        
        # Build success message
        if language == "en":
            success_parts = [
                "✅ <b>Group Data Reset Complete</b>\n",
                f"• {deleted_count} group link(s) deleted",
                "• Thread and configuration cleared",
                "• Moderation settings deleted"
            ]
            
            if reputation_count > 0:
                success_parts.append(f"• {reputation_count} user reputation(s) cleared")
            
            if kb_deleted:
                success_parts.append("• Knowledge base deleted")
            elif kb_index:
                success_parts.append("• ⚠️ KB index couldn't be deleted (may need manual cleanup)")
            
            success_parts.append("\n<i>💡 The bot will reinitialize if you send a new message or add it again.</i>")
            
            toast_message = "✅ Reset complete"
        else:  # Russian
            success_parts = [
                "✅ <b>Сброс данных группы завершен</b>\n",
                f"• {deleted_count} ссылок группы удалено",
                "• Тред и конфигурация очищены",
                "• Настройки модерации удалены"
            ]
            
            if reputation_count > 0:
                success_parts.append(f"• {reputation_count} репутаций пользователей очищено")
            
            if kb_deleted:
                success_parts.append("• База знаний удалена")
            elif kb_index:
                success_parts.append("• ⚠️ KB индекс не удалось удалить (может потребоваться ручная очистка)")
            
            success_parts.append("\n<i>💡 Бот реинициализируется при следующем сообщении или повторном добавлении.</i>")
            
            toast_message = "✅ Сброс завершен"
        
        # Update message to show success
        await callback.message.edit_text(
            "\n".join(success_parts),
            parse_mode="HTML"
        )
        
        await callback.answer(toast_message, show_alert=False)
        
        logger.info(f"✅ Group {group_id} reset by admin {current_user_id}")
        
    except Exception as e:
        logger.error(f"Failed to reset group: {e}")
        # Try to get language for error message
        try:
            group_service = await get_group_service()
            language = await group_service.get_group_language(group_id)
            error_msg = "❌ Error resetting group" if language == "en" else "❌ Ошибка сброса группы"
        except:
            error_msg = "❌ Error resetting group"
        await callback.answer(error_msg, show_alert=True)


@router.callback_query(lambda c: c.data == "group_reset_cancel")
async def handle_reset_cancel(callback: CallbackQuery):
    """Handle group reset cancellation."""
    try:
        # Try to determine language from the message
        # Since we don't have group_id in callback data for cancel, default to English
        # But we can try to extract it from the original message
        language = "en"  # Default
        
        try:
            # Try to extract group_id from the original warning message
            if callback.message and callback.message.text:
                import re
                # Look for Group ID in the message
                match = re.search(r'Group ID.*?(-?\d+)', callback.message.text)
                if match:
                    group_id = int(match.group(1))
                    group_service = await get_group_service()
                    language = await group_service.get_group_language(group_id)
        except Exception as e:
            logger.debug(f"Couldn't determine language for cancel: {e}")
        
        if language == "en":
            await callback.message.edit_text(
                "✅ <b>Reset Cancelled</b>\n\n"
                "No changes were made to the group.",
                parse_mode="HTML"
            )
            await callback.answer("Cancelled")
        else:  # Russian
            await callback.message.edit_text(
                "✅ <b>Сброс отменен</b>\n\n"
                "Никакие изменения не были внесены в группу.",
                parse_mode="HTML"
            )
            await callback.answer("Отменено")
        
        logger.info(f"❌ Group reset cancelled by user {callback.from_user.id}")
        
    except Exception as e:
        logger.error(f"Failed to cancel reset: {e}")
        await callback.answer("Error")

