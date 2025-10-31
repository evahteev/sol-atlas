"""
Telegram Mini App Authentication

Validates Telegram WebApp initData signature.
"""
import hmac
import hashlib
import json
from urllib.parse import parse_qs
from fastapi import HTTPException
from loguru import logger


def validate_telegram_webapp_data(init_data: str, bot_token: str) -> dict:
    """
    Validate Telegram Mini App initData signature.
    
    Args:
        init_data: Signed data from Telegram WebApp
        bot_token: Bot token for signature validation
    
    Returns:
        dict with user data if valid
    
    Raises:
        HTTPException: If signature invalid
    """
    try:
        # Parse query string
        parsed = parse_qs(init_data)
        
        # Extract hash
        received_hash = parsed.get('hash', [None])[0]
        if not received_hash:
            raise HTTPException(status_code=401, detail="Missing hash")
        
        # Build data check string (sorted key=value pairs, excluding hash)
        data_check_string = '\n'.join(
            f"{k}={v[0]}"
            for k, v in sorted(parsed.items())
            if k != 'hash'
        )
        
        # Compute secret key
        secret_key = hmac.new(
            key=b"WebAppData",
            msg=bot_token.encode(),
            digestmod=hashlib.sha256
        ).digest()
        
        # Compute expected hash
        expected_hash = hmac.new(
            key=secret_key,
            msg=data_check_string.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        # Verify signature (constant-time comparison)
        if not hmac.compare_digest(received_hash, expected_hash):
            logger.warning("Invalid Telegram signature")
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Parse user data
        user_data = json.loads(parsed.get('user', ['{}'])[0])
        
        return {
            'telegram_user_id': user_data.get('id'),
            'username': user_data.get('username'),
            'first_name': user_data.get('first_name'),
            'last_name': user_data.get('last_name'),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Telegram auth validation error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")
