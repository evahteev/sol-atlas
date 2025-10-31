# Moderation Integration Guide

## Overview

This document outlines the exact changes needed to integrate the moderation system into `handlers/group_messages.py`.

**Status**: Phase 1 & 2 Complete (Models + Service)  
**Next**: Phase 3 - Handler Integration

---

## File: handlers/group_messages.py

### Change 1: Add Imports (at top of file)

```python
# Add after existing imports
from luka_bot.services.moderation_service import get_moderation_service
from luka_bot.utils.content_detection import (
    check_stoplist,
    match_patterns,
    contains_links,
    is_service_message
)
```

### Change 2: Add Pre-processing Filters

**Location**: After line 228 (after basic extraction), BEFORE auto-initialization

```python
async def handle_group_message(message: Message) -> None:
    """..."""
    try:
        group_id = message.chat.id
        user_id = message.from_user.id if message.from_user else None
        message_text = message.text or message.caption or ""
        
        if not message_text or not user_id:
            return
        
        # ========================================================================
        # STEP 1: PRE-PROCESSING FILTERS (Fast, rule-based)
        # ========================================================================
        
        # Get moderation service
        moderation_service = await get_moderation_service()
        
        # Get GroupSettings (or skip moderation if not configured yet)
        group_settings = await moderation_service.get_group_settings(group_id)
        
        if group_settings:
            # Check service messages
            if group_settings.delete_service_messages:
                content_type = message.content_type
                if is_service_message(content_type, group_settings.service_message_types):
                    logger.info(f"🗑️ Deleting service message: {content_type}")
                    try:
                        await message.delete()
                    except Exception as e:
                        logger.warning(f"Failed to delete service message: {e}")
                    return  # Stop processing
            
            # Check stoplist words
            if group_settings.stoplist_enabled:
                matched_word = check_stoplist(
                    message_text,
                    group_settings.stoplist_words,
                    group_settings.stoplist_case_sensitive
                )
                if matched_word:
                    logger.info(f"🚫 Stoplist violation: '{matched_word}' by user {user_id}")
                    try:
                        await message.delete()
                        # Send notification to user
                        try:
                            await message.bot.send_message(
                                user_id,
                                f"⚠️ Your message in {message.chat.title} was removed (forbidden word: {matched_word})"
                            )
                        except:
                            pass  # User may have blocked bot
                    except Exception as e:
                        logger.warning(f"Failed to delete stoplist message: {e}")
                    return  # Stop processing
            
            # Check content type filters
            if group_settings.delete_links and contains_links(message_text):
                logger.info(f"🚫 Link violation by user {user_id}")
                try:
                    await message.delete()
                except:
                    pass
                return
            
            if group_settings.delete_forwarded and message.forward_origin:
                logger.info(f"🚫 Forwarded message deleted by user {user_id}")
                try:
                    await message.delete()
                except:
                    pass
                return
            
            # Check media types
            content_type = message.content_type
            if (group_settings.delete_images and content_type == "photo") or \
               (group_settings.delete_videos and content_type == "video") or \
               (group_settings.delete_stickers and content_type == "sticker"):
                logger.info(f"🚫 Media type violation: {content_type} by user {user_id}")
                try:
                    await message.delete()
                except:
                    pass
                return
            
            # Check regex patterns
            matched_pattern = match_patterns(message_text, group_settings.pattern_filters)
            if matched_pattern:
                action = matched_pattern.get("action", "warn")
                if action == "delete":
                    logger.info(f"🚫 Pattern violation by user {user_id}: {matched_pattern.get('description')}")
                    try:
                        await message.delete()
                    except:
                        pass
                    return
        
        # ========================================================================
        # Continue with existing logic (auto-initialization, etc.)
        # ========================================================================
        
        # Check if this message is in a topic (supergroup thread)
        thread_id = getattr(message, 'message_thread_id', None)
        
        # ... rest of existing code ...
```

### Change 3: Add Background Moderation

**Location**: After auto-initialization, BEFORE topic greeting (around line 410)

```python
        # ========================================================================
        # STEP 2: BACKGROUND MODERATION (LLM evaluation with moderation_prompt)
        # ========================================================================
        
        # Get GroupSettings (reload if needed)
        if not group_settings:
            group_settings = await moderation_service.get_group_settings(group_id)
        
        # Perform background moderation (evaluates ALL messages)
        moderation_result = None
        if group_settings and group_settings.moderation_enabled:
            logger.info(f"🛡️ Background moderation for message from user {user_id}")
            
            moderation_result = await moderation_service.evaluate_message_moderation(
                message_text=message_text,
                group_settings=group_settings,
                user_id=user_id,
                group_id=group_id
            )
            
            # Take action based on moderation result
            action = moderation_result.get("action", "none")
            violation_type = moderation_result.get("violation")
            
            if action == "delete" and violation_type:
                logger.warning(f"🚫 Auto-deleting message from user {user_id}: {violation_type}")
                try:
                    await message.delete()
                    # Notify user
                    try:
                        reason = moderation_result.get("reason", "Violation detected")
                        await message.bot.send_message(
                            user_id,
                            f"⚠️ Your message in {message.chat.title} was removed.\n"
                            f"Reason: {reason}\n\n"
                            f"Violation type: {violation_type}"
                        )
                    except:
                        pass
                except Exception as e:
                    logger.warning(f"Failed to delete violating message: {e}")
                return  # Stop processing
            
            elif action == "warn" and violation_type:
                logger.warning(f"⚠️ Warning for user {user_id}: {violation_type}")
                # Send warning (non-blocking)
                try:
                    reason = moderation_result.get("reason", "Content warning")
                    await message.bot.send_message(
                        user_id,
                        f"⚠️ Warning about your message in {message.chat.title}.\n"
                        f"Reason: {reason}\n\n"
                        f"Please follow group rules."
                    )
                except:
                    pass
        
        # ========================================================================
        # STEP 3: UPDATE USER REPUTATION
        # ========================================================================
        
        if group_settings and group_settings.reputation_enabled and moderation_result:
            # Determine if message is a reply or mention
            is_reply = bool(message.reply_to_message)
            is_mention = "@" in message_text  # Simplified check
            
            # Update reputation
            reputation = await moderation_service.update_user_reputation(
                user_id=user_id,
                group_id=group_id,
                moderation_result=moderation_result,
                group_settings=group_settings,
                is_reply=is_reply,
                is_mention=is_mention
            )
            
            # Check for new achievements
            new_achievements = await moderation_service.check_achievements(
                user_id=user_id,
                group_id=group_id,
                group_settings=group_settings
            )
            
            # Announce achievements
            if new_achievements and group_settings.public_achievements:
                for achievement in new_achievements:
                    icon = achievement.get("icon", "🏆")
                    name = achievement.get("name", "Achievement")
                    description = achievement.get("description", "")
                    try:
                        await message.reply(
                            f"{icon} Congratulations to {message.from_user.mention_html()}!\n\n"
                            f"<b>{name}</b>: {description}",
                            parse_mode="HTML"
                        )
                    except:
                        pass
            
            # Check if user was banned
            if reputation.is_banned:
                logger.warning(f"🚫 User {user_id} was auto-banned in group {group_id}")
                try:
                    # Try to ban user from group (requires bot to be admin)
                    from datetime import timedelta
                    if reputation.ban_until:
                        await message.bot.ban_chat_member(
                            group_id,
                            user_id,
                            until_date=reputation.ban_until
                        )
                    else:
                        # Permanent ban
                        await message.bot.ban_chat_member(group_id, user_id)
                    
                    if group_settings.notify_bans:
                        await message.answer(
                            f"🚫 User {message.from_user.mention_html()} has been banned.\n"
                            f"Reason: {reputation.ban_reason}",
                            parse_mode="HTML"
                        )
                except Exception as e:
                    logger.error(f"Failed to ban user: {e}")
                
                return  # Stop processing
        
        # ========================================================================
        # Continue with existing logic (topic greeting, mentions, indexing)
        # ========================================================================
        
        # ... rest of existing code ...
```

### Change 4: Verify Mention Handler

**Location**: The existing mention handler (around line 489-657) already uses Thread.system_prompt correctly.

**Verification needed**: Ensure the mention handler code around line 555-559 uses:
```python
async for chunk in llm_service.stream_response(
    llm_input, 
    user_id=user_id, 
    thread_id=group_thread.thread_id,
    thread=group_thread  # ← This ensures Thread.system_prompt is used
):
```

This is CORRECT - it uses `thread=group_thread`, which means it will use `Thread.system_prompt` for conversation, NOT `GroupSettings.moderation_prompt`.

✅ **No changes needed** - mention handler already uses Thread.system_prompt.

---

## Summary of Changes

### Files Modified:
1. `handlers/group_messages.py` - Add 3 code blocks (~150 lines)

### Key Points:
1. ✅ Pre-processing happens FIRST (fast filters)
2. ✅ Background moderation evaluates ALL messages (with moderation_prompt)
3. ✅ Reputation updates happen after moderation
4. ✅ Mention handler stays unchanged (uses Thread.system_prompt)
5. ✅ Two-prompt architecture maintained:
   - `GroupSettings.moderation_prompt` → Background evaluation
   - `Thread.system_prompt` → Active conversation

---

## Testing Checklist

After integration:
- [ ] Send message with stoplist word → deleted
- [ ] Send spam → moderation detects, points deducted
- [ ] Send helpful message → points added
- [ ] Mention bot → uses Thread.system_prompt (conversational)
- [ ] Reach violation threshold → auto-ban
- [ ] Earn achievement → notification shown

---

## Next Steps

1. Implement these changes in `group_messages.py`
2. Update `handle_bot_added_to_group` to create default GroupSettings
3. Update `handle_bot_added_to_group` auto-initialization to create GroupSettings
4. Update `/reset` command to delete GroupSettings + UserReputation
5. Create admin UI for moderation settings
6. Add i18n strings
7. Create documentation
8. Test thoroughly

---

**Status**: Integration plan complete  
**Ready for**: Implementation

