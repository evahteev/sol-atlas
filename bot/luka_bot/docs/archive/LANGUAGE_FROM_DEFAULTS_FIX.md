# Language from User Defaults - Implementation ✅

## 🎯 **The Requirement**

**User Request**:
> "The default settings should have default language populated from the main app settings (there is default locale there) but after those default - factory settings were applied and re-saved by the user with another language the saved language should be applied"

---

## 📋 **How It Should Work**

### **Scenario 1: First Time User**
1. User hasn't configured default settings yet
2. Bot creates user defaults automatically
3. **Language initialized from user's profile** (e.g., if user profile is "ru", defaults get "ru")

### **Scenario 2: User Changes Default Language**
1. User goes to `/groups` → "Default Settings" → Language → Select "en"
2. Language "en" is **saved** in user's default settings
3. User adds bot to a **new group**
4. Group is created with language **"en"** (from user defaults, NOT profile!)

### **Scenario 3: User Has Different Profile and Default Language**
- User profile language: "ru"
- User default settings language: "en"
- When adding bot to group → **Uses "en"** (from defaults)

**Key Point**: Once user changes default language, it **overrides** profile language for new groups!

---

## ✅ **Implementation**

### **1. Added `language` Field to GroupSettings**

**File**: `luka_bot/models/group_settings.py`

**Added field** (line 65-67):
```python
# Default language for new groups (used in user defaults)
# When user adds bot to a group, this language is applied to the group
language: str = "en"  # "en" or "ru"
```

**Added to serialization** (line 179):
```python
"language": self.language,
```

**Added to deserialization** (line 263):
```python
language=data.get("language", "en"),
```

---

### **2. Added Language to Factory Defaults**

**File**: `luka_bot/models/group_settings_defaults.py`

**Added** (line 23):
```python
"language": "en",  # Default language for new groups (will be set from app locale on first creation)
```

**Note**: This is just the fallback - actual initial value comes from user profile!

---

### **3. Initialize Language from User Profile**

**File**: `luka_bot/services/moderation_service.py`

**Made function async** (line 150):
```python
async def _create_default_settings_template(self, user_id: int) -> GroupSettings:
```

**Get user's profile language** (lines 167-170):
```python
# Get user's profile language to set as initial default
from luka_bot.utils.i18n_helper import get_user_language
user_language = await get_user_language(user_id)
defaults["language"] = user_language
```

**Updated callers to await** (lines 232, 261):
```python
settings = await self._create_default_settings_template(user_id)
```

**Result**: First-time defaults inherit user's profile language!

---

### **4. Copy Language to New Groups**

**File**: `luka_bot/services/moderation_service.py`

**Added to copy list** (line 295):
```python
language=user_defaults.language,  # Copy default language
```

**Result**: New groups get language from user defaults!

---

### **5. Use Language from Defaults on Group Creation**

**File**: `luka_bot/handlers/group_messages.py`

**Before** ❌:
```python
# Get user's preferred language for new group
from luka_bot.utils.i18n_helper import get_user_language
user_language = await get_user_language(user_id)  # ❌ From profile
```

**After** ✅:
```python
# Get user's default language from their group settings defaults
# This allows users to set a default language for all new groups
from luka_bot.services.moderation_service import get_moderation_service
moderation_service_temp = await get_moderation_service()
user_defaults_temp = await moderation_service_temp.get_or_create_user_default_settings(user_id)
user_language = user_defaults_temp.language  # ✅ From defaults
logger.info(f"📝 Using language '{user_language}' for group {group_id} (from user {user_id} default settings)")
```

**Result**: Group creation uses language from user defaults, not profile!

---

## 🔄 **The Complete Flow**

### **First-Time User Flow**

```
1. User has profile language: "ru"
2. User adds bot to group
3. Bot checks: Does user have default settings?
   ❌ NO
4. Bot creates defaults:
   - Calls get_or_create_user_default_settings(user_id)
   - Calls _create_default_settings_template(user_id)
   - Gets user profile language: "ru"
   - Sets defaults.language = "ru"
   - Saves to Redis
5. Bot creates group with language "ru"
```

**Result**: ✅ Group language matches user profile!

---

### **Configured User Flow**

```
1. User profile language: "ru"
2. User goes to /groups → Default Settings → Language → "en"
3. Bot saves: user_defaults.language = "en"
4. User adds bot to new group
5. Bot checks: Does user have default settings?
   ✅ YES
6. Bot gets user_defaults.language = "en"
7. Bot creates group with language "en"
```

**Result**: ✅ Group language matches user's chosen default, NOT profile!

---

## 🎯 **User Control**

Users can now control default language in **two places**:

### **1. Profile Language** (affects UI and DM interactions)
- Set via: `/profile` → Language
- Affects: Bot's DM responses, menu language
- **Also sets initial defaults** when first creating defaults

### **2. Default Settings Language** (affects new groups)
- Set via: `/groups` → "Default Settings" → Language
- Affects: Language of new groups when bot is added
- **Overrides profile language** for group creation

**Independence**: Changing profile language does NOT change default settings language!

---

## 📊 **Example Scenarios**

### **Scenario A: Consistent Russian User**
```
Profile Language: ru
Default Settings Language: ru (auto-set on first use)
New Groups: ru ✅
```

### **Scenario B: Russian User, English Groups**
```
Profile Language: ru
User changes Default Settings Language: en
New Groups: en ✅ (uses defaults, not profile)
Bot's DMs to user: ru ✅ (uses profile)
```

### **Scenario C: User Changes Profile, Defaults Unchanged**
```
Initial:
  Profile: ru
  Defaults: ru
User changes Profile: en
Defaults: ru (unchanged!)
New Groups: ru ✅ (still uses defaults)
```

### **Scenario D: Reset to Defaults**
```
Profile: en
Defaults: ru (user changed it before)
User clicks "Reset to Defaults"
Defaults: en (reset to current profile!)
New Groups: en ✅
```

---

## 🧪 **Testing**

### **Test 1: First-Time User**
1. Set profile language to Russian: `/profile` → Language → Русский
2. Add bot to a group
3. Check group language in `/groups` → Group → Language
4. ✅ **Expected**: Russian

### **Test 2: Change Default Language**
1. Profile language: Russian
2. Go to `/groups` → "Default Settings" → Language → English
3. Add bot to a **new group**
4. Check group language
5. ✅ **Expected**: English (not Russian!)

### **Test 3: Profile vs Defaults Independence**
1. Profile: Russian
2. Defaults: English
3. Change profile to English
4. Check defaults language (should still be English, not changed)
5. Add bot to new group
6. ✅ **Expected**: English (defaults unchanged)

### **Test 4: Reset to Defaults**
1. Profile: English
2. Defaults: Russian (manually set)
3. Click "Reset to Defaults" in `/groups` → Default Settings
4. Check defaults language
5. ✅ **Expected**: English (reset to current profile)

---

## 📝 **Files Modified**

| File | Changes | Purpose |
|------|---------|---------|
| `models/group_settings.py` | Added `language` field + serialization | Store language in settings |
| `models/group_settings_defaults.py` | Added `language: "en"` to defaults | Fallback default value |
| `services/moderation_service.py` | Made `_create_default_settings_template` async + get profile language | Initialize from profile |
| `services/moderation_service.py` | Copy `language` in `create_group_settings_from_user_defaults` | Apply to new groups |
| `handlers/group_messages.py` | Use `user_defaults.language` instead of `get_user_language()` | Use defaults, not profile |

**Total**: 3 files, ~20 lines changed

---

## 🎯 **Summary**

| Aspect | Before | After |
|--------|--------|-------|
| **New groups language** | Always from user profile | From user default settings |
| **First-time language** | Hardcoded "en" | From user profile |
| **User control** | Profile only | Profile + Defaults |
| **Independence** | N/A | Profile ≠ Defaults |
| **Flexibility** | Low | High ✅ |

---

## ✅ **Status**

**Implementation**: ✅ COMPLETE  
**Linter Errors**: 0  
**Breaking Changes**: None (backwards compatible)  
**Testing**: Required  
**User Impact**: High (more control!)

---

## 🎉 **Benefits**

1. ✅ **User Control**: Users can set different language for groups vs DMs
2. ✅ **Consistency**: All new groups use the same language (from defaults)
3. ✅ **Flexibility**: Change default language without affecting profile
4. ✅ **Smart Defaults**: First-time defaults inherit profile language
5. ✅ **Reset**: "Reset to Defaults" syncs with current profile

---

**Ready for testing!** Language flow is now fully implemented! 🚀

