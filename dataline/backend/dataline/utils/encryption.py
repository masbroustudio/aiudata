import os
from pathlib import Path
from cryptography.fernet import Fernet

# Store secret key alongside the database in the persistent volume
# Use SQLITE_PATH env var to determine the data directory, fallback to USER_DATA_DIR
_SQLITE_PATH = os.environ.get("SQLITE_PATH")
if _SQLITE_PATH:
    SECRET_KEY_DIR = Path(_SQLITE_PATH).parent
else:
    from dataline.config import USER_DATA_DIR
    SECRET_KEY_DIR = Path(USER_DATA_DIR)

SECRET_KEY_PATH = SECRET_KEY_DIR / ".secret_key"

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
