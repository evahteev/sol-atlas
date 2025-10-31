# Moderation Architecture V2 - True Background Processing

**Status**: 🔥 **CRITICAL IMPROVEMENT NEEDED**  
**Issue**: Current moderation blocks main flow for 5 seconds (timeout)  
**Goal**: Truly parallel background moderation with retroactive action

---

## 🚨 Current Problem

### What's Happening Now
```python
# Current flow (BLOCKING):
1. User sends message
2. ⏱️ Wait up to 5 seconds for moderation (with timeout)
3. 🔍 Check for mentions
4. 💬 Generate bot reply

Problem: Steps 2-4 are sequential, moderation delays everything
```

### Observed Behavior
```
19:00:15.540 | 🛡️ Background moderation for message from user 922705
19:00:20.552 | ⏱️ Background moderation timed out (5 seconds later!)
19:00:20.938 | 🔍 Checking for mentions (finally!)
```

**Impact**: 5-second delay before bot responds to mentions

---

## ✅ Proposed Solution: Fire-and-Forget with Retroactive Action

### Architecture Overview

```
User Message
     │
     ├──► 🔥 FIRE moderation task (asyncio.create_task)
     │         └──► Runs in parallel, no blocking
     │
     └──► 🚀 CONTINUE immediately
              ├──► Check mentions
              ├──► Generate bot reply
              └──► Index message
              
Meanwhile (in parallel):
🛡️ Moderation completes →
    ├──► If violation detected:
    │     ├──► Delete user message
    │     └──► Delete bot reply (if exists)
    └──► Update reputation
```

### Key Improvements

1. **Zero Blocking**: Bot responds immediately, moderation happens in parallel
2. **Retroactive Deletion**: Can delete bot's reply after the fact
3. **Better UX**: Fast responses, violations cleaned up later
4. **Scalable**: Can handle high message volume

---

## 🛠️ Implementation Plan

### Step 1: Fire-and-Forget Moderation

```python
# In handle_group_message():

# OLD (blocking):
moderation_result = await asyncio.wait_for(
    moderation_service.evaluate_message_moderation(...),
    timeout=5.0
)

# NEW (non-blocking):
if group_settings and group_settings.moderation_enabled:
    # Fire moderation task in background
    asyncio.create_task(
        process_moderation_in_background(
            message_id=message.message_id,
            chat_id=message.chat.id,
            user_id=user_id,
            message_text=message_text,
            group_settings=group_settings
        )
    )
    # Continue immediately, don't wait!

# Bot continues processing immediately...
```

### Step 2: Background Moderation Handler

```python
async def process_moderation_in_background(
    message_id: int,
    chat_id: int,
    user_id: int,
    message_text: str,
    group_settings: GroupSettings
):
    """
    Process moderation in true background.
    Takes as long as needed, doesn't block main flow.
    """
    try:
        from luka_bot.services.moderation_service import get_moderation_service
        from luka_bot.core.loader import bot
        
        moderation_service = await get_moderation_service()
        
        # Evaluate (no timeout, take as long as needed)
        result = await moderation_service.evaluate_message_moderation(
            message_text=message_text,
            group_settings=group_settings,
            user_id=user_id,
            group_id=chat_id
        )
        
        # Update reputation
        reputation = await moderation_service.update_user_reputation(
            user_id=user_id,
            group_id=chat_id,
            moderation_result=result,
            group_settings=group_settings
        )
        
        # Take action if needed
        action = result.get("action", "none")
        violation = result.get("violation")
        
        if action in ["delete", "warn"] and violation:
            # Get bot's reply to this message (if exists)
            bot_reply_id = await get_bot_reply_to_message(chat_id, message_id)
            
            if action == "delete":
                # Delete user's original message
                try:
                    await bot.delete_message(chat_id, message_id)
                    logger.warning(f"🚫 Deleted message {message_id} from user {user_id}: {violation}")
                except:
                    pass
                
                # Delete bot's reply (if exists)
                if bot_reply_id:
                    try:
                        await bot.delete_message(chat_id, bot_reply_id)
                        logger.info(f"🗑️ Also deleted bot reply {bot_reply_id}")
                    except:
                        pass
                
                # Notify user
                try:
                    await bot.send_message(
                        user_id,
                        f"⚠️ Your message was removed from the group.\n"
                        f"Reason: {result.get('reason', 'Violation detected')}\n"
                        f"Type: {violation}"
                    )
                except:
                    pass
            
            elif action == "warn":
                # Send warning (don't delete)
                try:
                    await bot.send_message(
                        user_id,
                        f"⚠️ Warning: Your message may violate group rules.\n"
                        f"Reason: {result.get('reason', 'Please review')}\n"
                        f"Type: {violation}"
                    )
                except:
                    pass
        
        # Check for ban
        if reputation.is_banned or (
            group_settings.auto_ban_enabled and 
            reputation.violations >= group_settings.ban_threshold
        ):
            # Ban user
            await moderation_service.ban_user(
                user_id=user_id,
                group_id=chat_id,
                reason="Exceeded violation threshold",
                duration_hours=group_settings.ban_duration_hours
            )
            
            try:
                from datetime import datetime, timedelta
                ban_until = datetime.utcnow() + timedelta(hours=group_settings.ban_duration_hours)
                await bot.ban_chat_member(chat_id, user_id, until_date=ban_until)
                logger.warning(f"🚫 Banned user {user_id} from group {chat_id}")
            except:
                pass
        
        # Check achievements
        new_achievements = await moderation_service.check_achievements(reputation)
        if new_achievements:
            # Announce achievement
            for achievement in new_achievements[:1]:  # Just announce the first
                try:
                    await bot.send_message(
                        chat_id,
                        f"🏆 <b>Achievement Unlocked!</b>\n\n"
                        f"{achievement['icon']} {achievement['name']}\n"
                        f"+{achievement['points']} points",
                        parse_mode="HTML"
                    )
                except:
                    pass
        
    except Exception as e:
        logger.error(f"❌ Background moderation error: {e}", exc_info=True)
```

### Step 3: Track Bot Replies for Retroactive Deletion

```python
# In message_state_service or new reply_tracker_service:

class ReplyTrackerService:
    """Track bot replies to user messages for retroactive moderation."""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def track_reply(
        self,
        chat_id: int,
        user_message_id: int,
        bot_reply_id: int,
        ttl: int = 300  # 5 minutes
    ):
        """Track that bot replied to a message."""
        key = f"bot_reply:{chat_id}:{user_message_id}"
        await self.redis.setex(key, ttl, str(bot_reply_id))
    
    async def get_bot_reply(
        self,
        chat_id: int,
        user_message_id: int
    ) -> Optional[int]:
        """Get bot's reply message ID (if exists)."""
        key = f"bot_reply:{chat_id}:{user_message_id}"
        result = await self.redis.get(key)
        return int(result) if result else None

# Usage in mention handler:
if is_mentioned:
    # ... generate bot reply ...
    bot_message = await message.reply(full_response)
    
    # Track this reply for retroactive moderation
    reply_tracker = get_reply_tracker_service()
    await reply_tracker.track_reply(
        chat_id=message.chat.id,
        user_message_id=message.message_id,
        bot_reply_id=bot_message.message_id
    )
```

---

## 📊 Performance Analysis

### Current (Blocking with Timeout)
```
User message → [Wait 5s for moderation] → Check mentions → Reply
Total time to reply: 5+ seconds
```

### Proposed (True Background)
```
User message → [Fire moderation task] → Check mentions → Reply
                      ↓ (parallel)
                 Moderation completes in background
Total time to reply: <1 second
```

**Improvement**: ~5x faster response time

---

## ⚠️ Trade-offs & Considerations

### Pros
✅ **Fast responses** - Bot replies immediately  
✅ **Better UX** - No perceived lag  
✅ **Scalable** - Can handle high message volume  
✅ **Retroactive cleanup** - Violations cleaned up after fact  

### Cons
⚠️ **Temporary violations** - Bad message visible for 1-5 seconds  
⚠️ **Complexity** - Need to track replies  
⚠️ **Race conditions** - Bot might reply to message that gets deleted  

### Mitigations
1. **Fast LLM**: Optimize moderation prompt for speed
2. **Pre-filtering**: Use stoplist/regex first (instant) before LLM
3. **Grace period**: Only retroactive-delete if moderation completes within 10s
4. **User feedback**: Show "Message deleted due to violation" after bot reply removed

---

## 🔧 Implementation Steps

### Phase 1: Fix Timeout (Immediate)
- [x] Add 5-second timeout (done)
- [ ] Investigate why LLM calls take >5 seconds
- [ ] Optimize moderation prompt for faster responses
- [ ] Consider smaller/faster model for moderation

### Phase 2: True Background (High Priority)
- [ ] Implement `process_moderation_in_background()`
- [ ] Replace `await` with `asyncio.create_task()`
- [ ] Test that bot replies immediately
- [ ] Verify moderation still happens in background

### Phase 3: Retroactive Deletion (Medium Priority)
- [ ] Create `ReplyTrackerService`
- [ ] Track all bot replies in mention handler
- [ ] Implement retroactive deletion logic
- [ ] Test deletion of both messages

### Phase 4: Optimization (Future)
- [ ] Batch multiple messages for single LLM call
- [ ] Use smaller model for simple cases
- [ ] Cache frequent patterns
- [ ] Pre-compute user reputation scores

---

## 🧪 Testing Plan

### Test 1: Response Speed
```
1. Send message mentioning bot
2. Measure time to bot reply
Expected: <1 second (not 5+ seconds)
```

### Test 2: Background Moderation
```
1. Enable moderation
2. Send violating message with mention
3. Bot should reply immediately
4. Within 10 seconds, both messages deleted
Expected: Fast reply, then cleanup
```

### Test 3: Race Conditions
```
1. Send violating message
2. Bot replies
3. Moderation completes
4. Both messages deleted
Expected: No orphaned replies
```

---

## 📝 Code Locations

**Files to modify**:
- `handlers/group_messages.py` - Main message handler
- `services/moderation_service.py` - Add background processing method
- `services/reply_tracker_service.py` - NEW: Track bot replies
- `utils/background_tasks.py` - NEW: Background task utilities

**Key changes**:
1. Replace `await moderation` with `create_task`
2. Add reply tracking after bot responds
3. Implement retroactive deletion logic

---

## 🎯 Success Criteria

✅ **Bot replies within 1 second** (not 5+ seconds)  
✅ **Moderation still evaluates all messages** (in background)  
✅ **Violations cleaned up retroactively** (delete both messages)  
✅ **No impact on non-violating messages** (normal flow)  
✅ **Reputation updates work correctly** (async safe)  

---

## 🚀 Next Steps

1. **Immediate**: Investigate why LLM calls take >5 seconds
   - Check LLM service health
   - Review moderation prompt length
   - Test with simpler prompt
   - Consider timeout at LLM level

2. **Short-term**: Implement true background processing
   - Refactor to use `asyncio.create_task()`
   - Test response time improvements
   - Verify moderation still works

3. **Medium-term**: Add retroactive deletion
   - Implement reply tracking
   - Add deletion logic
   - Test edge cases

---

**Priority**: 🔥 **CRITICAL** - Blocking bot responses is bad UX  
**Estimated effort**: 4-6 hours  
**Impact**: ~5x faster response times  

---

*Version: 2.0 (Proposed)*  
*Date: 2025-10-11*  
*Status: Architecture defined, implementation pending*

