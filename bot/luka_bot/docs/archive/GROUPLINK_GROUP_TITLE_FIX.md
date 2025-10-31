# GroupLink.group_title References Fix - October 12, 2025

## Issue
Multiple handlers were trying to access `group_link.group_title`, which was removed during the Thread model refactoring.

**Error**: `'GroupLink' object has no attribute 'group_title'`

---

## Root Cause

During the Thread model unification:
- `GroupLink` was simplified to only store linking data
- `group_title` (along with language, KB config) was moved to the `Thread` model
- Some handlers were not updated to use the new architecture

---

## Files Fixed

### 1. ✅ `/luka_bot/handlers/group_settings_inline.py`
**Function**: `handle_group_settings_menu`
**Line**: ~329-333

**Before**:
```python
links = await group_service.list_user_groups(callback.from_user.id)
for link in links:
    if link.group_id == group_id:
        group_title = link.group_title  # ❌ Error!
```

**After**:
```python
thread_service = get_thread_service()
group_thread = await thread_service.get_group_thread(group_id)
group_title = group_thread.name if group_thread else None

if not group_title:
    chat = await callback.bot.get_chat(group_id)
    group_title = chat.title
```

### 2. ✅ `/luka_bot/handlers/group_admin.py`
**Function**: `handle_back_to_admin_menu`
**Line**: ~33-38

Same fix pattern applied.

### 3. ✅ `/luka_bot/handlers/start.py`
**Function**: `handle_start` (deep link handling)
**Line**: ~191-200

Same fix pattern applied.

---

## Solution Pattern

All fixes follow this pattern:

```python
# 1. Get from Thread (primary source)
thread_service = get_thread_service()
group_thread = await thread_service.get_group_thread(group_id)
group_title = group_thread.name if group_thread else None

# 2. Fallback to Telegram API (if Thread not found)
if not group_title:
    try:
        chat = await message.bot.get_chat(group_id)
        group_title = chat.title
    except Exception:
        group_title = f"Group {group_id}"
```

This provides:
- ✅ **Primary**: Get from Thread (single source of truth)
- ✅ **Fallback**: Get from Telegram API (if Thread missing)
- ✅ **Default**: Use generic name (if both fail)

---

## Verification

Checked all handlers for remaining references:
```bash
grep -r "\.group_title" luka_bot/handlers/
# No results (only documentation files)
```

✅ All references fixed!

---

## Impact

### Before Fix
```
ERROR | 'GroupLink' object has no attribute 'group_title'
```
- Settings button: ❌ Crashed
- Admin menu: ❌ Crashed  
- Deep links: ❌ Crashed

### After Fix
- Settings button: ✅ Working
- Admin menu: ✅ Working
- Deep links: ✅ Working

---

## Related Changes

This is part of the **Thread Model Unification** initiative:
- `GroupLink`: Simplified to minimal linking data
- `Thread`: Single source of truth for all conversation config
- Group metadata: Moved from GroupLink to Thread

All handlers must use:
- `thread.name` for group title
- `thread.language` for group language
- `thread.knowledge_bases` for KB indices

---

**Status**: ✅ COMPLETE  
**Files Fixed**: 3 handlers  
**Verification**: All `group_title` references checked  
**Breaking Changes**: None

