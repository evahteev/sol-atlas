# Group Moderation System - Implementation Plan

## 🎯 Overview

Implementation plan for a comprehensive moderation system using a **two-prompt architecture**:

1. **GroupSettings.moderation_prompt** - Background moderation (evaluates ALL messages)
2. **Thread.system_prompt** - Active engagement (bot personality when mentioned)

---

## 📊 Implementation Scope

**Total Tasks**: 37  
**Estimated Effort**: 2-3 days  
**Complexity**: Medium-High

### Breakdown by Phase:

| Phase | Tasks | Status |
|-------|-------|--------|
| **Phase 1: Models** | 3 | 🔴 Not Started |
| **Phase 2: Service Layer** | 6 | 🔴 Not Started |
| **Phase 3: Message Handler** | 6 | 🔴 Not Started |
| **Phase 4: Initialization** | 2 | 🔴 Not Started |
| **Phase 5: Commands** | 2 | 🔴 Not Started |
| **Phase 6: Admin UI** | 6 | 🔴 Not Started |
| **Phase 7: Utilities** | 2 | 🔴 Not Started |
| **Phase 8: i18n** | 2 | 🔴 Not Started |
| **Phase 9: Documentation** | 3 | 🔴 Not Started |
| **Phase 10: Testing** | 5 | 🔴 Not Started |

---

## 📁 Files to Create/Modify

### New Files (8)
```
luka_bot/models/group_settings.py          ✨ NEW
luka_bot/models/user_reputation.py         ✨ NEW
luka_bot/services/moderation_service.py    ✨ NEW
luka_bot/handlers/moderation_commands.py   ✨ NEW
luka_bot/keyboards/moderation_inline.py    ✨ NEW
luka_bot/utils/content_detection.py        ✨ NEW
luka_bot/utils/moderation_templates.py     ✨ NEW
luka_bot/MODERATION_SYSTEM.md              ✨ NEW (docs)
```

### Modified Files (6)
```
luka_bot/handlers/group_messages.py        📝 UPDATE (add moderation flow)
luka_bot/handlers/group_commands.py        📝 UPDATE (add /moderation, update /reset)
luka_bot/handlers/__init__.py              📝 UPDATE (register new handlers)
luka_bot/locales/en/LC_MESSAGES/messages.po  📝 UPDATE (add i18n strings)
luka_bot/locales/ru/LC_MESSAGES/messages.po  📝 UPDATE (add i18n strings)
luka_bot/THREAD_ARCHITECTURE.md            📝 UPDATE (document new models)
```

---

## 🏗️ Phase Details

### Phase 1: Models (3 tasks) 🔴
**Goal**: Create data structures for moderation

**Tasks**:
1. ✅ Create `GroupSettings` model
   - Pre-processing filters (stoplist, regex, service messages)
   - `moderation_prompt` field (⭐ key field)
   - Thresholds and rules
   - Reputation system settings

2. ✅ Create `UserReputation` model
   - Points, violations, achievements
   - Ban status and duration
   - Activity tracking

3. ✅ Add serialization methods
   - `to_dict()` and `from_dict()` for Redis

**Deliverables**:
- `luka_bot/models/group_settings.py`
- `luka_bot/models/user_reputation.py`

---

### Phase 2: Service Layer (6 tasks) 🔴
**Goal**: Business logic for moderation

**Tasks**:
1. ✅ Create `ModerationService` class
2. ✅ GroupSettings CRUD methods
3. ✅ `evaluate_message_moderation()` - LLM evaluation with moderation_prompt
4. ✅ UserReputation CRUD methods
5. ✅ `update_user_reputation()` - Points/violations logic
6. ✅ Ban/achievement methods

**Deliverables**:
- `luka_bot/services/moderation_service.py`

**Key Method**:
```python
async def evaluate_message_moderation(
    message: str,
    prompt: str,  # GroupSettings.moderation_prompt
    group_id: int
) -> dict:
    # Returns: {helpful, violation, quality_score, action, reason}
```

---

### Phase 3: Message Handler (6 tasks) 🔴
**Goal**: Integrate moderation into message processing

**Message Flow**:
```
Message → Pre-processing → Background Moderation → Reputation Update → Engagement
```

**Tasks**:
1. ✅ Add pre-processing filters (stoplist, regex, service messages)
2. ✅ Add background moderation (ALL messages use moderation_prompt)
3. ✅ Add reputation updates after moderation
4. ✅ Ensure mention handler uses Thread.system_prompt (NOT moderation_prompt)
5. ✅ Add violation notifications
6. ✅ Add achievement notifications

**Modified File**:
- `luka_bot/handlers/group_messages.py`

---

### Phase 4: Initialization (2 tasks) 🔴
**Goal**: Create default settings when bot joins

**Tasks**:
1. ✅ Update `handle_bot_added_to_group`: Create default GroupSettings
2. ✅ Update auto-initialization: Create GroupSettings if missing

**Default Settings**:
- Moderation enabled: true
- Default moderation_prompt: General-purpose template
- Reputation enabled: true
- Auto-ban: false (admin must enable)

---

### Phase 5: Commands (2 tasks) 🔴
**Goal**: Admin commands for moderation

**Tasks**:
1. ✅ Add `/moderation` command - View current settings
2. ✅ Update `/reset` command - Delete GroupSettings + UserReputation

**Commands**:
```
/moderation - Show moderation status and stats
/reset - Delete all group data (including moderation)
```

---

### Phase 6: Admin UI (6 tasks) 🔴
**Goal**: Inline keyboards for configuration

**Tasks**:
1. ✅ Create moderation settings keyboard
2. ✅ Create moderation_prompt editor (text input)
3. ✅ Create stoplist editor (add/remove words)
4. ✅ Create pattern filter editor (regex)
5. ✅ Create user reputation viewer
6. ✅ Create leaderboard UI

**UI Structure**:
```
⚙️ Group Settings
  ├─ 🛡️ Moderation
  │   ├─ Edit Moderation Prompt
  │   ├─ Configure Filters
  │   ├─ Set Thresholds
  │   └─ View Reputation Stats
  └─ ... (existing settings)
```

---

### Phase 7: Utilities (2 tasks) 🔴
**Goal**: Helper functions and templates

**Tasks**:
1. ✅ Create content detection utilities
   - `contains_links(text)`
   - `extract_patterns(text, patterns)`
   - `check_stoplist(text, words)`

2. ✅ Create moderation prompt templates
   - General purpose
   - Crypto/trading groups
   - Tech/programming groups
   - Educational groups

**File**:
- `luka_bot/utils/content_detection.py`
- `luka_bot/utils/moderation_templates.py`

---

### Phase 8: i18n (2 tasks) 🔴
**Goal**: Multilingual support

**Tasks**:
1. ✅ Add moderation message strings (EN/RU)
   - Violation notices
   - Warning messages
   - Achievement notifications
   - Ban/unban messages

2. ✅ Add UI label strings (EN/RU)
   - Button labels
   - Setting descriptions
   - Help text

**Strings Needed**: ~50 new translation strings

---

### Phase 9: Documentation (3 tasks) 🔴
**Goal**: Comprehensive documentation

**Tasks**:
1. ✅ Create `MODERATION_SYSTEM.md` - Architecture overview
2. ✅ Update `THREAD_ARCHITECTURE.md` - Add new models
3. ✅ Create `MODERATION_PROMPT_GUIDE.md` - Prompt examples

**Documentation Topics**:
- Two-prompt architecture
- GroupSettings fields explained
- UserReputation system
- Prompt engineering tips
- Examples for different group types

---

### Phase 10: Testing (5 tasks) 🔴
**Goal**: Validate all functionality

**Test Scenarios**:
1. ✅ Pre-processing filters work correctly
2. ✅ Background moderation evaluates messages
3. ✅ Reputation updates trigger correctly
4. ✅ Achievements awarded at right thresholds
5. ✅ Two prompts stay separated (moderation vs conversation)

**Manual Testing Checklist**:
- [ ] Send message with stoplist word → deleted
- [ ] Send spam → violation recorded, points deducted
- [ ] Send helpful message → points added
- [ ] Mention bot → uses Thread.system_prompt
- [ ] Reach violation threshold → auto-ban works
- [ ] Reach achievement threshold → notification sent

---

## 🎯 Implementation Order (Recommended)

### Week 1: Core Foundation
1. **Day 1**: Phase 1 (Models) + Phase 2 (Service Layer)
2. **Day 2**: Phase 3 (Message Handler) + Phase 4 (Initialization)
3. **Day 3**: Phase 5 (Commands) + Phase 7 (Utilities)

### Week 2: UI & Polish
4. **Day 4**: Phase 6 (Admin UI) - Keyboards and handlers
5. **Day 5**: Phase 8 (i18n) + Phase 9 (Documentation)
6. **Day 6**: Phase 10 (Testing) + Bug fixes

---

## 🔑 Key Design Decisions

### 1. Two-Prompt Architecture ⭐
- **Background**: `GroupSettings.moderation_prompt` (evaluates ALL messages)
- **Foreground**: `Thread.system_prompt` (bot personality when engaged)

### 2. Separation of Concerns
- **GroupSettings** = Rules, filters, moderation
- **Thread** = Conversation, LLM personality
- **UserReputation** = Per-user tracking

### 3. Redis Storage
```
group_settings:{group_id}                  # GroupSettings
group_settings:{group_id}:topic_{topic_id} # Topic-specific
user_reputation:{user_id}:{group_id}       # Per-user
group_leaderboard:{group_id}               # Sorted set by points
```

### 4. Async Processing
- Pre-processing: Synchronous (fast filters)
- Background moderation: Async (non-blocking)
- Reputation updates: Async (background task)

---

## 📊 Success Metrics

After implementation, you should be able to:

✅ **Moderation**:
- Set custom moderation rules per group
- Auto-delete spam/toxic content
- Silent background evaluation of all messages

✅ **Reputation**:
- Track user contributions
- Award achievements automatically
- Enforce violation thresholds

✅ **Two-Prompt System**:
- Background moderation (passive)
- Conversational engagement (active)
- No confusion between the two

✅ **Admin Control**:
- Easy configuration via inline keyboards
- View reputation stats
- Manage stoplist and filters

---

## 🚨 Migration Notes

### Redis Changes Required
```bash
# No migration needed - new data structures
# Old Thread/GroupLink data unaffected
# Just add new keys:
# - group_settings:*
# - user_reputation:*
```

### Breaking Changes
**None!** This is purely additive:
- New models don't affect existing ones
- Thread/GroupLink unchanged
- Opt-in feature (can be disabled per group)

---

## 🎨 Example: Crypto Trading Group

### GroupSettings Configuration:
```python
group_settings = GroupSettings(
    group_id=-1001234567890,
    
    # Filters
    stoplist_words=["pump", "scam", "URGENT!!!"],
    delete_links=True,
    pattern_filters=[
        {"pattern": r"bit\.ly/.*", "action": "delete"}
    ],
    
    # Moderation
    moderation_prompt="""You moderate a crypto trading group.
    
    HELPFUL: Market analysis, technical questions, trading strategies
    SPAM: Pump schemes, referral links, repeated promotions
    TOXIC: FUD, personal attacks, harassment
    
    Return JSON: {helpful, violation, quality_score, action, reason}""",
    
    # Reputation
    points_per_helpful_message=5,
    violation_penalty=-15,
    violations_before_ban=3
)
```

### Thread Configuration:
```python
thread = Thread(
    thread_id="group_-1001234567890",
    thread_type="group",
    language="en",
    
    # Conversational personality (used when @mentioned)
    system_prompt="""You are CryptoGuru, a friendly crypto expert.
    
    Help users with:
    - Technical analysis
    - Market trends
    - Trading strategies
    - Wallet security
    
    Be friendly, accurate, and educational."""
)
```

---

## 📚 Related Documentation

After implementation:
- [MODERATION_SYSTEM.md](./MODERATION_SYSTEM.md) - System architecture
- [MODERATION_PROMPT_GUIDE.md](./MODERATION_PROMPT_GUIDE.md) - Prompt examples
- [THREAD_ARCHITECTURE.md](./THREAD_ARCHITECTURE.md) - Overall architecture

---

## ✅ Checklist

Before starting implementation, ensure:
- [ ] Redis is running and accessible
- [ ] LLM service is configured
- [ ] Bot has admin permissions in test groups
- [ ] i18n system is working
- [ ] You understand two-prompt architecture

---

**Created**: October 11, 2025  
**Status**: Ready for Implementation  
**Estimated Time**: 5-6 days

Ready to start? Begin with **Phase 1: Models**! 🚀

