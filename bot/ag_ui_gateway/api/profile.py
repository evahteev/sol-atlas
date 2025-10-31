"""
Profile API Endpoints

Handles user profile management, settings, and active processes.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict, Any
from loguru import logger

from ag_ui_gateway.auth.permissions import require_authenticated
from ag_ui_gateway.adapters.profile_adapter import get_profile_adapter

router = APIRouter()


class SettingsUpdate(BaseModel):
    """Settings update request."""
    language: Optional[str] = None
    kb_index: Optional[str] = None


@router.get("/profile")
async def get_profile(user_data: dict = Depends(require_authenticated)):
    """
    Get current user's profile.
    
    Returns:
        User profile with settings and metadata
    """
    try:
        user_id = user_data.get("user_id")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found"
            )
        
        logger.info(f"📋 Profile request for user {user_id}")
        
        profile_adapter = get_profile_adapter()
        profile = await profile_adapter.get_profile(user_id)
        
        if not profile:
            # Create profile if doesn't exist
            profile = await profile_adapter.create_profile(
                user_id=user_id,
                user_data={
                    "username": user_data.get("username"),
                    "first_name": user_data.get("first_name"),
                    "last_name": user_data.get("last_name"),
                    "language": "en"
                }
            )
            
            if not profile:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create profile"
                )
        
        # Get active processes
        active_processes = await profile_adapter.get_active_processes(user_id)
        
        return {
            "profile": profile,
            "active_processes": active_processes,
            "active_processes_count": len(active_processes)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve profile"
        )


@router.patch("/profile/settings")
async def update_settings(
    settings_update: SettingsUpdate,
    user_data: dict = Depends(require_authenticated)
):
    """
    Update user settings.
    
    Args:
        settings_update: Settings to update (language, kb_index)
        user_data: Authenticated user data
    
    Returns:
        Updated settings
    """
    try:
        user_id = user_data.get("user_id")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found"
            )
        
        logger.info(f"⚙️  Settings update for user {user_id}")
        
        # Convert to dict, excluding None values
        settings_dict = settings_update.model_dump(exclude_none=True)
        
        if not settings_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No settings provided"
            )
        
        profile_adapter = get_profile_adapter()
        success = await profile_adapter.update_settings(user_id, settings_dict)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update settings"
            )
        
        # Get updated profile
        profile = await profile_adapter.get_profile(user_id)
        
        return {
            "message": "Settings updated successfully",
            "settings": profile.get("settings", {}) if profile else {}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update settings"
        )


@router.get("/profile/language")
async def get_language(user_data: dict = Depends(require_authenticated)):
    """
    Get user's language preference.
    
    Returns:
        Language code
    """
    try:
        user_id = user_data.get("user_id")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found"
            )
        
        profile_adapter = get_profile_adapter()
        language = await profile_adapter.get_language(user_id)
        
        return {
            "language": language
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting language: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve language"
        )


@router.put("/profile/language")
async def set_language(
    language: str,
    user_data: dict = Depends(require_authenticated)
):
    """
    Set user's language preference.
    
    Args:
        language: Language code (e.g., "en", "ru")
        user_data: Authenticated user data
    
    Returns:
        Success message
    """
    try:
        user_id = user_data.get("user_id")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found"
            )
        
        # Validate language
        if language not in ["en", "ru"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid language. Supported: en, ru"
            )
        
        profile_adapter = get_profile_adapter()
        success = await profile_adapter.set_language(user_id, language)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to set language"
            )
        
        return {
            "message": "Language updated successfully",
            "language": language
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error setting language: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set language"
        )


@router.delete("/profile")
async def delete_profile(user_data: dict = Depends(require_authenticated)):
    """
    Delete user profile (GDPR compliance).
    
    Returns:
        Success message
    """
    try:
        user_id = user_data.get("user_id")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found"
            )
        
        logger.warning(f"🗑️  Profile deletion request for user {user_id}")
        
        profile_adapter = get_profile_adapter()
        success = await profile_adapter.delete_profile(user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete profile"
            )
        
        return {
            "message": "Profile deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete profile"
        )
