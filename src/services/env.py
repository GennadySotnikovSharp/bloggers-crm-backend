import os
from dotenv import load_dotenv

_env_loaded = False

def load_env(dotenv_path: str = ".env"):
    global _env_loaded
    if not _env_loaded:
        load_dotenv(dotenv_path=dotenv_path, override=True)
        _env_loaded = True

def get_env_var(key: str, default: str = "") -> str:
    return os.getenv(key, default)
