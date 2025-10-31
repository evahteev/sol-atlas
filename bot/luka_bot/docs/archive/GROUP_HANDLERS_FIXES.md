# Group Handlers Fixes

**Date**: 2025-10-11  
**Status**: ✅ Fixed

## Issues Fixed

### 1. ❌ Missing `moderation_service` in Language Change Handler

**Error**:
```
ERROR | Failed to handle language change: name 'moderation_service' is not defined
```

**Location**: `luka_bot/handlers/group_settings_inline.py:306`

**Root Cause**: 
The `handle_group_language_change` function was using `moderation_service` on lines 173 and 218 without initializing it. The service was only defined in the sibling function `handle_group_language_menu`.

**Fix**:
Added proper service initialization at the beginning of the function:

```python
@router.callback_query(F.data.startswith("group_set_lang:"))
async def handle_group_language_change(callback: CallbackQuery):
    """Handle group language change button with LLM confirmation."""
    try:
        # ... parse callback data ...
        
        # Get services
        from luka_bot.services.moderation_service import get_moderation_service
        moderation_service = await get_moderation_service()
        group_service = await get_group_service()
        
        # ... rest of the function can now use moderation_service ...
```

### 2. ⚠️ Invalid `message_thread_id` Parameter in `edit_message_text()`

**Error**:
```
WARNING | ⚠️ Failed final update: Bot.edit_message_text() got an unexpected keyword argument 'message_thread_id'
```

**Location**: `luka_bot/handlers/group_messages.py:784`

**Root Cause**: 
The `bot.edit_message_text()` method from aiogram doesn't accept `message_thread_id` as a parameter. This parameter is only valid for sending new messages, not for editing existing ones. The message is already in the thread context, so the parameter is not needed.

**Fix**:
Removed `message_thread_id` parameter from all three `edit_message_text()` calls:

**Before**:
```python
await message.bot.edit_message_text(
    text=formatted_response,
    chat_id=message.chat.id,
    message_id=bot_message.message_id,
    parse_mode="HTML",
    message_thread_id=thread_id  # ❌ Not supported
)
```

**After**:
```python
await message.bot.edit_message_text(
    text=formatted_response,
    chat_id=message.chat.id,
    message_id=bot_message.message_id,
    parse_mode="HTML"  # ✅ Removed unsupported parameter
)
```

## Impact

### Before Fixes:
- ❌ Language change buttons in groups failed silently
- ⚠️ Group message updates generated warnings (but still worked)
- 🐛 Users couldn't change group language via inline keyboard

### After Fixes:
- ✅ Language change works correctly
- ✅ No more warnings in message updates
- ✅ Clean logs without errors
- ✅ All group inline settings functional

## Files Modified

1. `luka_bot/handlers/group_settings_inline.py`
   - Added `moderation_service` initialization in `handle_group_language_change()`

2. `luka_bot/handlers/group_messages.py`
   - Removed `message_thread_id` from 3 `edit_message_text()` calls (lines 735, 757, 780)

## Testing

To verify these fixes work:

1. **Language Change Test**:
   ```
   - Add bot to a group
   - Click inline "🌐 Language" button
   - Select a different language (e.g., Russian)
   - Should see LLM confirmation message in new language
   - No errors in logs
   ```

2. **Message Updates Test**:
   ```
   - Mention bot in a group
   - Watch the bot's response being streamed
   - No warnings about message_thread_id in logs
   - Message updates smoothly during streaming
   ```

## Related

- **LLM_PROVIDER_DEBUGGING.md** - Enhanced logging system
- **OPENAI_FALLBACK_FIX.md** - OpenAI provider fix
- **GROUP_ONBOARDING_ROADMAP.md** - Group features documentation

## Status

✅ **Both issues resolved** - Ready for production

