"""Utility functions for CQTech Metrics SDK"""
import hashlib
import time
from typing import Dict, Any


def generate_checksum(username: str, secret: str, nonce: int, curtime: int) -> str:
    """
    Generate checksum for authentication using SHA1
    """
    check_sum_builder = f"{username}{secret}{nonce}{curtime}"
    return hashlib.sha1(check_sum_builder.encode()).hexdigest()


def generate_nonce() -> int:
    """
    Generate a random 10-digit number
    """
    import random
    return random.randint(1000000000, 9999999999)


def format_auth_header(access_token: str) -> Dict[str, str]:
    """
    Format the authorization header
    """
    return {"Authorization": f"Bearer {access_token}"}