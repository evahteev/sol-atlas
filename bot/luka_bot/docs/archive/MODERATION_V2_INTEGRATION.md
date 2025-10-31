# Moderation V2 - Integration Guide

**Status**: Implementation complete, integration pending  
**Files created**:
- `services/reply_tracker_service.py` ✅
- `utils/background_tasks.py` ✅
- `handlers/moderation_background.py` ✅

---

## 🎯 What Changed

### V1 (Old - Blocking)
```python
# In handle_group_message():

# BLOCKING - waits up to 5 seconds!
if group_settings and group_settings.moderation_enabled:
    moderation_result = await asyncio.wait_for(
        moderation_service.evaluate_message_moderation(...),
        timeout=5.0
    )
    # Handle result immediately
    if moderation_result.get("action") == "delete":
        await message.delete()
    # Update reputation
    reputation = await moderation_service.update_user_reputation(...)
    # Check achievements
    # Check ban threshold

# Then continue with mention check (5 seconds later!)
if is_mentioned:
    # Generate bot reply
```

### V2 (New - Non-Blocking)
```python
# In handle_group_message():

# NON-BLOCKING - fires and continues immediately!
if group_settings and group_settings.moderation_enabled:
    from luka_bot.handlers.moderation_background import fire_moderation_task
    
    fire_moderation_task(
        message_id=message.message_id,
        chat_id=message.chat.id,
        user_id=user_id,
        message_text=message_text,
        group_settings=group_settings
    )
    # Continues IMMEDIATELY (no waiting!)

# Check mentions (instant!)
if is_mentioned:
    # Generate bot reply (instant!)
    bot_message = await message.reply(full_response)
    
    # Track reply for retroactive deletion
    from luka_bot.services.reply_tracker_service import get_reply_tracker_service
    reply_tracker = get_reply_tracker_service()
    await reply_tracker.track_reply(
        chat_id=message.chat.id,
        user_message_id=message.message_id,
        bot_reply_id=bot_message.message_id
    )

# Meanwhile, moderation happens in background and can delete both messages!
```

---

## 📝 Integration Steps

### Step 1: Find the moderation section
Look for this in `handlers/group_messages.py`:

```python
# ========================================================================
# STEP 2: BACKGROUND MODERATION (LLM evaluation with moderation_prompt)
# ========================================================================

if group_settings and group_settings.moderation_enabled:
    logger.debug(f"🛡️ Background moderation for message from user {user_id}")
    try:
        import asyncio
        moderation_result = await asyncio.wait_for(
            moderation_service.evaluate_message_moderation(...),
            timeout=5.0
        )
    except asyncio.TimeoutError:
        logger.warning(f"⏱️ Background moderation timed out...")
        moderation_result = {"helpful": None, "violation": None, "action": "none"}
    # ... lots of code handling results, reputation, achievements, bans ...
```

### Step 2: Replace with V2 implementation

**REMOVE** the entire STEP 2 and STEP 3 sections (moderation + reputation).

**ADD** this instead:

```python
# ========================================================================
# STEP 2: BACKGROUND MODERATION V2 (Fire-and-forget, truly parallel)
# ========================================================================

# Fire moderation task in background (non-blocking)
if group_settings and group_settings.moderation_enabled:
    logger.debug(f"🛡️ [V2] Firing background moderation for message from user {user_id}")
    try:
        from luka_bot.handlers.moderation_background import fire_moderation_task
        
        # Fire and forget - no await, no blocking!
        fire_moderation_task(
            message_id=message.message_id,
            chat_id=message.chat.id,
            user_id=user_id,
            message_text=message_text,
            group_settings=group_settings
        )
        logger.debug(f"🔥 [V2] Moderation task fired, continuing immediately...")
    except Exception as e:
        logger.error(f"❌ Failed to fire moderation task: {e}")

# Main flow continues immediately (no blocking!)
# Note: Moderation happens in parallel, can delete messages retroactively
```

That's it! No more reputation updates, achievement checks, or bans here - all moved to background handler.

### Step 3: Track bot replies

Find where the bot sends replies to mentions (around line 700-800):

```python
if is_mentioned:
    # ... LLM response generation ...
    
    # Send response
    try:
        formatted_response = escape_html(full_response)
        bot_message = await edit_and_send_parts(bot_message, formatted_response)
        logger.info(f"✅ Bot replied to mention in group {group_id}")
    except Exception as e:
        logger.warning(f"⚠️ Failed final update: {e}")
```

**ADD** reply tracking after sending the message:

```python
if is_mentioned:
    # ... LLM response generation ...
    
    # Send response
    try:
        formatted_response = escape_html(full_response)
        bot_message = await edit_and_send_parts(bot_message, formatted_response)
        logger.info(f"✅ Bot replied to mention in group {group_id}")
        
        # ✨ NEW: Track reply for retroactive deletion
        from luka_bot.services.reply_tracker_service import get_reply_tracker_service
        reply_tracker = get_reply_tracker_service()
        await reply_tracker.track_reply(
            chat_id=message.chat.id,
            user_message_id=message.message_id,
            bot_reply_id=bot_message.message_id
        )
        logger.debug(f"📍 Tracked bot reply {bot_message.message_id} for moderation")
        
    except Exception as e:
        logger.warning(f"⚠️ Failed final update: {e}")
```

### Step 4: Add shutdown handler (optional but recommended)

In `__main__.py`, add graceful shutdown for background tasks:

```python
async def on_shutdown() -> None:
    """Bot shutdown cleanup."""
    logger.info("🛑 luka_bot shutting down...")
    
    # Cancel all background tasks (NEW)
    from luka_bot.utils.background_tasks import cancel_all_background_tasks
    await cancel_all_background_tasks()
    
    logger.info("✅ luka_bot shut down gracefully")
```

---

## 🧪 Testing

### Test 1: Response Speed (Without Moderation)
```
1. Disable moderation (toggle button)
2. Mention bot: @GuruKeeperBot hello
3. Measure response time

Expected: <1 second ✅
```

### Test 2: Response Speed (With Moderation)
```
1. Enable moderation (toggle button)
2. Mention bot: @GuruKeeperBot hello
3. Measure response time

Expected: <1 second ✅ (NOT 5+ seconds!)
```

### Test 3: Background Moderation Still Works
```
1. Enable moderation
2. Send violating message: @GuruKeeperBot [spam link]
3. Bot replies immediately
4. Within 10 seconds, both messages deleted

Expected: 
- Fast reply ✅
- Messages cleaned up retroactively ✅
```

### Test 4: Reputation Updates
```
1. Enable moderation
2. Send several good messages
3. Check /reputation

Expected: Points increase ✅
```

### Test 5: Achievements
```
1. Enable moderation
2. Send enough good messages to unlock achievement
3. Achievement announced in group

Expected: 🏆 Achievement message ✅
```

---

## 📊 Expected Results

### Before (V1)
```
User mentions bot
  ↓
⏱️ Wait 5 seconds (moderation timeout)
  ↓
🔍 Check for mention
  ↓
💬 Generate reply
  ↓
📤 Send reply

Total time: 5-7 seconds ❌
```

### After (V2)
```
User mentions bot
  ├──► 🔥 Fire moderation (parallel, no wait)
  └──► 🚀 Continue immediately
         ├──► 🔍 Check mention ✅
         ├──► 💬 Generate reply ✅
         └──► 📤 Send reply ✅

Meanwhile (in parallel):
  🛡️ Moderation evaluates
       ↓
  🚫 Delete both messages (if violation)

Total time: <1 second ✅
```

**Improvement**: 5-7x faster! 🚀

---

## ⚠️ Important Notes

### Trade-offs

**Pros**:
- ✅ **5-7x faster responses** - No blocking
- ✅ **Better user experience** - Instant replies
- ✅ **Scalable** - Can handle high message volume
- ✅ **Still catches violations** - Retroactive deletion

**Cons**:
- ⚠️ **Violations visible briefly** - Message visible for 1-10 seconds before deletion
- ⚠️ **Bot might reply to bad message** - Reply gets deleted retroactively
- ⚠️ **More complex** - Need to track replies

### When to Use

**Use V2 if**:
- You want fast bot responses
- Brief violation visibility is acceptable
- You have high message volume

**Use V1 if**:
- You want instant moderation (before bot reply)
- You can accept 5-second delays
- You have low message volume

**Recommendation**: Use V2 for production (better UX)

---

## 🔧 Troubleshooting

### Bot still slow after V2
**Check**: Is V2 actually integrated?
**Look for**: `[V2]` markers in logs
**Fix**: Verify integration steps completed

### Moderation not working
**Check**: Are background tasks running?
**Command**: Check logs for "🔥 Fired moderation task"
**Fix**: Verify `fire_moderation_task()` is called

### Messages not deleted
**Check**: Is LLM evaluating correctly?
**Look for**: "[Background]" logs
**Fix**: Check ModerationService LLM calls

### Bot replies not tracked
**Check**: Reply tracker logs
**Look for**: "📍 Tracked bot reply"
**Fix**: Verify tracking code after bot sends message

---

## 📚 Code Reference

**New files** (all complete):
- `services/reply_tracker_service.py` - Tracks bot replies in Redis
- `utils/background_tasks.py` - Manages async background tasks
- `handlers/moderation_background.py` - V2 moderation logic

**Modified files** (integration needed):
- `handlers/group_messages.py` - Replace V1 with V2 calls
- `__main__.py` - Add shutdown handler (optional)

**Lines to change**: ~100 lines removed, ~20 lines added (net -80 lines!)

---

## ✅ Verification Checklist

After integration:

- [ ] Bot responds to mentions in <1 second
- [ ] Logs show `[V2]` markers
- [ ] Logs show `🔥 Fired moderation task`
- [ ] Logs show `📍 Tracked bot reply`
- [ ] Logs show `[Background]` moderation logs
- [ ] Violating messages still get deleted (retroactively)
- [ ] Reputation updates still work
- [ ] Achievements still announced
- [ ] Auto-ban still works
- [ ] No errors in logs

---

## 🎯 Next Steps

1. **Integrate** V2 into `group_messages.py`
2. **Test** response speed
3. **Verify** background moderation works
4. **Monitor** logs for errors
5. **Celebrate** 5x performance improvement! 🎉

---

**Status**: ✅ **READY TO INTEGRATE**  
**Estimated time**: 10-15 minutes  
**Risk**: Low (easy to revert if issues)  
**Impact**: High (5-7x faster responses)

🚀 **Let's make the bot faster!**

