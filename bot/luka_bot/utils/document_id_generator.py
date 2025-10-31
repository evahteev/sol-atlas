"""
Document ID generator for Elasticsearch and Camunda correlation.
Generates consistent document IDs that can be used across both systems.
"""
from typing import Optional


class DocumentIDGenerator:
    """Generate consistent document IDs for cross-system correlation."""
    
    @staticmethod
    def generate_group_message_id(
        user_id: int,
        group_id: int,
        telegram_message_id: int,
        thread_id: Optional[str] = None
    ) -> str:
        """
        Generate document ID for group user messages.
        
        Format: group_{user_id}_{group_id}_{thread_id}_{telegram_message_id}
        Example: group_922705_1001234567890_456_42
        
        Args:
            user_id: Telegram user ID
            group_id: Telegram group ID
            telegram_message_id: Telegram message ID
            thread_id: Optional thread ID for supergroup topics
            
        Returns:
            Document ID string
        """
        if thread_id:
            return f"group_{abs(user_id)}_{group_id}_{thread_id}_{telegram_message_id}"
        else:
            return f"group_{abs(user_id)}_{group_id}_{telegram_message_id}"
    
    @staticmethod
    def generate_group_assistant_id(
        group_id: int,
        telegram_message_id: int,
        thread_id: Optional[str] = None
    ) -> str:
        """
        Generate document ID for group assistant messages.
        
        Format: group_assistant_{group_id}_{thread_id}_{telegram_message_id}
        Example: group_assistant_1001234567890_456_42
        
        Args:
            group_id: Telegram group ID
            telegram_message_id: Telegram message ID
            thread_id: Optional thread ID for supergroup topics
            
        Returns:
            Document ID string
        """
        if thread_id:
            return f"group_assistant_{group_id}_{thread_id}_{telegram_message_id}"
        else:
            return f"group_assistant_{group_id}_{telegram_message_id}"
    
    @staticmethod
    def generate_dm_message_id(
        user_id: int,
        thread_id: str,
        telegram_message_id: int
    ) -> str:
        """
        Generate document ID for DM user messages.
        
        Format: dm_{user_id}_{thread_id}_{telegram_message_id}
        Example: dm_922705_550e8400e29b41d4a716446655440000_123
        
        Args:
            user_id: Telegram user ID
            thread_id: Thread UUID (without hyphens)
            telegram_message_id: Telegram message ID
            
        Returns:
            Document ID string
        """
        return f"dm_{abs(user_id)}_{thread_id}_{telegram_message_id}"
    
    @staticmethod
    def generate_dm_assistant_id(
        thread_id: str,
        telegram_message_id: int
    ) -> str:
        """
        Generate document ID for DM assistant messages.
        
        Format: dm_assistant_{thread_id}_{telegram_message_id}
        Example: dm_assistant_550e8400e29b41d4a716446655440000_123
        
        Args:
            thread_id: Thread UUID (without hyphens)
            telegram_message_id: Telegram message ID
            
        Returns:
            Document ID string
        """
        return f"dm_assistant_{thread_id}_{telegram_message_id}"
    
    @staticmethod
    def parse_document_id(document_id: str) -> dict:
        """
        Parse document ID to extract components.
        
        Args:
            document_id: Document ID to parse
            
        Returns:
            Dict with parsed components
        """
        parts = document_id.split("_")
        
        if document_id.startswith("group_"):
            if parts[1] == "assistant":
                # group_assistant_{group_id}_{thread_id}_{message_id} or group_assistant_{group_id}_{message_id}
                if len(parts) == 4:
                    return {
                        "type": "group",
                        "role": "assistant",
                        "group_id": int(parts[2]),
                        "telegram_message_id": int(parts[3])
                    }
                else:
                    return {
                        "type": "group",
                        "role": "assistant",
                        "group_id": int(parts[2]),
                        "thread_id": parts[3],
                        "telegram_message_id": int(parts[4])
                    }
            else:
                # group_{user_id}_{group_id}_{thread_id}_{message_id} or group_{user_id}_{group_id}_{message_id}
                if len(parts) == 4:
                    return {
                        "type": "group",
                        "role": "user",
                        "user_id": int(parts[1]),
                        "group_id": int(parts[2]),
                        "telegram_message_id": int(parts[3])
                    }
                else:
                    return {
                        "type": "group",
                        "role": "user",
                        "user_id": int(parts[1]),
                        "group_id": int(parts[2]),
                        "thread_id": parts[3],
                        "telegram_message_id": int(parts[4])
                    }
        elif document_id.startswith("dm_"):
            if parts[1] == "assistant":
                # dm_assistant_{thread_id}_{message_id}
                return {
                    "type": "dm",
                    "role": "assistant",
                    "thread_id": parts[2],
                    "telegram_message_id": int(parts[3])
                }
            else:
                # dm_{user_id}_{thread_id}_{message_id}
                return {
                    "type": "dm",
                    "role": "user",
                    "user_id": int(parts[1]),
                    "thread_id": parts[2],
                    "telegram_message_id": int(parts[3])
                }
        else:
            return {"type": "unknown", "raw_id": document_id}
