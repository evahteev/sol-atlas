"""
Profile Adapter for AG-UI Protocol

Manages user profiles, settings, and active processes.
"""
from typing import Optional, Dict, Any, List
import time
from loguru import logger

# Lazy imports to avoid circular dependencies
# from luka_bot.services.user_profile_service import get_user_profile_service
# from luka_bot.services.camunda_service import get_camunda_service


class ProfileAdapter:
    """
    Adapter for user profile management.
    
    Provides:
    - User profile retrieval
    - Settings management
    - Active process listing
    - Language preferences
    """
    
    def __init__(self):
        # Lazy initialization to avoid circular imports
        self._profile_service = None
        self._camunda_service = None
    
    @property
    def profile_service(self):
        """Get profile service (lazy loaded)."""
        if self._profile_service is None:
            from luka_bot.services.user_profile_service import get_user_profile_service
            self._profile_service = get_user_profile_service()
        return self._profile_service
    
    @property
    def camunda_service(self):
        """Get Camunda service (lazy loaded)."""
        if self._camunda_service is None:
            from luka_bot.services.camunda_service import get_camunda_service
            self._camunda_service = get_camunda_service()
        return self._camunda_service
    
    async def get_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user profile.
        
        Args:
            user_id: Telegram user ID
        
        Returns:
            User profile dict or None if not found
        """
        try:
            profile = await self.profile_service.get_profile(user_id)
            
            if not profile:
                logger.warning(f"Profile not found for user {user_id}")
                return None
            
            return {
                "user_id": profile.user_id,
                "username": profile.username,
                "first_name": profile.first_name,
                "last_name": profile.last_name,
                "language": profile.language,
                "kb_index": profile.kb_index,
                "is_blocked": profile.is_blocked,
                "settings": {
                    "language": profile.language,
                    "kb_index": profile.kb_index
                },
                "created_at": None,  # Not stored in current model
                "updated_at": None   # Not stored in current model
            }
            
        except Exception as e:
            logger.warning(f"⚠️  Could not get profile for user {user_id}: {e}")
            logger.debug(f"   Returning guest profile defaults")
            # Return guest profile defaults
            return {
                "user_id": user_id,
                "username": f"user_{user_id}",
                "settings": {"language": "en", "theme": "dark"},
                "created_at": None,
                "updated_at": None
            }
    
    async def update_settings(
        self,
        user_id: int,
        settings: Dict[str, Any]
    ) -> bool:
        """
        Update user settings.
        
        Args:
            user_id: Telegram user ID
            settings: Settings to update (language, kb_index, etc.)
        
        Returns:
            True if updated successfully
        """
        try:
            profile = await self.profile_service.get_profile(user_id)
            
            if not profile:
                logger.error(f"Profile not found for user {user_id}")
                return False
            
            # Update settings
            if "language" in settings:
                await self.profile_service.set_language(user_id, settings["language"])
            
            if "kb_index" in settings:
                await self.profile_service.set_kb_index(user_id, settings["kb_index"])
            
            logger.info(f"✅ Updated settings for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating settings for user {user_id}: {e}")
            return False
    
    async def get_active_processes(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get user's active process instances.
        
        Args:
            user_id: Telegram user ID
        
        Returns:
            List of active process instances
        """
        try:
            # Get active process instances for user
            # This is a simplified version - in real implementation,
            # you'd query Camunda for process instances where user is participant
            
            # For now, return empty list as we don't have a direct way to query
            # user's process instances without business key or other identifier
            
            logger.info(f"📋 Retrieved active processes for user {user_id}")
            return []
            
        except Exception as e:
            logger.warning(f"⚠️  Could not get active processes for user {user_id}: {e}")
            logger.debug(f"   Returning empty list")
            return []
    
    async def create_profile(
        self,
        user_id: int,
        user_data: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create new user profile.
        
        Args:
            user_id: Telegram user ID
            user_data: Optional user metadata (username, first_name, etc.)
        
        Returns:
            Created profile dict
        """
        try:
            # Create profile using service
            from luka_bot.models.user_profile import UserProfile
            
            profile = UserProfile(
                user_id=user_id,
                username=user_data.get("username") if user_data else None,
                first_name=user_data.get("first_name") if user_data else None,
                last_name=user_data.get("last_name") if user_data else None,
                language=user_data.get("language", "en") if user_data else "en",
            )
            
            saved = await self.profile_service.save_profile(profile)
            
            if saved:
                logger.info(f"✅ Created profile for user {user_id}")
                return await self.get_profile(user_id)
            else:
                return None
            
        except Exception as e:
            logger.error(f"❌ Error creating profile for user {user_id}: {e}")
            return None
    
    async def delete_profile(self, user_id: int) -> bool:
        """
        Delete user profile (for GDPR compliance).
        
        Args:
            user_id: Telegram user ID
        
        Returns:
            True if deleted successfully
        """
        try:
            success = await self.profile_service.delete_profile(user_id)
            
            if success:
                logger.info(f"🗑️  Deleted profile for user {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error deleting profile for user {user_id}: {e}")
            return False
    
    async def get_language(self, user_id: int) -> str:
        """
        Get user's language preference.
        
        Args:
            user_id: Telegram user ID
        
        Returns:
            Language code (e.g., "en", "ru")
        """
        try:
            language = await self.profile_service.get_language(user_id)
            return language
        except Exception as e:
            logger.warning(f"⚠️  Could not get language for user {user_id}: {e}")
            logger.debug(f"   Defaulting to English")
            return "en"  # Default fallback
    
    async def set_language(self, user_id: int, language: str) -> bool:
        """
        Set user's language preference.
        
        Args:
            user_id: Telegram user ID
            language: Language code (e.g., "en", "ru")
        
        Returns:
            True if set successfully
        """
        try:
            success = await self.profile_service.set_language(user_id, language)
            
            if success:
                logger.info(f"✅ Set language for user {user_id}: {language}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error setting language for user {user_id}: {e}")
            return False
    
    def format_profile_response(self, profile_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Format profile data for AG-UI protocol.
        
        Args:
            profile_data: Profile data dict
        
        Returns:
            Formatted response
        """
        if not profile_data:
            return {
                "type": "error",
                "code": "PROFILE_NOT_FOUND",
                "message": "Profile not found",
                "timestamp": int(time.time() * 1000)
            }
        
        return {
            "type": "profileData",
            "profile": profile_data,
            "timestamp": int(time.time() * 1000)
        }


# Singleton instance
_profile_adapter: Optional[ProfileAdapter] = None


def get_profile_adapter() -> ProfileAdapter:
    """Get or create ProfileAdapter singleton."""
    global _profile_adapter
    if _profile_adapter is None:
        _profile_adapter = ProfileAdapter()
        logger.info("✅ ProfileAdapter singleton created")
    return _profile_adapter

