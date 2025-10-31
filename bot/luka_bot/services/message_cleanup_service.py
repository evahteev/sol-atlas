"""
Message cleanup service for task-related messages.
Tracks and auto-deletes messages when tasks complete.
"""
import asyncio
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from aiogram import Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from loguru import logger


@dataclass
class TrackedMessage:
    """Info about tracked message"""
    message_id: int
    chat_id: int
    message_type: str  # "task_content", "action_buttons", "dialog_prompt", "file_upload_prompt"
    original_content: Optional[str] = None


@dataclass
class TaskMessageTracking:
    """Tracking info for a task"""
    messages: List[TrackedMessage] = field(default_factory=list)
    task_id: str = ""
    created_at: float = 0.0


class MessageCleanupService:
    """Service for tracking and cleaning up task messages"""
    
    _instance: Optional['MessageCleanupService'] = None
    
    @classmethod
    def get_instance(cls) -> 'MessageCleanupService':
        """Get singleton"""
        if cls._instance is None:
            cls._instance = cls()
            logger.debug("✅ MessageCleanupService singleton created")
        return cls._instance
    
    async def track_task_message(
        self,
        task_id: str,
        message: Message,
        state: FSMContext,
        message_type: str = "task_content",
        original_content: Optional[str] = None
    ) -> None:
        """Track a task-related message for later deletion"""
        try:
            data = await state.get_data()
            tracked = data.get("tracked_task_messages", {})
            
            if task_id not in tracked:
                tracked[task_id] = {
                    "messages": [],
                    "task_id": task_id,
                    "created_at": message.date.timestamp() if message.date else 0.0
                }
            
            tracked[task_id]["messages"].append({
                "message_id": message.message_id,
                "chat_id": message.chat.id,
                "message_type": message_type,
                "original_content": original_content or message.text or message.caption
            })
            
            await state.update_data({"tracked_task_messages": tracked})
            logger.debug(f"📝 Tracking message {message.message_id} for task {task_id} (type: {message_type})")
        
        except Exception as e:
            logger.error(f"❌ Failed to track message for task {task_id}: {e}")
    
    async def delete_task_messages(
        self,
        task_id: str,
        bot: Bot,
        state: FSMContext,
        delete_types: Optional[Set[str]] = None
    ) -> int:
        """Delete all tracked messages for a task"""
        try:
            data = await state.get_data()
            tracked = data.get("tracked_task_messages", {})
            
            if task_id not in tracked:
                logger.debug(f"No tracked messages found for task {task_id}")
                return 0
            
            messages = tracked[task_id].get("messages", [])
            
            # Filter by type if specified
            if delete_types:
                messages = [m for m in messages if m.get("message_type") in delete_types]
            
            # Delete messages
            deleted_count = 0
            for msg_info in messages:
                try:
                    await bot.delete_message(
                        chat_id=msg_info["chat_id"],
                        message_id=msg_info["message_id"]
                    )
                    deleted_count += 1
                    await asyncio.sleep(0.1)  # Rate limit protection
                except Exception as e:
                    logger.debug(f"Could not delete message {msg_info['message_id']}: {e}")
            
            # Remove from tracking
            del tracked[task_id]
            await state.update_data({"tracked_task_messages": tracked})
            
            logger.info(f"🗑️  Deleted {deleted_count} messages for task {task_id}")
            return deleted_count
        
        except Exception as e:
            logger.error(f"❌ Failed to delete task messages: {e}")
            return 0
    
    async def clear_all_tracked_messages(
        self,
        bot: Bot,
        state: FSMContext
    ) -> int:
        """Clear all tracked messages for user"""
        try:
            data = await state.get_data()
            tracked = data.get("tracked_task_messages", {})
            
            total_deleted = 0
            for task_id in list(tracked.keys()):
                deleted = await self.delete_task_messages(task_id, bot, state)
                total_deleted += deleted
            
            logger.info(f"🗑️  Cleared all tracked messages: {total_deleted} deleted")
            return total_deleted
        
        except Exception as e:
            logger.error(f"❌ Failed to clear all tracked messages: {e}")
            return 0


def get_message_cleanup_service() -> MessageCleanupService:
    """Get MessageCleanupService singleton"""
    return MessageCleanupService.get_instance()

