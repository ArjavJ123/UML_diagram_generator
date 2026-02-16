"""
Diagram Service
Handles diagram retrieval and feedback
"""

from typing import List, Dict

from utils.db_utils import (
    get_thread_diagrams,
    update_diagram_feedback
)


def get_diagrams_for_thread(thread_id: str) -> List[Dict]:
    """
    Get all diagrams for a thread
    """
    return get_thread_diagrams(thread_id)


def add_feedback(
    diagram_id: str,
    feedback: str,
    rating: int
) -> bool:
    """
    Add feedback to a diagram
    """
    return update_diagram_feedback(
        diagram_id=diagram_id,
        user_feedback=feedback,
        feedback_rating=rating
    )
