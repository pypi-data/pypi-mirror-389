"""DialNexa Python SDK

Usage:
  from dialnexa import NexaClient
  client = NexaClient(api_key="...")
  langs = client.languages.list()
"""
from dotenv import load_dotenv
from .client import NexaClient

load_dotenv()

__all__ = [
    "NexaClient",
]
