"""
Thread Service
Handles thread creation and retrieval
"""

import uuid
from typing import List

from utils.db_utils import get_thread_messages


def create_thread_id(user_id: str) -> str:
    """
    Create a new thread id
    """
    return f"thread_{uuid.uuid4().hex[:6]}"


def get_thread_history(thread_id: str) -> List[dict]:
    """
    Get all messages in a thread
    """
    return get_thread_messages(thread_id)


def thread_exists(thread_id: str) -> bool:
    """
    Check if thread has any messages
    """
    messages = get_thread_messages(thread_id)
    return len(messages) > 0
