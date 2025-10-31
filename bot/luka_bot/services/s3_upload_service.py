"""
S3-compatible file upload service for various providers.
Supports: Cloudflare R2, Selectel, AWS S3, and other S3-compatible storage.
Handles Telegram file uploads with SSL certificate support.
"""
import boto3
import asyncio
import uuid
from typing import Optional
from pathlib import Path
from datetime import datetime
from aiogram.types import Document, Message
from loguru import logger

from luka_bot.core.config import settings


class S3UploadService:
    """Service for uploading files to S3-compatible storage"""
    
    _instance: Optional['S3UploadService'] = None
    
    def __init__(self):
        # Build boto3 client config
        client_config = {
            'aws_access_key_id': settings.S3_ACCESS_KEY_ID,
            'aws_secret_access_key': settings.S3_SECRET_ACCESS_KEY,
            'region_name': settings.S3_REGION,
        }
        
        # Add custom endpoint URL for non-AWS S3 (R2, Selectel, MinIO, etc.)
        # Leave empty for standard AWS S3
        if settings.S3_ENDPOINT_URL:
            client_config['endpoint_url'] = settings.S3_ENDPOINT_URL
            logger.info(f"🌐 Using custom S3 endpoint: {settings.S3_ENDPOINT_URL}")
        else:
            logger.info(f"☁️  Using standard AWS S3 (region: {settings.S3_REGION})")
        
        # Add SSL certificate verification if provided (for custom S3 providers)
        if settings.S3_CA_CERT_PATH:
            cert_path = Path(settings.S3_CA_CERT_PATH)
            if cert_path.exists():
                client_config['verify'] = str(cert_path.absolute())
                logger.info(f"🔒 Using SSL certificate: {cert_path}")
            else:
                logger.warning(f"⚠️  SSL certificate not found: {cert_path}, using system CA bundle")
        
        # Create S3 client with 's3' as service name (first positional argument)
        self.s3_client = boto3.client('s3', **client_config)
        self.bucket_name = settings.S3_BUCKET_NAME
        self.public_url = settings.S3_PUBLIC_URL
    
    @classmethod
    def get_instance(cls) -> 'S3UploadService':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
            logger.info("✅ S3UploadService singleton created")
        return cls._instance
    
    async def upload_telegram_file(
        self,
        message: Message,
        document: Document,
        task_id: str,
        user_id: int,
        variable_name: str
    ) -> str:
        """
        Upload Telegram document to S3-compatible storage and return public URL.
        
        File naming strategy:
        - Generates unique UUID for filename to prevent collisions
        - Preserves original file extension for proper MIME type handling
        - Format: tasks/{user_id}/{task_id}/{variable_name}/{uuid}.{ext}
        
        Args:
            message: Telegram message containing the document
            document: Document object from Telegram
            task_id: Camunda task ID (for organizing files)
            user_id: Telegram user ID
            variable_name: Variable name (e.g., "s3_chatHistory")
            
        Returns:
            Public URL of uploaded file (can be used for future downloads)
            
        Raises:
            ValueError: If file size exceeds Telegram Bot API limit (20MB)
        """
        try:
            # Check file size limit (Telegram Bot API limitation)
            MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB in bytes
            
            if document.file_size and document.file_size > MAX_FILE_SIZE:
                size_mb = document.file_size / (1024 * 1024)
                raise ValueError(
                    f"file_too_large:{size_mb:.1f}"  # Format for parsing in handler
                )
            
            # Download file from Telegram
            file = await message.bot.get_file(document.file_id)
            temp_path = f"/tmp/{user_id}_{task_id}_{document.file_name}"
            await message.bot.download_file(file.file_path, temp_path)
            
            logger.info(f"📥 Downloaded file from Telegram: {document.file_name} ({document.file_size} bytes)")
            
            # Generate unique filename with UUID
            file_uuid = str(uuid.uuid4())
            original_extension = Path(document.file_name).suffix  # Preserves .json, .txt, .zip, etc.
            unique_filename = f"{file_uuid}{original_extension}"
            
            # Generate S3 key with organized folder structure
            s3_key = f"tasks/{user_id}/{task_id}/{variable_name}/{unique_filename}"
            
            logger.debug(
                f"📝 File mapping:\n"
                f"   Original: {document.file_name}\n"
                f"   UUID: {file_uuid}\n"
                f"   S3 Key: {s3_key}"
            )
            
            # Upload to S3 (async wrapper)
            await asyncio.get_event_loop().run_in_executor(
                None,
                self._sync_upload,
                temp_path,
                s3_key,
                document.mime_type
            )
            
            # Clean up temp file
            Path(temp_path).unlink(missing_ok=True)
            logger.debug(f"🗑️  Cleaned up temp file: {temp_path}")
            
            # Return public URL (this will be stored in Camunda variable)
            public_url = f"{self.public_url}/{s3_key}"
            logger.info(f"✅ Uploaded file to S3: {public_url}")
            logger.info(f"   File UUID: {file_uuid} (stored for tracking)")
            return public_url
        
        except Exception as e:
            logger.error(f"❌ Failed to upload file to S3: {e}")
            raise
    
    def _sync_upload(self, local_path: str, s3_key: str, content_type: str):
        """Synchronous upload for executor"""
        try:
            self.s3_client.upload_file(
                local_path,
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    'ContentType': content_type,
                    'ACL': 'public-read'  # Or use signed URLs for private files
                }
            )
            logger.debug(f"📤 S3 upload complete: {s3_key}")
        except Exception as e:
            logger.error(f"❌ S3 upload failed for {s3_key}: {e}")
            raise


def get_s3_upload_service() -> S3UploadService:
    """Get S3UploadService singleton"""
    return S3UploadService.get_instance()

