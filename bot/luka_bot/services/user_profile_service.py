"""
User Profile Service - Phase 4.

Manages user profiles with Redis persistence.
"""
from typing import Optional
from aiogram.types import User as TelegramUser
from loguru import logger

from luka_bot.core.loader import redis_client
from luka_bot.core.config import settings
from luka_bot.models.user_profile import UserProfile


class UserProfileService:
    """Service for managing user profiles."""
    
    def __init__(self):
        self.redis = redis_client
    
    @classmethod
    async def get_user_profile(cls, user_id: int) -> Optional[UserProfile]:
        """
        Class method to get user profile (for agent factory compatibility).
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            UserProfile if exists, None otherwise
        """
        service = cls()
        return await service.get_profile(user_id)
    
    async def get_or_create_profile(
        self,
        user_id: int,
        telegram_user: Optional[TelegramUser] = None
    ) -> UserProfile:
        """
        Get user profile or create if doesn't exist.
        
        Args:
            user_id: Telegram user ID
            telegram_user: Optional Telegram user object for auto-filling data
            
        Returns:
            UserProfile instance
        """
        profile = await self.get_profile(user_id)
        
        if not profile:
            # Create new profile
            profile = UserProfile(
                user_id=user_id,
                username=telegram_user.username if telegram_user else None,
                first_name=telegram_user.first_name if telegram_user else None,
                last_name=telegram_user.last_name if telegram_user else None,
                language=telegram_user.language_code if telegram_user and telegram_user.language_code in ["en", "ru"] else settings.DEFAULT_LOCALE,
            )
            await self.save_profile(profile)
            logger.info(f"✨ Created new profile for user {user_id}")
        
        return profile
    
    async def get_or_create_minimal_profile(
        self,
        user_id: int,
        telegram_user: Optional[TelegramUser] = None
    ) -> UserProfile:
        """
        Get or create minimal profile for users seen in groups.
        Unlike get_or_create_profile, this creates profiles with is_blocked=False
        to indicate they haven't onboarded via DM yet.
        
        Args:
            user_id: Telegram user ID
            telegram_user: Optional Telegram user object
            
        Returns:
            UserProfile instance
        """
        profile = await self.get_profile(user_id)
        if profile:
            return profile
        
        # Create minimal profile (not onboarded)
        username = telegram_user.username if telegram_user else None
        first_name = telegram_user.first_name if telegram_user else None
        last_name = telegram_user.last_name if telegram_user else None
        language = telegram_user.language_code if telegram_user and telegram_user.language_code in ["en", "ru"] else settings.DEFAULT_LOCALE
        
        profile = UserProfile(
            user_id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language=language,
            is_blocked=False,  # Not onboarded until they DM the bot
            kb_index=f"tg-kb-user-{user_id}",  # Standard KB index
        )
        
        await self.save_profile(profile)
        logger.info(f"✨ Created minimal profile for user {user_id} from group activity")
        return profile
    
    async def get_profile(self, user_id: int) -> Optional[UserProfile]:
        """
        Get user profile.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            UserProfile if exists, None otherwise
        """
        try:
            key = f"user_profile:{user_id}"
            data = await self.redis.hgetall(key)
            
            if not data:
                return None
            
            # Decode bytes to strings (Redis returns bytes)
            decoded_data = {
                k.decode() if isinstance(k, bytes) else k: 
                v.decode() if isinstance(v, bytes) else v
                for k, v in data.items()
            }
            
            profile = UserProfile.from_dict(decoded_data)
            return profile
            
        except Exception as e:
            logger.error(f"❌ Error getting profile for user {user_id}: {e}")
            return None
    
    async def save_profile(self, profile: UserProfile) -> bool:
        """
        Save user profile.
        
        Args:
            profile: UserProfile instance
            
        Returns:
            True if saved successfully
        """
        try:
            key = f"user_profile:{profile.user_id}"
            data = profile.to_dict()
            
            await self.redis.hset(key, mapping=data)
            logger.debug(f"💾 Saved profile for user {profile.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving profile: {e}")
            return False
    
    async def get_language(self, user_id: int) -> str:
        """
        Get user's language preference.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Language code ("en" or "ru"), defaults to configured DEFAULT_LOCALE
        """
        try:
            profile = await self.get_profile(user_id)
            return profile.language if profile else settings.DEFAULT_LOCALE
        except Exception as e:
            logger.error(f"❌ Error getting language for user {user_id}: {e}")
            return settings.DEFAULT_LOCALE
    
    async def update_language(self, user_id: int, language: str) -> bool:
        """
        Update user's language preference.
        
        Args:
            user_id: Telegram user ID
            language: Language code ("en" or "ru")
            
        Returns:
            True if updated successfully
        """
        try:
            profile = await self.get_profile(user_id)
            if not profile:
                logger.warning(f"⚠️  Profile not found for user {user_id}")
                return False
            
            profile.language = language
            profile.updated_at = profile.updated_at  # Will be updated in to_dict
            
            await self.save_profile(profile)
            logger.info(f"🌍 Updated language for user {user_id}: {language}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating language: {e}")
            return False
    
    async def mark_onboarding_complete(self, user_id: int) -> bool:
        """
        Mark onboarding as complete for user.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            True if marked successfully
        """
        try:
            profile = await self.get_profile(user_id)
            if not profile:
                logger.warning(f"⚠️  Profile not found for user {user_id}")
                return False
            
            profile.mark_onboarding_complete()
            await self.save_profile(profile)
            logger.info(f"✅ Marked onboarding complete for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error marking onboarding complete: {e}")
            return False
    
    async def needs_onboarding(self, user_id: int) -> bool:
        """
        Check if user needs onboarding.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            True if needs onboarding (is_blocked == False or profile doesn't exist)
        """
        try:
            profile = await self.get_profile(user_id)
            if not profile:
                return True  # New user needs onboarding
            return profile.needs_onboarding()
            
        except Exception as e:
            logger.error(f"❌ Error checking onboarding status: {e}")
            return True  # Err on the side of caution
    
    async def reset_onboarding(self, user_id: int) -> bool:
        """
        Reset onboarding status for user (set is_blocked to False).
        Used by /reset command to allow user to go through onboarding again.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            True if reset successfully
        """
        try:
            profile = await self.get_profile(user_id)
            if not profile:
                logger.warning(f"⚠️  Profile not found for user {user_id}, cannot reset onboarding")
                return False
            
            profile.is_blocked = False  # Reset to trigger onboarding
            await self.save_profile(profile)
            logger.info(f"🔄 Reset onboarding status for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error resetting onboarding: {e}")
            return False
    
    async def set_kb_index(self, user_id: int, kb_index: str) -> bool:
        """
        Set KB index for user.
        
        Args:
            user_id: Telegram user ID
            kb_index: Elasticsearch KB index name (e.g., "tg-kb-user-922705")
            
        Returns:
            True if set successfully
        """
        try:
            profile = await self.get_profile(user_id)
            if not profile:
                logger.warning(f"⚠️  Profile not found for user {user_id}")
                return False
            
            profile.kb_index = kb_index
            await self.save_profile(profile)
            logger.info(f"📚 Set KB index for user {user_id}: {kb_index}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error setting KB index: {e}")
            return False
    
    async def get_kb_index(self, user_id: int) -> Optional[str]:
        """
        Get KB index for user.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            KB index name if set, None otherwise
        """
        try:
            profile = await self.get_profile(user_id)
            return profile.kb_index if profile else None
            
        except Exception as e:
            logger.error(f"❌ Error getting KB index: {e}")
            return None


# Global service instance
_user_profile_service: Optional[UserProfileService] = None


def get_user_profile_service() -> UserProfileService:
    """Get or create user profile service instance."""
    global _user_profile_service
    if _user_profile_service is None:
        _user_profile_service = UserProfileService()
    return _user_profile_service

