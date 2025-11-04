"""Tests for CQTech Metrics SDK"""

# Try to load environment variables from .env file
try:
    print("Loading environment variables from .env file")
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv is optional, so if it's not installed, just continue
    pass