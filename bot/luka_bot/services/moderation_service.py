"""
Moderation Service - Background moderation, reputation, and content filtering.

Handles:
- GroupSettings management
- UserReputation tracking
- Background message moderation (with moderation_prompt)
- Achievement system
- Ban management
"""
import json
import re
from typing import Optional, List
from datetime import datetime
from loguru import logger

from luka_bot.models.group_settings import GroupSettings
from luka_bot.models.user_reputation import UserReputation
from luka_bot.models.group_settings_defaults import DEFAULT_GROUP_SETTINGS


class ModerationService:
    """
    Service for group moderation and reputation management.
    
    Implements two-prompt architecture:
    - GroupSettings.moderation_prompt: Background evaluation of ALL messages
    - Thread.system_prompt: Active conversation when bot is engaged
    """
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    # ============================================================================
    # GroupSettings Management
    # ============================================================================
    
    async def get_group_settings(
        self,
        group_id: int,
        topic_id: Optional[int] = None
    ) -> Optional[GroupSettings]:
        """
        Get GroupSettings for a group or topic.
        
        Args:
            group_id: Telegram group ID
            topic_id: Optional topic ID (None = group-wide settings)
        
        Returns:
            GroupSettings or None if not found
        """
        try:
            key = GroupSettings.get_group_settings_key(group_id, topic_id)
            data = await self.redis.hgetall(key)
            
            if not data:
                return None
            
            # Decode bytes to strings
            decoded_data = {
                k.decode() if isinstance(k, bytes) else k:
                v.decode() if isinstance(v, bytes) else v
                for k, v in data.items()
            }
            
            # DEBUG: Log key settings being loaded
            logger.debug(f"📖 Loading from {key}: AI={decoded_data.get('ai_assistant_enabled')}, Silent={decoded_data.get('silent_mode')}, KB={decoded_data.get('kb_indexation_enabled')}, Moderation={decoded_data.get('moderation_enabled')}")
            
            settings = GroupSettings.from_dict(decoded_data)
            
            # DEBUG: Log parsed settings
            logger.debug(f"✅ Parsed settings: AI={settings.ai_assistant_enabled}, Silent={settings.silent_mode}, KB={settings.kb_indexation_enabled}, Moderation={settings.moderation_enabled}")
            
            return settings
            
        except Exception as e:
            logger.error(f"❌ Error getting group settings for {group_id}: {e}")
            return None
    
    async def save_group_settings(self, settings: GroupSettings) -> bool:
        """
        Save GroupSettings to Redis.
        
        Args:
            settings: GroupSettings instance
        
        Returns:
            True if successful
        """
        try:
            key = settings.get_redis_key()
            settings.updated_at = datetime.utcnow()
            
            settings_dict = settings.to_dict()
            # DEBUG: Log key settings being saved
            logger.debug(f"💾 Saving to {key}: AI={settings_dict.get('ai_assistant_enabled')}, Silent={settings_dict.get('silent_mode')}, KB={settings_dict.get('kb_indexation_enabled')}, Moderation={settings_dict.get('moderation_enabled')}")
            
            await self.redis.hset(key, mapping=settings_dict)
            
            logger.info(f"✅ Saved group settings: {key}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving group settings: {e}")
            return False
    
    async def create_default_group_settings(
        self,
        group_id: int,
        created_by: int,
        topic_id: Optional[int] = None
    ) -> GroupSettings:
        """
        Create default GroupSettings for a new group/topic using factory defaults.
        
        Args:
            group_id: Telegram group ID
            created_by: Admin user_id who triggered creation
            topic_id: Optional topic ID
        
        Returns:
            Created GroupSettings
        """
        # Start with factory defaults
        defaults = DEFAULT_GROUP_SETTINGS.copy()
        defaults["stoplist_words"] = defaults["stoplist_words"].copy()
        
        settings = GroupSettings(
            group_id=group_id,
            topic_id=topic_id,
            created_by=created_by,
            **defaults  # Apply all factory defaults
        )
        
        await self.save_group_settings(settings)
        logger.info(f"✨ Created default group settings for group {group_id} with factory defaults")
        
        return settings
    
    # ============================================================================
    # User Default Settings (Template for New Groups)
    # ============================================================================
    
    async def _create_default_settings_template(self, user_id: int) -> GroupSettings:
        """
        Create a fresh GroupSettings object with factory defaults.
        
        Uses DEFAULT_GROUP_SETTINGS dict from group_settings_defaults module.
        Language is initialized from user's profile language preference.
        
        Args:
            user_id: User ID to create defaults for
            
        Returns:
            GroupSettings initialized with factory defaults
        """
        # Copy stoplist words to avoid shared reference
        defaults = DEFAULT_GROUP_SETTINGS.copy()
        defaults["stoplist_words"] = defaults["stoplist_words"].copy()
        
        # Get user's profile language to set as initial default
        from luka_bot.utils.i18n_helper import get_user_language
        user_language = await get_user_language(user_id)
        defaults["language"] = user_language
        
        return GroupSettings(
            group_id=user_id,  # Use user_id as identifier
            is_user_default=True,
            created_by=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            **defaults  # Unpack all defaults from the dict
        )
    
    async def get_user_default_settings(self, user_id: int) -> Optional[GroupSettings]:
        """
        Get user's default template for new groups.
        
        Args:
            user_id: User ID
            
        Returns:
            GroupSettings configured as user default, or None if not found
        """
        try:
            key = GroupSettings.get_user_default_key(user_id)
            data = await self.redis.hgetall(key)
            
            if not data:
                return None
            
            # Decode bytes to strings
            decoded_data = {
                k.decode() if isinstance(k, bytes) else k:
                v.decode() if isinstance(v, bytes) else v
                for k, v in data.items()
            }
            
            return GroupSettings.from_dict(decoded_data)
            
        except Exception as e:
            logger.error(f"❌ Error getting user default settings for {user_id}: {e}")
            return None
    
    async def get_or_create_user_default_settings(self, user_id: int) -> GroupSettings:
        """
        Get or create user's default template settings.
        
        Creates a sensible default template if none exists:
        - silent_mode: False (show bot service/system messages)
        - ai_assistant_enabled: True (enable AI responses)
        - moderation_enabled: False (opt-in for new groups)
        - reputation_enabled: False (opt-in for new groups)
        
        Args:
            user_id: User ID
            
        Returns:
            GroupSettings as user default template
        """
        settings = await self.get_user_default_settings(user_id)
        
        if not settings:
            # Create default template from constants
            settings = await self._create_default_settings_template(user_id)
            await self.save_group_settings(settings)
            logger.info(f"✨ Created default template settings for user {user_id}")
        
        return settings
    
    async def reset_user_default_settings(self, user_id: int) -> GroupSettings:
        """
        Reset user's default template to factory defaults.
        
        This will:
        1. Delete existing user defaults from Redis
        2. Create fresh defaults from constants
        3. Save them back to Redis
        
        Used when user clicks "Reset to Defaults" button.
        
        Args:
            user_id: User ID
            
        Returns:
            New GroupSettings with factory defaults
        """
        # Delete existing settings
        key = f"user_default_group_settings:{user_id}"
        await self.redis.delete(key)
        logger.info(f"🗑️ Deleted existing default settings for user {user_id}")
        
        # Create and save fresh defaults
        settings = await self._create_default_settings_template(user_id)
        await self.save_group_settings(settings)
        logger.info(f"✨ Reset user {user_id} defaults to factory settings")
        
        return settings
    
    async def create_group_settings_from_user_defaults(
        self,
        user_id: int,
        group_id: int,
        topic_id: Optional[int] = None
    ) -> GroupSettings:
        """
        Create new group settings based on user's default template.
        
        Applies user's preferences from their default template to the new group,
        allowing users to standardize settings across groups they manage.
        
        Args:
            user_id: User who added the bot
            group_id: Group ID
            topic_id: Optional topic ID
            
        Returns:
            New GroupSettings for the group, initialized from user's template
        """
        # Get user's defaults (creates if not exists)
        user_defaults = await self.get_or_create_user_default_settings(user_id)
        
        # Create group settings from template - copy ALL settings from user defaults
        group_settings = GroupSettings(
            group_id=group_id,
            topic_id=topic_id,
            is_user_default=False,
            
            # Copy bot behavior settings from template
            silent_mode=user_defaults.silent_mode,
            ai_assistant_enabled=user_defaults.ai_assistant_enabled,
            kb_indexation_enabled=user_defaults.kb_indexation_enabled,
            language=user_defaults.language,  # Copy default language
            
            # Copy moderation settings from template
            moderate_admins_enabled=user_defaults.moderate_admins_enabled,
            moderation_enabled=user_defaults.moderation_enabled,
            moderation_prompt=user_defaults.moderation_prompt,
            reputation_enabled=user_defaults.reputation_enabled,
            auto_ban_enabled=user_defaults.auto_ban_enabled,
            
            # Copy content filters from template
            delete_service_messages=user_defaults.delete_service_messages,
            service_message_types=user_defaults.service_message_types.copy(),
            delete_links=user_defaults.delete_links,
            delete_images=user_defaults.delete_images,
            delete_videos=user_defaults.delete_videos,
            delete_stickers=user_defaults.delete_stickers,
            delete_forwarded=user_defaults.delete_forwarded,
            
            # Copy stoplist from template
            stoplist_enabled=user_defaults.stoplist_enabled,
            stoplist_words=user_defaults.stoplist_words.copy(),
            stoplist_case_sensitive=user_defaults.stoplist_case_sensitive,
            stoplist_auto_delete=user_defaults.stoplist_auto_delete,
            
            # Copy thresholds from template
            auto_delete_threshold=user_defaults.auto_delete_threshold,
            auto_warn_threshold=user_defaults.auto_warn_threshold,
            quality_threshold=user_defaults.quality_threshold,
            
            # Metadata
            created_by=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        await self.save_group_settings(group_settings)
        logger.info(f"✨ Created group settings for {group_id} from user {user_id} template")
        
        return group_settings
    
    async def delete_group_settings(
        self,
        group_id: int,
        topic_id: Optional[int] = None
    ) -> bool:
        """
        Delete GroupSettings.
        
        Args:
            group_id: Telegram group ID
            topic_id: Optional topic ID
        
        Returns:
            True if deleted
        """
        try:
            key = GroupSettings.get_group_settings_key(group_id, topic_id)
            await self.redis.delete(key)
            logger.info(f"🗑️ Deleted group settings: {key}")
            return True
        except Exception as e:
            logger.error(f"❌ Error deleting group settings: {e}")
            return False
    
    # ============================================================================
    # UserReputation Management
    # ============================================================================
    
    async def get_user_reputation(
        self,
        user_id: int,
        group_id: int
    ) -> UserReputation:
        """
        Get UserReputation for a user in a group.
        
        Creates new reputation if doesn't exist.
        
        Args:
            user_id: Telegram user ID
            group_id: Telegram group ID
        
        Returns:
            UserReputation instance
        """
        try:
            key = UserReputation.get_user_reputation_key(user_id, group_id)
            data = await self.redis.hgetall(key)
            
            if not data:
                # Create new reputation
                reputation = UserReputation(user_id=user_id, group_id=group_id)
                await self.save_user_reputation(reputation)
                return reputation
            
            # Decode bytes to strings
            decoded_data = {
                k.decode() if isinstance(k, bytes) else k:
                v.decode() if isinstance(v, bytes) else v
                for k, v in data.items()
            }
            
            reputation = UserReputation.from_dict(decoded_data)
            
            # Check if temporary ban expired
            if reputation.is_ban_expired():
                reputation.unban()
                await self.save_user_reputation(reputation)
            
            return reputation
            
        except Exception as e:
            logger.error(f"❌ Error getting user reputation: {e}")
            # Return new reputation on error
            return UserReputation(user_id=user_id, group_id=group_id)
    
    async def save_user_reputation(self, reputation: UserReputation) -> bool:
        """
        Save UserReputation to Redis.
        
        Args:
            reputation: UserReputation instance
        
        Returns:
            True if successful
        """
        try:
            key = reputation.get_redis_key()
            reputation.updated_at = datetime.utcnow()
            
            await self.redis.hset(key, mapping=reputation.to_dict())
            
            # Update leaderboard (sorted set by points)
            leaderboard_key = UserReputation.get_group_leaderboard_key(reputation.group_id)
            await self.redis.zadd(leaderboard_key, {str(reputation.user_id): reputation.points})
            
            # Add to group users set
            users_key = UserReputation.get_group_users_reputation_key(reputation.group_id)
            await self.redis.sadd(users_key, str(reputation.user_id))
            
            logger.debug(f"💾 Saved user reputation: {key}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving user reputation: {e}")
            return False
    
    async def delete_all_group_reputations(self, group_id: int) -> int:
        """
        Delete all user reputations for a group (used in /reset).
        
        Args:
            group_id: Telegram group ID
        
        Returns:
            Number of reputations deleted
        """
        try:
            # Get all users with reputation in this group
            users_key = UserReputation.get_group_users_reputation_key(group_id)
            user_ids_bytes = await self.redis.smembers(users_key)
            user_ids = [
                int(uid.decode() if isinstance(uid, bytes) else uid)
                for uid in user_ids_bytes
            ]
            
            # Delete each reputation
            deleted_count = 0
            for user_id in user_ids:
                key = UserReputation.get_user_reputation_key(user_id, group_id)
                await self.redis.delete(key)
                deleted_count += 1
            
            # Delete leaderboard and users set
            leaderboard_key = UserReputation.get_group_leaderboard_key(group_id)
            await self.redis.delete(leaderboard_key)
            await self.redis.delete(users_key)
            
            logger.info(f"🗑️ Deleted {deleted_count} user reputations for group {group_id}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"❌ Error deleting group reputations: {e}")
            return 0
    
    async def get_group_leaderboard(
        self,
        group_id: int,
        limit: int = 10
    ) -> List[tuple[int, int]]:
        """
        Get top users by reputation points.
        
        Args:
            group_id: Telegram group ID
            limit: Number of top users to return
        
        Returns:
            List of (user_id, points) tuples, sorted by points descending
        """
        try:
            leaderboard_key = UserReputation.get_group_leaderboard_key(group_id)
            
            # Get top users (ZREVRANGE for descending order)
            top_users = await self.redis.zrevrange(
                leaderboard_key,
                0,
                limit - 1,
                withscores=True
            )
            
            # Convert to list of tuples
            leaderboard = [
                (int(user_id.decode() if isinstance(user_id, bytes) else user_id), int(score))
                for user_id, score in top_users
            ]
            
            return leaderboard
            
        except Exception as e:
            logger.error(f"❌ Error getting leaderboard: {e}")
            return []
    
    # ============================================================================
    # Background Moderation (LLM-based evaluation)
    # ============================================================================
    
    async def evaluate_message_moderation(
        self,
        message_text: str,
        group_settings: GroupSettings,
        user_id: int,
        group_id: int
    ) -> dict:
        """
        Evaluate a message using moderation_prompt.
        
        This is the KEY method for background moderation.
        Uses GroupSettings.moderation_prompt (NOT Thread.system_prompt).
        
        Args:
            message_text: Message content
            group_settings: GroupSettings with moderation_prompt
            user_id: User who sent message
            group_id: Group where message was sent
        
        Returns:
            Moderation result dict:
            {
                "helpful": true/false,
                "violation": null or "spam"|"toxic"|"off-topic",
                "quality_score": 0-10,
                "action": "none"|"warn"|"delete",
                "reason": "Brief explanation"
            }
        """
        if not group_settings.moderation_enabled:
            return {"helpful": None, "violation": None, "action": "none"}
        
        try:
            from pydantic_ai import Agent
            from pydantic_ai.models.openai import OpenAIModel
            from pydantic_ai.providers.ollama import OllamaProvider
            from luka_bot.core.config import settings
            
            # Get moderation prompt (use default if not set)
            moderation_prompt = (
                group_settings.moderation_prompt or
                self._get_default_moderation_prompt()
            )
            
            # Build full prompt with message
            full_prompt = f"""{moderation_prompt}

MESSAGE TO EVALUATE:
User ID: {user_id}
Group ID: {group_id}
Content: {message_text}

Return ONLY valid JSON with these exact fields:
{{
  "helpful": true/false,
  "violation": null or "spam"|"toxic"|"off-topic"|"other",
  "quality_score": 0-10,
  "action": "none"|"warn"|"delete",
  "reason": "Brief explanation"
}}"""
            
            # Create direct agent for moderation with automatic fallback (Ollama → OpenAI)
            from luka_bot.services.llm_model_factory import create_moderation_model
            
            model = await create_moderation_model(context=f"mod_g{group_id}_u{user_id}")
            
            agent: Agent[None, str] = Agent(
                model,
                system_prompt="You are a content moderation system. Return ONLY valid JSON, no additional text.",
                retries=1
            )
            
            # Call LLM with low temperature for consistent moderation
            result = await agent.run(
                full_prompt,
                model_settings={"temperature": 0.1}
            )
            
            # Parse JSON response
            try:
                # Extract text from result (handle different return types)
                if hasattr(result, 'output'):
                    result_text = str(result.output)
                elif hasattr(result, 'data'):
                    result_text = str(result.data)
                else:
                    result_text = str(result)
                
                # Clean up response (remove markdown code blocks if present)
                result_text = result_text.strip()
                if result_text.startswith("```json"):
                    result_text = result_text[7:]
                if result_text.startswith("```"):
                    result_text = result_text[3:]
                if result_text.endswith("```"):
                    result_text = result_text[:-3]
                result_text = result_text.strip()
                
                moderation_data = json.loads(result_text)
                
                logger.info(f"🛡️ Moderation result for user {user_id}: {moderation_data}")
                return moderation_data
                
            except json.JSONDecodeError as e:
                logger.error(f"❌ Failed to parse moderation JSON: {result_text[:200] if 'result_text' in locals() else str(result)}")
                return {"helpful": None, "violation": None, "action": "none", "reason": "Parse error"}
            
        except Exception as e:
            logger.error(f"❌ Error in evaluate_message_moderation: {e}", exc_info=True)
            return {"helpful": None, "violation": None, "action": "none", "reason": "Error"}
    
    # ============================================================================
    # Reputation Updates
    # ============================================================================
    
    async def update_user_reputation(
        self,
        user_id: int,
        group_id: int,
        moderation_result: dict,
        group_settings: GroupSettings,
        is_reply: bool = False,
        is_mention: bool = False
    ) -> UserReputation:
        """
        Update user reputation based on moderation result.
        
        Args:
            user_id: User ID
            group_id: Group ID
            moderation_result: Result from evaluate_message_moderation()
            group_settings: Group settings for point rules
            is_reply: Whether message is a reply
            is_mention: Whether message mentions bot
        
        Returns:
            Updated UserReputation
        """
        reputation = await self.get_user_reputation(user_id, group_id)
        
        # Update activity
        reputation.update_activity(is_reply=is_reply, is_mention=is_mention)
        
        # Award points for helpful/quality messages
        if moderation_result.get("helpful"):
            reputation.helpful_messages += 1
            reputation.points += group_settings.points_per_helpful_message
            logger.info(f"➕ User {user_id} +{group_settings.points_per_helpful_message} points (helpful)")
        
        quality_score = moderation_result.get("quality_score", 0)
        if quality_score >= group_settings.quality_threshold:
            reputation.quality_replies += 1
            reputation.points += group_settings.points_per_quality_reply
            logger.info(f"➕ User {user_id} +{group_settings.points_per_quality_reply} points (quality)")
        
        # Handle violations
        violation_type = moderation_result.get("violation")
        if violation_type:
            # Determine penalty based on type
            if violation_type == "spam":
                penalty = group_settings.spam_penalty
            elif violation_type == "toxic":
                penalty = group_settings.toxic_penalty
            else:
                penalty = group_settings.violation_penalty
            
            reputation.add_violation(
                violation_type=violation_type,
                reason=moderation_result.get("reason", "No reason provided"),
                penalty=penalty
            )
            logger.warning(f"⚠️ User {user_id} violation: {violation_type} ({penalty} points)")
        
        # Check for auto-ban
        if (group_settings.auto_ban_enabled and
            reputation.violations >= group_settings.violations_before_ban and
            not reputation.is_banned):
            
            reputation.ban(
                reason=f"Exceeded violation threshold ({reputation.violations} violations)",
                duration_hours=group_settings.ban_duration_hours
            )
            logger.warning(f"🚫 User {user_id} auto-banned in group {group_id}")
        
        # Save updated reputation
        await self.save_user_reputation(reputation)
        
        return reputation
    
    # ============================================================================
    # Achievement System
    # ============================================================================
    
    async def check_achievements(
        self,
        user_id: int,
        group_id: int,
        group_settings: GroupSettings
    ) -> List[dict]:
        """
        Check if user has earned any new achievements.
        
        Args:
            user_id: User ID
            group_id: Group ID
            group_settings: Group settings with achievement rules
        
        Returns:
            List of newly awarded achievements
        """
        if not group_settings.achievements_enabled:
            return []
        
        reputation = await self.get_user_reputation(user_id, group_id)
        new_achievements = []
        
        for rule in group_settings.achievement_rules:
            achievement_id = rule.get("id")
            
            # Skip if already has this achievement
            if achievement_id in reputation.achievements:
                continue
            
            # Evaluate condition
            condition = rule.get("condition", "")
            if self._evaluate_achievement_condition(condition, reputation):
                # Award achievement
                success = reputation.add_achievement(
                    achievement_id=achievement_id,
                    achievement_name=rule.get("name", achievement_id),
                    points=rule.get("points", group_settings.points_per_achievement)
                )
                
                if success:
                    new_achievements.append(rule)
                    logger.info(f"🏆 User {user_id} earned achievement: {achievement_id}")
        
        if new_achievements:
            await self.save_user_reputation(reputation)
        
        return new_achievements
    
    def _evaluate_achievement_condition(self, condition: str, reputation: UserReputation) -> bool:
        """
        Evaluate an achievement condition.
        
        Examples:
        - "helpful_messages >= 10"
        - "points >= 100"
        - "quality_replies >= 5"
        """
        try:
            # Replace field names with actual values
            context = {
                "helpful_messages": reputation.helpful_messages,
                "quality_replies": reputation.quality_replies,
                "points": reputation.points,
                "message_count": reputation.message_count,
                "violations": reputation.violations,
            }
            
            # Evaluate condition safely
            return eval(condition, {"__builtins__": {}}, context)
        except Exception as e:
            logger.error(f"❌ Error evaluating achievement condition '{condition}': {e}")
            return False
    
    # ============================================================================
    # Ban Management
    # ============================================================================
    
    async def ban_user(
        self,
        user_id: int,
        group_id: int,
        reason: str,
        duration_hours: int = 0,
        banned_by: Optional[int] = None
    ) -> bool:
        """
        Ban a user.
        
        Args:
            user_id: User ID to ban
            group_id: Group ID
            reason: Ban reason
            duration_hours: Ban duration (0 = permanent)
            banned_by: Admin user_id who issued ban
        
        Returns:
            True if successful
        """
        try:
            reputation = await self.get_user_reputation(user_id, group_id)
            reputation.ban(reason=reason, duration_hours=duration_hours, banned_by=banned_by)
            await self.save_user_reputation(reputation)
            
            logger.warning(f"🚫 Banned user {user_id} in group {group_id}: {reason}")
            return True
        except Exception as e:
            logger.error(f"❌ Error banning user: {e}")
            return False
    
    async def unban_user(self, user_id: int, group_id: int) -> bool:
        """
        Unban a user.
        
        Args:
            user_id: User ID to unban
            group_id: Group ID
        
        Returns:
            True if successful
        """
        try:
            reputation = await self.get_user_reputation(user_id, group_id)
            reputation.unban()
            await self.save_user_reputation(reputation)
            
            logger.info(f"✅ Unbanned user {user_id} in group {group_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Error unbanning user: {e}")
            return False
    
    # ============================================================================
    # Helper Methods
    # ============================================================================
    
    def _get_default_moderation_prompt(self) -> str:
        """Get default general-purpose moderation prompt."""
        return """You are a content moderator for a Telegram group.

Evaluate each message for:
1. HELPFUL: Contributes to discussion, answers questions, shares knowledge
2. SPAM: Advertising, repeated promotions, off-topic commercial content
3. TOXIC: Personal attacks, harassment, hate speech, excessive profanity
4. OFF-TOPIC: Completely unrelated to group purpose

Return JSON with these exact fields:
{
  "helpful": true/false,
  "violation": null or "spam"|"toxic"|"off-topic",
  "quality_score": 0-10 (how valuable is this message),
  "action": "none"|"warn"|"delete",
  "reason": "Brief 1-sentence explanation"
}

Examples:
- Helpful technical answer → {"helpful": true, "violation": null, "quality_score": 8, "action": "none"}
- "Buy my course!!!" → {"helpful": false, "violation": "spam", "quality_score": 0, "action": "delete"}
- Personal insult → {"helpful": false, "violation": "toxic", "quality_score": 0, "action": "warn"}

Be fair and consistent. When in doubt, prefer "warn" over "delete"."""


# Singleton instance
_moderation_service: Optional[ModerationService] = None


async def get_moderation_service() -> ModerationService:
    """Get or create ModerationService singleton."""
    global _moderation_service
    if _moderation_service is None:
        from luka_bot.core.loader import redis_client
        _moderation_service = ModerationService(redis_client)
        logger.info("✅ ModerationService singleton created")
    return _moderation_service

