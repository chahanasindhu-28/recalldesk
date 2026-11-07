import os
import re
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


def get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    value = os.getenv(name, default)
    return value.strip() if isinstance(value, str) and value.strip() else default


def validate_customer_id(customer_id: str) -> str:
    if not customer_id:
        raise ValueError("Customer ID is required.")
    if not re.fullmatch(r"[A-Za-z0-9_-]{3,64}", customer_id):
        raise ValueError("Customer ID contains invalid characters.")
    return customer_id


def get_settings() -> dict:
    return {
        "groq_api_key": get_env("GROQ_API_KEY"),
        "groq_model": get_env("GROQ_MODEL", "openai/gpt-oss-20b"),
        "hindsight_api_key": get_env("HINDSIGHT_API_KEY"),
        "hindsight_base_url": get_env("HINDSIGHT_BASE_URL"),
        "hindsight_bank_id": get_env("HINDSIGHT_BANK_ID"),
    }
