"""
UUID utilities for generating clean UUIDs without hyphens.
"""
import uuid
from typing import Optional


class UUIDUtils:
    """Utility class for UUID operations."""
    
    @staticmethod
    def generate_clean_uuid() -> str:
        """
        Generate UUID without hyphens (32 characters).
        
        Returns:
            Clean UUID string without hyphens
        """
        return str(uuid.uuid4()).replace("-", "")
    
    @staticmethod
    def clean_uuid(uuid_str: str) -> str:
        """
        Remove hyphens from existing UUID string.
        
        Args:
            uuid_str: UUID string with or without hyphens
            
        Returns:
            Clean UUID string without hyphens
        """
        return uuid_str.replace("-", "")
    
    @staticmethod
    def is_valid_uuid(uuid_str: str) -> bool:
        """
        Check if string is a valid UUID (with or without hyphens).
        
        Args:
            uuid_str: String to validate
            
        Returns:
            True if valid UUID, False otherwise
        """
        try:
            # Try parsing with hyphens first
            uuid.UUID(uuid_str)
            return True
        except ValueError:
            try:
                # Try parsing without hyphens
                uuid.UUID(uuid_str.replace("-", ""))
                return True
            except ValueError:
                return False
