"""
MongoDB client initialization.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from src.core.config import settings

_client = None
_client_loop = None

def get_database():
    """
    Get the MongoDB database instance. Recreates the client if the event loop changes
    to prevent 'Event loop is closed' errors in tests and concurrent requests.
    """
    global _client, _client_loop
    try:
        current_loop = asyncio.get_running_loop()
    except RuntimeError:
        try:
            current_loop = asyncio.get_event_loop()
        except RuntimeError:
            current_loop = None

    if _client is None or _client_loop != current_loop:
        _client = AsyncIOMotorClient(settings.MONGO_URI)
        _client_loop = current_loop

    return _client[settings.MONGO_DB_NAME]


class DatabaseProxy:
    """A proxy wrapper around the database to resolve event loop conflicts."""
    def __getitem__(self, name):
        return get_database()[name]

    def __getattr__(self, name):
        return getattr(get_database(), name)

db = DatabaseProxy()
