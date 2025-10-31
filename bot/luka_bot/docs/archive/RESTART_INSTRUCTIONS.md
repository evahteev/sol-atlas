# 🔄 How to Restart the Bot

## Quick Restart

```bash
# 1. Stop current bot (if running)
# Press Ctrl+C in the terminal where bot is running

# 2. Start bot again
/Users/evgenyvakhteev/Documents/src/dexguru/bot/venv/bin/python \
/Users/evgenyvakhteev/Documents/src/dexguru/bot/luka_bot/__main__.py
```

---

## What to Look For After Restart

### ✅ Successful Startup
You should see:
```
INFO     | __main__:main:120 - 📡 Using polling mode
INFO     | __main__:on_startup:30 - 🚀 luka_bot starting...
INFO     | __main__:on_startup:35 - 🌍 I18n middleware registered
INFO     | luka_bot.handlers:get_llm_bot_router:64 - 📦 Phase 4 handlers registered
INFO     | __main__:on_startup:49 - 📋 Default commands configured
INFO     | __main__:on_startup:53 - ✅ Bot: GURU Keeper (@GuruKeeperBot, ID: ...)
INFO     | __main__:on_startup:55 - ✅ luka_bot started successfully
```

### ✅ Fixed Issues
After restart, these errors should be GONE:
- ❌ ~~`'LLMService' object has no attribute 'agent'`~~ → FIXED
- ❌ ~~`'thread_id'` missing from GroupLink~~ → FIXED (auto-migrates)
- ❌ ~~Moderation blocking mentions~~ → FIXED (disabled by default + timeout)

### ✅ New Features Working
After restart, you should see:
- 🔍 `Checking for mentions of @BotUsername` - Enhanced logging
- ✅ `Bot mention detected via entity` - Mention detection working
- 🛡️ `Background moderation for message from user X` - Only if moderation enabled
- ⏱️ `Background moderation timed out` - Timeout protection working

---

## Test After Restart

### 1. Test Mention Detection
In a group where bot is present:
```
@GuruKeeperBot hello
```

**Expected logs**:
```
🔍 Checking for mentions of @GuruKeeperBot
✅ Bot mention detected via entity: @GuruKeeperBot
🔔 Bot mentioned in group -XXXXXXXXX by user XXXXXX
```

### 2. Test /groups Command
In DM with bot:
```
/groups
```

**Expected**: List of groups with KB and agent info

### 3. Test /moderation Command
In group (as admin):
```
/moderation
```

**Expected**: Settings view showing **moderation DISABLED** by default

---

## If Something's Wrong

### Bot Not Starting
**Check**:
- Is port already in use? (Kill old process)
- Are dependencies installed? (`pip install -r requirements.txt`)
- Is Redis running? (`redis-cli ping` should return `PONG`)
- Is Elasticsearch running? (`curl http://localhost:9200`)

### Bot Starting But Not Responding
**Check logs for errors**:
- Look for any `ERROR` or `CRITICAL` entries
- Check if handlers registered: `📦 Phase 4 handlers registered`
- Check if commands configured: `📋 Default commands configured`

### Moderation Still Causing Issues
**Disable via Redis**:
```bash
redis-cli
> SCAN 0 MATCH group_settings:*
> HSET group_settings:GROUP_ID moderation_enabled false
```

---

## Background Process (Optional)

If you want to run bot in background:

```bash
# Using nohup
nohup /Users/evgenyvakhteev/Documents/src/dexguru/bot/venv/bin/python \
/Users/evgenyvakhteev/Documents/src/dexguru/bot/luka_bot/__main__.py \
> bot.log 2>&1 &

# Check logs
tail -f bot.log

# Find process
ps aux | grep luka_bot

# Stop process
kill <PID>
```

Or use a process manager like `systemd`, `supervisor`, or `pm2`.

---

## Changes Applied in Latest Version

1. ✅ **Moderation disabled by default** - Safe opt-in approach
2. ✅ **5-second timeout on moderation** - Prevents blocking
3. ✅ **Enhanced mention logging** - Better debugging
4. ✅ **Legacy GroupLink migration** - Auto-fixes old data
5. ✅ **Direct LLM agent for moderation** - Fixes 'agent' error

---

**Ready?** Stop the bot (Ctrl+C) and restart using the command above! 🚀

