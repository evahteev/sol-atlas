# Moderation System Documentation

## Overview

The Luka Bot moderation system implements a sophisticated **two-prompt architecture** that separates background content moderation from active conversational engagement.

**Key Innovation**: Instead of using a single LLM prompt for all interactions, we use:
1. **`GroupSettings.moderation_prompt`** - Background evaluation of ALL messages (passive)
2. **`Thread.system_prompt`** - Active conversation when bot is directly engaged (active)

This separation ensures:
- ✅ All messages are evaluated for quality/violations (even when bot isn't mentioned)
- ✅ Bot remains conversational and helpful when directly engaged
- ✅ Admins can customize moderation rules independent of bot personality

---

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                     GROUP MESSAGE FLOW                       │
└─────────────────────────────────────────────────────────────┘

Message Received
    ↓
┌───────────────────────────────────────┐
│ 1. PRE-PROCESSING (Fast, Rule-Based) │
│    • Stoplist check                   │
│    • Pattern matching (regex)         │
│    • Content type filters             │
│    • Service message deletion         │
│    Result: Instant delete or continue │
└───────────────────────────────────────┘
    ↓
┌───────────────────────────────────────┐
│ 2. BACKGROUND MODERATION (LLM-Based) │
│    Uses: GroupSettings.moderation_    │
│          prompt                        │
│    Evaluates:                          │
│    • Is this helpful?                  │
│    • Is this spam/toxic?               │
│    • Quality score (0-10)              │
│    • Action: none/warn/delete          │
└───────────────────────────────────────┘
    ↓
┌───────────────────────────────────────┐
│ 3. REPUTATION UPDATE                  │
│    • Award/deduct points               │
│    • Track violations                  │
│    • Check for achievements            │
│    • Auto-ban if threshold reached     │
└───────────────────────────────────────┘
    ↓
┌───────────────────────────────────────┐
│ 4. INDEX TO KNOWLEDGE BASE            │
│    (Only if not deleted)               │
└───────────────────────────────────────┘
    ↓
┌───────────────────────────────────────┐
│ 5. CONVERSATIONAL ENGAGEMENT          │
│    (Only when bot is @mentioned)       │
│    Uses: Thread.system_prompt          │
│    Result: Helpful response            │
└───────────────────────────────────────┘
```

---

## Models

### 1. GroupSettings

Stores per-group moderation configuration.

**Redis Key**: `group_settings:{group_id}` or `group_settings:{group_id}:topic_{topic_id}`

**Fields**:
```python
# Pre-processing filters
delete_service_messages: bool
service_message_types: list[str]
stoplist_enabled: bool
stoplist_words: list[str]
stoplist_case_sensitive: bool
delete_links: bool
delete_images: bool
delete_videos: bool
delete_stickers: bool
delete_forwarded: bool
pattern_filters: list[dict]  # Regex patterns

# Background moderation
moderation_enabled: bool
moderation_prompt: str  # ⭐ KEY FIELD
auto_delete_threshold: float  # 8.0 = auto-delete if score >= 8
auto_warn_threshold: float    # 5.0 = warn if score >= 5
quality_threshold: float      # 7.0 = award points if score >= 7

# Reputation system
reputation_enabled: bool
points_per_helpful_message: int
points_per_quality_reply: int
violations_before_ban: int
ban_duration_hours: int
achievements_enabled: bool
achievement_rules: list[dict]

# Notifications
notify_violations: bool
notify_achievements: bool
public_warnings: bool
public_achievements: bool
```

### 2. UserReputation

Tracks per-user reputation in a group.

**Redis Keys**: 
- `user_reputation:{user_id}:{group_id}` - Individual reputation
- `group_leaderboard:{group_id}` - Sorted set of user points
- `group_users_reputation:{group_id}` - Set of user IDs

**Fields**:
```python
# Score
points: int
message_count: int
helpful_messages: int
quality_replies: int

# Violations
warnings: int
violations: int
violation_history: list[dict]
last_violation_at: datetime

# Ban status
is_banned: bool
ban_reason: str
ban_until: datetime  # None = permanent

# Achievements
achievements: list[str]
achievement_history: list[dict]

# Activity
first_message_at: datetime
last_message_at: datetime
replies_count: int
mentions_count: int
```

---

## Service Layer

### ModerationService

**Location**: `luka_bot/services/moderation_service.py`

**Key Methods**:

#### GroupSettings Management
```python
async def get_group_settings(group_id, topic_id=None) -> GroupSettings
async def save_group_settings(settings: GroupSettings) -> bool
async def create_default_group_settings(group_id, created_by) -> GroupSettings
async def delete_group_settings(group_id, topic_id=None) -> bool
```

#### Background Moderation ⭐
```python
async def evaluate_message_moderation(
    message_text: str,
    group_settings: GroupSettings,
    user_id: int,
    group_id: int
) -> dict:
    """
    Evaluates message using moderation_prompt.
    
    Returns:
    {
        "helpful": true/false,
        "violation": null or "spam"|"toxic"|"off-topic",
        "quality_score": 0-10,
        "action": "none"|"warn"|"delete",
        "reason": "Brief explanation"
    }
    """
```

#### UserReputation Management
```python
async def get_user_reputation(user_id, group_id) -> UserReputation
async def save_user_reputation(reputation: UserReputation) -> bool
async def update_user_reputation(
    user_id, group_id, moderation_result, 
    group_settings, is_reply, is_mention
) -> UserReputation
async def delete_all_group_reputations(group_id) -> int
```

#### Achievements & Bans
```python
async def check_achievements(user_id, group_id, group_settings) -> list[dict]
async def ban_user(user_id, group_id, reason, duration_hours, banned_by) -> bool
async def unban_user(user_id, group_id) -> bool
```

---

## Usage Guide

### For Group Admins

#### Setting Up Moderation

1. **Add bot to group** - Bot creates default GroupSettings automatically
2. **Use `/moderation` command** (coming soon) - View current settings
3. **Customize via admin UI** (coming soon) - Edit settings inline

#### Default Configuration

When bot joins a group, default settings are:
```python
moderation_enabled = True
moderation_prompt = "General-purpose prompt" (fair, balanced)
reputation_enabled = True
auto_ban_enabled = False  # Admins must enable manually

# All filters disabled by default
delete_links = False
stoplist_enabled = False
# etc.
```

#### Moderation Prompt Templates

**Available templates** (see `luka_bot/utils/moderation_templates.py`):
- `general` - Balanced, fair for any group
- `crypto` - Crypto/trading groups (strict on pump schemes)
- `tech` - Tech/programming groups (welcoming to beginners)
- `educational` - Learning groups (encourages questions)
- `community` - Social groups (lenient, friendly)
- `business` - Professional groups (maintains tone)

**Accessing templates**:
```python
from luka_bot.utils.moderation_templates import get_template

prompt = get_template("crypto")  # Use crypto template
```

#### Stoplist Management

**Use case**: Block specific words/phrases
**Examples**:
- Competitor brand names
- Prohibited topics
- Spam keywords

**Configuration**:
```python
group_settings.stoplist_enabled = True
group_settings.stoplist_words = ["viagra", "casino", "pump now"]
group_settings.stoplist_case_sensitive = False
```

#### Pattern Filters (Regex)

**Use case**: Block patterns like specific link domains, phone numbers, etc.

**Examples**:
```python
pattern_filters = [
    {
        "pattern": r"http://bit\.ly/.*",
        "action": "delete",
        "description": "Bit.ly links forbidden"
    },
    {
        "pattern": r"\d{3}-\d{3}-\d{4}",
        "action": "warn",
        "description": "Phone numbers not allowed"
    }
]
```

#### Content Type Filters

**Use case**: Restrict media types in group

**Configuration**:
```python
group_settings.delete_links = True      # No links allowed
group_settings.delete_images = False    # Images OK
group_settings.delete_videos = True     # No videos
group_settings.delete_stickers = True   # No stickers
group_settings.delete_forwarded = False # Forwards OK
```

#### Service Message Cleanup

**Use case**: Keep group clean (hide "X joined" messages)

**Configuration**:
```python
group_settings.delete_service_messages = True
group_settings.service_message_types = [
    "new_chat_members",
    "left_chat_member",
    "pinned_message"
]
```

#### Reputation System

**How it works**:
- Users gain points for helpful/quality messages
- Users lose points for violations
- Achievements awarded at milestones
- Auto-ban after N violations (if enabled)

**Point Configuration**:
```python
points_per_helpful_message = 5    # Helpful content
points_per_quality_reply = 10     # High-quality replies
violation_penalty = -10           # Minor violation
spam_penalty = -25                # Spam
toxic_penalty = -50               # Toxic behavior
```

**Auto-ban Configuration**:
```python
auto_ban_enabled = True           # Enable auto-ban
violations_before_ban = 3         # Ban after 3 violations
ban_duration_hours = 24           # 24-hour ban (0 = permanent)
```

#### Achievements

**Use case**: Gamify positive contributions

**Example achievement rules**:
```python
achievement_rules = [
    {
        "id": "helper_10",
        "name": "Helpful Contributor",
        "condition": "helpful_messages >= 10",
        "description": "Helped the community 10 times",
        "points": 50,
        "icon": "🌟"
    },
    {
        "id": "quality_50",
        "name": "Quality Expert",
        "condition": "quality_replies >= 50",
        "description": "Posted 50 high-quality replies",
        "points": 100,
        "icon": "💎"
    }
]
```

---

### For Developers

#### Adding New Moderation Rules

1. **Update `GroupSettings` model** if needed:
   ```python
   # In luka_bot/models/group_settings.py
   new_filter: bool = False
   new_filter_config: list[str] = field(default_factory=list)
   ```

2. **Update `to_dict()` and `from_dict()` methods**

3. **Implement filter in `handle_group_message`**:
   ```python
   # In luka_bot/handlers/group_messages.py
   if group_settings.new_filter:
       # Apply filter logic
       if should_delete:
           await message.delete()
           return
   ```

#### Customizing Moderation Prompt

**For specific group**:
```python
moderation_service = await get_moderation_service()
settings = await moderation_service.get_group_settings(group_id)

settings.moderation_prompt = """Custom prompt here...
Evaluate messages for:
- Custom rule 1
- Custom rule 2

Return JSON: {"helpful": ..., "violation": ..., "action": ...}
"""

await moderation_service.save_group_settings(settings)
```

**Creating a new template**:
```python
# In luka_bot/utils/moderation_templates.py
def get_gaming_moderation_prompt() -> str:
    return """You moderate a gaming community...
    
    HELPFUL content:
    - Game tips and strategies
    - Team coordination
    
    VIOLATIONS:
    - Cheating/hacking discussion
    - Toxic behavior, trash talk
    ...
    """

MODERATION_TEMPLATES["gaming"] = get_gaming_moderation_prompt
```

#### Testing Moderation

See `MODERATION_INTEGRATION_GUIDE.md` for testing checklist.

**Manual testing**:
1. Send message with stoplist word → Should delete instantly
2. Send spam message → LLM should detect, delete/warn
3. Send helpful message → Should award points
4. Check user reputation: `user_reputation:{user_id}:{group_id}` in Redis
5. Reach violation threshold → Should auto-ban

---

## Commands

### Group Commands

#### `/reset` (Admin only)
Resets ALL bot data for the group:
- ✅ Deletes all GroupLinks
- ✅ Deletes Thread configuration
- ✅ Deletes GroupSettings (moderation config)
- ✅ Deletes all UserReputation data
- ✅ Deletes Elasticsearch KB index

**Usage**: `/reset` → Confirm with button → Complete wipe

#### `/moderation` (Coming soon, Admin only)
View current moderation settings for the group.

---

## Best Practices

### For Moderation Prompts

1. **Be specific about your community's values**
   ```
   BAD:  "Moderate this group"
   GOOD: "This is a beginner-friendly Python learning group. 
          Welcome all questions, encourage learning."
   ```

2. **Define clear violation categories**
   ```
   - SPAM: Promotional content, repeated ads
   - TOXIC: Personal attacks, harassment
   - OFF-TOPIC: Non-Python discussions (some flexibility OK)
   ```

3. **Set appropriate thresholds**
   ```
   Strict:  auto_delete_threshold = 6.0
   Balanced: auto_delete_threshold = 8.0
   Lenient: auto_delete_threshold = 9.5
   ```

4. **Test before enabling auto-delete**
   - Start with `action: "warn"` only
   - Monitor moderation results
   - Adjust thresholds based on false positives
   - Enable `action: "delete"` once confident

### For Reputation Systems

1. **Start with auto-ban disabled**
   - Monitor violation patterns
   - Adjust thresholds
   - Enable once confident

2. **Balance positive/negative points**
   ```
   Good ratio:
   helpful_message = 5 points
   violation = -10 points
   (1 violation = 2 helpful messages to recover)
   ```

3. **Use achievements to encourage behavior**
   - Create meaningful milestones
   - Make icons visually appealing
   - Announce publicly to motivate others

---

## Troubleshooting

### Message not being moderated

**Check**:
1. Is `moderation_enabled` set to `True`?
2. Does the group have GroupSettings? (Check Redis: `group_settings:{group_id}`)
3. Is the moderation_prompt valid? (Check logs for LLM errors)

### False positives (good messages deleted)

**Solutions**:
1. Lower `auto_delete_threshold` (e.g., from 8.0 to 9.0)
2. Refine moderation prompt to be more specific
3. Review `moderation_prompt` - may be too strict
4. Check pattern_filters for overly broad regex

### Bot not responding when mentioned

**This is expected!** Bot will only respond when:
- User @mentions the bot
- Bot uses `Thread.system_prompt` (NOT `moderation_prompt`)

**If bot still doesn't respond**:
- Check that mention detection logic works
- Verify `Thread.system_prompt` is set correctly
- Check logs for errors in LLM streaming

### Reputation not updating

**Check**:
1. Is `reputation_enabled` set to `True`?
2. Is background moderation working? (Check logs for moderation results)
3. Does UserReputation exist? (Check Redis: `user_reputation:{user_id}:{group_id}`)

---

## Redis Keys Reference

```
# GroupSettings
group_settings:{group_id}
group_settings:{group_id}:topic_{topic_id}

# UserReputation
user_reputation:{user_id}:{group_id}
group_leaderboard:{group_id}  # Sorted set by points
group_users_reputation:{group_id}  # Set of user IDs

# Thread (stores system_prompt, NOT moderation_prompt)
thread:group_{group_id}
thread:group_{group_id}_topic_{topic_id}

# GroupLink
group_link:{user_id}:{group_id}
user_groups:{user_id}  # Set of group IDs
group_users:{group_id}  # Set of user IDs
```

---

## Glossary

**Background Moderation**: Passive evaluation of ALL messages using `moderation_prompt`, independent of bot engagement.

**Conversational Engagement**: Active bot responses when @mentioned, using `Thread.system_prompt`.

**Two-Prompt Architecture**: Design pattern separating moderation (background) from conversation (foreground).

**Pre-processing Filters**: Fast, rule-based checks (stoplist, regex) that run before LLM moderation.

**Quality Score**: LLM-assigned score (0-10) indicating message helpfulness/value.

**Auto-ban**: Automatic ban triggered after N violations (configurable).

**Achievement**: Gamification milestone awarded for positive contributions.

**Moderation Prompt Template**: Pre-built prompt for specific community types (crypto, tech, etc.).

---

## See Also

- `MODERATION_INTEGRATION_GUIDE.md` - Implementation details
- `MODERATION_PROMPT_GUIDE.md` - Prompt engineering guide (coming soon)
- `THREAD_ARCHITECTURE.md` - Thread model design
- `luka_bot/services/moderation_service.py` - Service implementation
- `luka_bot/utils/content_detection.py` - Filter utilities
- `luka_bot/utils/moderation_templates.py` - Prompt templates

---

**Version**: 1.0  
**Last Updated**: 2025-10-11  
**Status**: ✅ Core system complete, UI pending

