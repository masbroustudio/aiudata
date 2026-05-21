import os
from pathlib import Path
from cryptography.fernet import Fernet
from dataline.config import USER_DATA_DIR

SECRET_KEY_PATH = Path(USER_DATA_DIR) / ".secret_key"

def _get_or_create_key() -> bytes:
    if SECRET_KEY_PATH.exists():
        return SECRET_KEY_PATH.read_bytes()
    
    # Ensure directory exists
    SECRET_KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    key = Fernet.generate_key()
    SECRET_KEY_PATH.write_bytes(key)
    return key

_KEY = _get_or_create_key()
_FERNET = Fernet(_KEY)

def encrypt(data: str | None) -> str | None:
    if not data:
        return data
    return _FERNET.encrypt(data.encode()).decode()

def decrypt(data: str | None) -> str | None:
    if not data:
        return data
    try:
        return _FERNET.decrypt(data.encode()).decode()
    except Exception:
        # Fallback to plain text during migration or if it's not encrypted
        return data
