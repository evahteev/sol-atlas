"""
User Reputation Viewer

Allows admins to view detailed reputation information for group members.
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ChatType
from loguru import logger

from luka_bot.services.moderation_service import get_moderation_service
from luka_bot.services.group_service import get_group_service
from luka_bot.utils.permissions import is_user_admin_in_group

router = Router()


@router.callback_query(F.data.startswith("mod_view_reputation:"))
async def handle_view_reputation(callback: CallbackQuery):
    """
    View a user's reputation details.
    
    Callback format: mod_view_reputation:group_id:user_id
    """
    try:
        parts = callback.data.split(":")
        if len(parts) != 3:
            await callback.answer("❌ Invalid request", show_alert=True)
            return
        
        group_id = int(parts[1])
        target_user_id = int(parts[2])
        admin_user_id = callback.from_user.id
        
        # Admin check
        if not await is_user_admin_in_group(callback.bot, group_id, admin_user_id):
            await callback.answer("⚠️ Admin only", show_alert=True)
            return
        
        # Get services
        moderation_service = await get_moderation_service()
        group_service = await get_group_service()
        
        # Get reputation
        reputation = await moderation_service.get_user_reputation(target_user_id, group_id)
        language = await group_service.get_group_language(group_id)
        
        # Get user info
        try:
            user = await callback.bot.get_chat(target_user_id)
            user_name = user.full_name or f"User {target_user_id}"
        except:
            user_name = f"User {target_user_id}"
        
        # Format reputation details
        if language == "en":
            # Activity stats
            activity_text = f"""👤 <b>{user_name}</b>
🆔 User ID: <code>{target_user_id}</code>

<b>📊 Stats:</b>
  • Total points: <b>{reputation.points}</b>
  • Messages sent: {reputation.message_count}
  • Helpful messages: {reputation.helpful_messages}
  • Quality replies: {reputation.quality_replies}
  • Replies: {reputation.replies_count}
  • Bot mentions: {reputation.mentions_count}"""
            
            # Violations
            if reputation.warnings > 0 or reputation.violations > 0:
                activity_text += f"""

<b>⚠️ Violations:</b>
  • Warnings: {reputation.warnings}
  • Violations: {reputation.violations}"""
                
                if reputation.last_violation_at:
                    activity_text += f"\n  • Last violation: {reputation.last_violation_at.strftime('%Y-%m-%d %H:%M')}"
            
            # Ban status
            if reputation.is_banned:
                ban_type = "Permanent" if not reputation.ban_until else f"Until {reputation.ban_until.strftime('%Y-%m-%d %H:%M')}"
                activity_text += f"""

<b>🚫 Ban Status:</b>
  • Status: <b>BANNED</b>
  • Type: {ban_type}
  • Reason: {reputation.ban_reason or 'Not specified'}"""
            
            # Achievements
            if reputation.achievements:
                activity_text += f"""

<b>🏆 Achievements ({len(reputation.achievements)}):</b>"""
                for achievement in reputation.achievement_history[:5]:  # Show latest 5
                    icon = achievement.get("icon", "🏆")
                    name = achievement.get("name", "Achievement")
                    points = achievement.get("points", 0)
                    activity_text += f"\n  {icon} {name} (+{points} pts)"
                
                if len(reputation.achievements) > 5:
                    activity_text += f"\n  <i>...and {len(reputation.achievements) - 5} more</i>"
            
            # Recent violations
            if reputation.violation_history:
                activity_text += f"""

<b>📜 Recent Violations ({len(reputation.violation_history)}):</b>"""
                for violation in reputation.violation_history[-3:]:  # Show latest 3
                    v_type = violation.get("type", "unknown")
                    reason = violation.get("reason", "No reason")
                    penalty = violation.get("penalty", 0)
                    activity_text += f"\n  • {v_type.capitalize()}: {reason} ({penalty} pts)"
            
            # Activity timeline
            if reputation.first_message_at:
                activity_text += f"""

<b>📅 Timeline:</b>
  • First message: {reputation.first_message_at.strftime('%Y-%m-%d')}"""
                if reputation.last_message_at:
                    activity_text += f"\n  • Last message: {reputation.last_message_at.strftime('%Y-%m-%d')}"
        
        else:  # Russian
            # Activity stats
            activity_text = f"""👤 <b>{user_name}</b>
🆔 ID пользователя: <code>{target_user_id}</code>

<b>📊 Статистика:</b>
  • Всего очков: <b>{reputation.points}</b>
  • Сообщений отправлено: {reputation.message_count}
  • Полезных сообщений: {reputation.helpful_messages}
  • Качественных ответов: {reputation.quality_replies}
  • Ответов: {reputation.replies_count}
  • Упоминаний бота: {reputation.mentions_count}"""
            
            # Violations
            if reputation.warnings > 0 or reputation.violations > 0:
                activity_text += f"""

<b>⚠️ Нарушения:</b>
  • Предупреждений: {reputation.warnings}
  • Нарушений: {reputation.violations}"""
                
                if reputation.last_violation_at:
                    activity_text += f"\n  • Последнее нарушение: {reputation.last_violation_at.strftime('%Y-%m-%d %H:%M')}"
            
            # Ban status
            if reputation.is_banned:
                ban_type = "Постоянно" if not reputation.ban_until else f"До {reputation.ban_until.strftime('%Y-%m-%d %H:%M')}"
                activity_text += f"""

<b>🚫 Статус бана:</b>
  • Статус: <b>ЗАБАНЕН</b>
  • Тип: {ban_type}
  • Причина: {reputation.ban_reason or 'Не указана'}"""
            
            # Achievements
            if reputation.achievements:
                activity_text += f"""

<b>🏆 Достижения ({len(reputation.achievements)}):</b>"""
                for achievement in reputation.achievement_history[:5]:
                    icon = achievement.get("icon", "🏆")
                    name = achievement.get("name", "Достижение")
                    points = achievement.get("points", 0)
                    activity_text += f"\n  {icon} {name} (+{points} очков)"
                
                if len(reputation.achievements) > 5:
                    activity_text += f"\n  <i>...и еще {len(reputation.achievements) - 5}</i>"
            
            # Recent violations
            if reputation.violation_history:
                activity_text += f"""

<b>📜 Недавние нарушения ({len(reputation.violation_history)}):</b>"""
                for violation in reputation.violation_history[-3:]:
                    v_type = violation.get("type", "unknown")
                    reason = violation.get("reason", "Нет причины")
                    penalty = violation.get("penalty", 0)
                    activity_text += f"\n  • {v_type.capitalize()}: {reason} ({penalty} очков)"
            
            # Activity timeline
            if reputation.first_message_at:
                activity_text += f"""

<b>📅 Временная шкала:</b>
  • Первое сообщение: {reputation.first_message_at.strftime('%Y-%m-%d')}"""
                if reputation.last_message_at:
                    activity_text += f"\n  • Последнее сообщение: {reputation.last_message_at.strftime('%Y-%m-%d')}"
        
        # Create action buttons
        keyboard_buttons = []
        
        if reputation.is_banned:
            # Unban button
            if language == "en":
                keyboard_buttons.append([
                    InlineKeyboardButton(
                        text="✅ Unban User",
                        callback_data=f"mod_unban:{group_id}:{target_user_id}"
                    )
                ])
            else:
                keyboard_buttons.append([
                    InlineKeyboardButton(
                        text="✅",
                        callback_data=f"mod_unban:{group_id}:{target_user_id}"
                    )
                ])
        else:
            # Ban button
            if language == "en":
                keyboard_buttons.append([
                    InlineKeyboardButton(
                        text="🚫 Ban User",
                        callback_data=f"mod_ban:{group_id}:{target_user_id}"
                    )
                ])
            else:
                keyboard_buttons.append([
                    InlineKeyboardButton(
                        text="🚫",
                        callback_data=f"mod_ban:{group_id}:{target_user_id}"
                    )
                ])
        
        # Close button
        if language == "en":
            keyboard_buttons.append([
                InlineKeyboardButton(text="❌ Close", callback_data="mod_close_reputation")
            ])
        else:
            keyboard_buttons.append([
                InlineKeyboardButton(text="❌", callback_data="mod_close_reputation")
            ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        # Send as new message or edit
        await callback.message.answer(activity_text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer("👤 Reputation loaded")
        
    except Exception as e:
        logger.error(f"Failed to view reputation: {e}", exc_info=True)
        await callback.answer("❌ Error loading reputation", show_alert=True)


@router.callback_query(F.data == "mod_close_reputation")
async def handle_close_reputation(callback: CallbackQuery):
    """Close reputation viewer."""
    try:
        await callback.message.delete()
        await callback.answer("Closed")
    except Exception as e:
        logger.error(f"Failed to close reputation: {e}")


@router.callback_query(F.data.startswith("mod_ban:"))
async def handle_ban_user(callback: CallbackQuery):
    """Ban a user (admin action)."""
    try:
        parts = callback.data.split(":")
        group_id = int(parts[1])
        target_user_id = int(parts[2])
        admin_user_id = callback.from_user.id
        
        # Admin check
        if not await is_user_admin_in_group(callback.bot, group_id, admin_user_id):
            await callback.answer("⚠️ Admin only", show_alert=True)
            return
        
        # Ban user
        moderation_service = await get_moderation_service()
        success = await moderation_service.ban_user(
            user_id=target_user_id,
            group_id=group_id,
            reason="Manual ban by admin",
            duration_hours=24,  # 24-hour ban by default
            banned_by=admin_user_id
        )
        
        if success:
            # Try to ban from Telegram group
            try:
                from datetime import datetime, timedelta
                ban_until = datetime.utcnow() + timedelta(hours=24)
                await callback.bot.ban_chat_member(group_id, target_user_id, until_date=ban_until)
            except Exception as e:
                logger.warning(f"Failed to ban from Telegram: {e}")
            
            await callback.answer("✅ User banned (24h)")
            await callback.message.delete()
        else:
            await callback.answer("❌ Failed to ban user", show_alert=True)
        
    except Exception as e:
        logger.error(f"Failed to ban user: {e}")
        await callback.answer("❌ Error", show_alert=True)


@router.callback_query(F.data.startswith("mod_unban:"))
async def handle_unban_user(callback: CallbackQuery):
    """Unban a user (admin action)."""
    try:
        parts = callback.data.split(":")
        group_id = int(parts[1])
        target_user_id = int(parts[2])
        admin_user_id = callback.from_user.id
        
        # Admin check
        if not await is_user_admin_in_group(callback.bot, group_id, admin_user_id):
            await callback.answer("⚠️ Admin only", show_alert=True)
            return
        
        # Unban user
        moderation_service = await get_moderation_service()
        success = await moderation_service.unban_user(target_user_id, group_id)
        
        if success:
            # Try to unban from Telegram group
            try:
                await callback.bot.unban_chat_member(group_id, target_user_id, only_if_banned=True)
            except Exception as e:
                logger.warning(f"Failed to unban from Telegram: {e}")
            
            await callback.answer("✅ User unbanned")
            await callback.message.delete()
        else:
            await callback.answer("❌ Failed to unban user", show_alert=True)
        
    except Exception as e:
        logger.error(f"Failed to unban user: {e}")
        await callback.answer("❌ Error", show_alert=True)


# Command to check own reputation
@router.message(lambda msg: msg.chat.type in ("group", "supergroup"), Command("reputation"))
async def handle_reputation_command(message: Message):
    """
    Allow users to check their own reputation in the group.

    Usage: /reputation or /reputation @username (admin only)

    Note: Filter uses strings instead of ChatType enum for reliable matching
    """
    try:
        if not message.from_user:
            return
        
        user_id = message.from_user.id
        group_id = message.chat.id
        
        # Get language
        group_service = await get_group_service()
        language = await group_service.get_group_language(group_id)
        
        # Check if checking another user (admin only)
        target_user_id = user_id
        if message.text and len(message.text.split()) > 1:
            # Admin trying to check another user
            is_admin = await is_user_admin_in_group(message.bot, group_id, user_id)
            if not is_admin:
                if language == "en":
                    await message.answer("⚠️ You can only check your own reputation.")
                else:
                    await message.answer("⚠️ Вы можете проверить только свою репутацию.")
                return
            
            # Parse mentioned user (simplified)
            # In production, you'd use message.entities to properly parse mentions
            if language == "en":
                await message.answer("💡 Use the inline button in /moderation → Leaderboard to view user reputations.")
            else:
                await message.answer("💡 Используйте кнопку в /moderation → Рейтинг для просмотра репутации пользователей.")
            return
        
        # Get reputation
        moderation_service = await get_moderation_service()
        reputation = await moderation_service.get_user_reputation(target_user_id, group_id)
        
        # Format simple message
        if language == "en":
            response = f"""📊 <b>Your Reputation</b>

💰 Points: <b>{reputation.points}</b>
✅ Helpful messages: {reputation.helpful_messages}
⭐ Quality replies: {reputation.quality_replies}
📨 Total messages: {reputation.message_count}
⚠️ Warnings: {reputation.warnings}
🚫 Violations: {reputation.violations}"""
            
            if reputation.achievements:
                response += f"\n🏆 Achievements: {len(reputation.achievements)}"
            
            if reputation.is_banned:
                response += "\n\n🚫 <b>You are currently banned.</b>"
        
        else:  # Russian
            response = f"""📊 <b>Ваша репутация</b>

💰 Очков: <b>{reputation.points}</b>
✅ Полезных сообщений: {reputation.helpful_messages}
⭐ Качественных ответов: {reputation.quality_replies}
📨 Всего сообщений: {reputation.message_count}
⚠️ Предупреждений: {reputation.warnings}
🚫 Нарушений: {reputation.violations}"""
            
            if reputation.achievements:
                response += f"\n🏆 Достижений: {len(reputation.achievements)}"
            
            if reputation.is_banned:
                response += "\n\n🚫 <b>Вы сейчас забанены.</b>"
        
        await message.answer(response, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Failed to handle /reputation: {e}")

