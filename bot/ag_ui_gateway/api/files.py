"""
File Upload API Endpoints

Handles file uploads to S3/R2 storage for tasks and chat.
"""
from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, status, Form
from typing import Optional
import uuid
import asyncio
from pathlib import Path
from loguru import logger

from ag_ui_gateway.auth.permissions import require_authenticated
from ag_ui_gateway.config.settings import settings
from luka_bot.services.s3_upload_service import get_s3_upload_service

router = APIRouter()


@router.post("/files/upload")
async def upload_file(
    file: UploadFile = File(...),
    task_id: Optional[str] = Form(None),
    variable_name: Optional[str] = Form("file"),
    user_data: dict = Depends(require_authenticated)
):
    """
    Upload file to S3/R2 storage.
    
    Args:
        file: File to upload
        task_id: Optional task ID (for organizing files)
        variable_name: Optional variable name (for Camunda forms)
        user_data: Authenticated user data
    
    Returns:
        File metadata with public URL
    """
    try:
        user_id = user_data.get("user_id")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found"
            )
        
        # Validate file size
        if settings.MAX_FILE_SIZE_MB:
            max_size_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
            file.file.seek(0, 2)  # Seek to end
            file_size = file.file.tell()
            file.file.seek(0)  # Reset to start
            
            if file_size > max_size_bytes:
                size_mb = file_size / (1024 * 1024)
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File too large: {size_mb:.1f}MB. Maximum: {settings.MAX_FILE_SIZE_MB}MB"
                )
        
        # Validate file type (if configured)
        if settings.ALLOWED_FILE_TYPES and file.content_type not in settings.ALLOWED_FILE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"File type not allowed: {file.content_type}"
            )
        
        logger.info(f"📤 File upload request: {file.filename} ({file.content_type}), user={user_id}")
        
        # Get S3 service
        s3_service = get_s3_upload_service()
        
        # Generate unique filename
        file_uuid = str(uuid.uuid4())
        original_extension = Path(file.filename).suffix
        unique_filename = f"{file_uuid}{original_extension}"
        
        # Generate S3 key with organized structure
        if task_id:
            s3_key = f"tasks/{user_id}/{task_id}/{variable_name}/{unique_filename}"
        else:
            s3_key = f"uploads/{user_id}/{unique_filename}"
        
        # Save to temp file
        temp_path = f"/tmp/{unique_filename}"
        with open(temp_path, "wb") as temp_file:
            content = await file.read()
            temp_file.write(content)
        
        file_size = len(content)
        
        logger.debug(f"📝 File mapping: {file.filename} → {s3_key}")
        
        # Upload to S3 (async wrapper)
        await asyncio.get_event_loop().run_in_executor(
            None,
            s3_service._sync_upload,
            temp_path,
            s3_key,
            file.content_type or "application/octet-stream"
        )
        
        # Clean up temp file
        Path(temp_path).unlink(missing_ok=True)
        
        # Generate public URL
        public_url = f"{s3_service.public_url}/{s3_key}"
        
        logger.info(f"✅ File uploaded: {public_url}")
        
        return {
            "file_url": public_url,
            "file_name": file.filename,
            "file_size": file_size,
            "mime_type": file.content_type,
            "file_uuid": file_uuid,
            "s3_key": s3_key,
            "uploaded_at": None  # Could add timestamp
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ File upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File upload failed: {str(e)}"
        )


@router.get("/files/{file_uuid}")
async def get_file_info(
    file_uuid: str,
    user_data: dict = Depends(require_authenticated)
):
    """
    Get file metadata by UUID.
    
    Args:
        file_uuid: File UUID
        user_data: Authenticated user data
    
    Returns:
        File metadata
    """
    try:
        # In a real implementation, you would query a database
        # for file metadata by UUID
        # For now, return a placeholder
        
        logger.info(f"📖 File info request: {file_uuid}")
        
        return {
            "file_uuid": file_uuid,
            "message": "File metadata retrieval not yet implemented"
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting file info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve file info"
        )


@router.delete("/files/{file_uuid}")
async def delete_file(
    file_uuid: str,
    user_data: dict = Depends(require_authenticated)
):
    """
    Delete file by UUID (owner only).
    
    Args:
        file_uuid: File UUID
        user_data: Authenticated user data
    
    Returns:
        Success message
    """
    try:
        user_id = user_data.get("user_id")
        
        logger.warning(f"🗑️  File deletion request: {file_uuid}, user={user_id}")
        
        # In a real implementation, you would:
        # 1. Query database for file metadata
        # 2. Check ownership
        # 3. Delete from S3
        # 4. Delete from database
        
        return {
            "message": "File deletion not yet fully implemented",
            "file_uuid": file_uuid
        }
        
    except Exception as e:
        logger.error(f"❌ Error deleting file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete file"
        )
