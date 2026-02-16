"""
Database utilities for JSON-based storage
Manages messages.json and diagrams.json
"""
import json
import os
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path

from utils.constants import DB_DIR, MESSAGES_DB, DIAGRAMS_DB


def _ensure_db_dir():
    """Ensure database directory exists"""
    Path(DB_DIR).mkdir(parents=True, exist_ok=True)


def _initialize_db():
    """Initialize database files if they don't exist"""
    _ensure_db_dir()
    
    if not os.path.exists(MESSAGES_DB):
        with open(MESSAGES_DB, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=2)
    
    if not os.path.exists(DIAGRAMS_DB):
        with open(DIAGRAMS_DB, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=2)


def _load_messages() -> List[Dict[str, Any]]:
    """Load all messages from database"""
    _initialize_db()
    
    with open(MESSAGES_DB, 'r', encoding='utf-8') as f:
        return json.load(f)


def _save_messages(messages: List[Dict[str, Any]]) -> None:
    """Save all messages to database"""
    _ensure_db_dir()
    
    with open(MESSAGES_DB, 'w', encoding='utf-8') as f:
        json.dump(messages, f, indent=2, ensure_ascii=False)


def _load_diagrams() -> List[Dict[str, Any]]:
    """Load all diagrams from database"""
    _initialize_db()
    
    with open(DIAGRAMS_DB, 'r', encoding='utf-8') as f:
        return json.load(f)


def _save_diagrams(diagrams: List[Dict[str, Any]]) -> None:
    """Save all diagrams to database"""
    _ensure_db_dir()
    
    with open(DIAGRAMS_DB, 'w', encoding='utf-8') as f:
        json.dump(diagrams, f, indent=2, ensure_ascii=False)


# ===== MESSAGE OPERATIONS =====

def add_message(
    user_id: str,
    thread_id: str,
    message_id: str,
    prompt: str,
    parent_message_id: Optional[str] = None,
    user_files_directory_path: Optional[str] = None,
    diagram_ids: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Add a new message to the database
    
    Args:
        user_id: User identifier
        thread_id: Thread identifier
        message_id: Message identifier
        prompt: User's prompt
        parent_message_id: Parent message ID (for updates)
        user_files_directory_path: Path to uploaded files directory
        diagram_ids: List of diagram IDs generated
        
    Returns:
        The created message record
    """
    messages = _load_messages()
    
    message_record = {
        "user_id": user_id,
        "thread_id": thread_id,
        "message_id": message_id,
        "parent_message_id": parent_message_id,
        "prompt": prompt,
        "user_files_directory_path": user_files_directory_path,
        "diagram_ids": diagram_ids or [],
        "created_timestamp": datetime.now().isoformat(),
        "completed_timestamp": None
    }
    
    messages.append(message_record)
    _save_messages(messages)
    
    return message_record


def get_message(message_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a message by ID
    
    Args:
        message_id: Message identifier
        
    Returns:
        Message record or None if not found
    """
    messages = _load_messages()
    
    for message in messages:
        if message["message_id"] == message_id:
            return message
    
    return None


def update_message(
    message_id: str,
    diagram_ids: Optional[List[str]] = None,
    completed_timestamp: Optional[str] = None
) -> bool:
    """
    Update a message record
    
    Args:
        message_id: Message identifier
        diagram_ids: Updated list of diagram IDs
        completed_timestamp: Completion timestamp
        
    Returns:
        True if updated, False if not found
    """
    messages = _load_messages()
    
    for message in messages:
        if message["message_id"] == message_id:
            if diagram_ids is not None:
                message["diagram_ids"] = diagram_ids
            if completed_timestamp is not None:
                message["completed_timestamp"] = completed_timestamp
            
            _save_messages(messages)
            return True
    
    return False


def get_thread_messages(thread_id: str) -> List[Dict[str, Any]]:
    """
    Get all messages in a thread
    
    Args:
        thread_id: Thread identifier
        
    Returns:
        List of message records, sorted by creation time
    """
    messages = _load_messages()
    
    thread_messages = [
        msg for msg in messages 
        if msg["thread_id"] == thread_id
    ]
    
    # Sort by created_timestamp
    thread_messages.sort(key=lambda x: x["created_timestamp"])
    
    return thread_messages


# ===== DIAGRAM OPERATIONS =====

def add_diagram(
    diagram_id: str,
    user_id: str,
    thread_id: str,
    message_id: str,
    diagram_type: str,
    version: int = 1,
    parent_diagram_id: Optional[str] = None,
    context_file_path: Optional[str] = None,
    plantuml_code_file_path: Optional[str] = None,
    diagram_png_file_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Add a new diagram to the database
    
    Args:
        diagram_id: Diagram identifier
        user_id: User identifier
        thread_id: Thread identifier
        message_id: Message identifier
        diagram_type: Type of diagram (class, sequence, etc.)
        version: Version number
        parent_diagram_id: Parent diagram ID (for updates)
        context_file_path: Path to context JSON
        plantuml_code_file_path: Path to PlantUML code
        diagram_png_file_path: Path to PNG diagram
        
    Returns:
        The created diagram record
    """
    diagrams = _load_diagrams()
    
    diagram_record = {
        "diagram_id": diagram_id,
        "parent_diagram_id": parent_diagram_id,
        "version": version,
        "user_id": user_id,
        "thread_id": thread_id,
        "message_id": message_id,
        "diagram_type": diagram_type,
        "context_file_path": context_file_path,
        "plantuml_code_file_path": plantuml_code_file_path,
        "diagram_png_file_path": diagram_png_file_path,
        "created_timestamp": datetime.now().isoformat(),
        "user_feedback": None,
        "feedback_rating": None
    }
    
    diagrams.append(diagram_record)
    _save_diagrams(diagrams)
    
    return diagram_record


def get_diagram(diagram_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a diagram by ID
    
    Args:
        diagram_id: Diagram identifier
        
    Returns:
        Diagram record or None if not found
    """
    diagrams = _load_diagrams()
    
    for diagram in diagrams:
        if diagram["diagram_id"] == diagram_id:
            return diagram
    
    return None


def get_latest_diagram(
    user_id: str,
    thread_id: str,
    diagram_type: str
) -> Optional[Dict[str, Any]]:
    """
    Get the latest version of a diagram for a user/thread/type
    
    Args:
        user_id: User identifier
        thread_id: Thread identifier
        diagram_type: Type of diagram
        
    Returns:
        Latest diagram record or None if not found
    """
    diagrams = _load_diagrams()
    
    # Filter by user, thread, and type
    matching_diagrams = [
        d for d in diagrams
        if d["user_id"] == user_id
        and d["thread_id"] == thread_id
        and d["diagram_type"] == diagram_type
    ]
    
    if not matching_diagrams:
        return None
    
    # Sort by version descending and get the latest
    matching_diagrams.sort(key=lambda x: x["version"], reverse=True)
    
    return matching_diagrams[0]


def get_diagram_versions(
    user_id: str,
    thread_id: str,
    diagram_type: str
) -> List[Dict[str, Any]]:
    """
    Get all versions of a diagram
    
    Args:
        user_id: User identifier
        thread_id: Thread identifier
        diagram_type: Type of diagram
        
    Returns:
        List of diagram records, sorted by version
    """
    diagrams = _load_diagrams()
    
    matching_diagrams = [
        d for d in diagrams
        if d["user_id"] == user_id
        and d["thread_id"] == thread_id
        and d["diagram_type"] == diagram_type
    ]
    
    # Sort by version ascending
    matching_diagrams.sort(key=lambda x: x["version"])
    
    return matching_diagrams


def update_diagram_feedback(
    diagram_id: str,
    user_feedback: str,
    feedback_rating: int
) -> bool:
    """
    Update diagram with user feedback
    
    Args:
        diagram_id: Diagram identifier
        user_feedback: User's feedback text
        feedback_rating: Rating (1-5)
        
    Returns:
        True if updated, False if not found
    """
    diagrams = _load_diagrams()
    
    for diagram in diagrams:
        if diagram["diagram_id"] == diagram_id:
            diagram["user_feedback"] = user_feedback
            diagram["feedback_rating"] = feedback_rating
            
            _save_diagrams(diagrams)
            return True
    
    return False


# ===== COMMON UPDATE OPERATIONS =====

def update_after_run(
    message_id: str,
    diagram_records: List[Dict[str, Any]]
) -> bool:
    """
    Common function to update database after a complete run
    Updates message with diagram IDs and completion timestamp
    
    Args:
        message_id: Message identifier
        diagram_records: List of diagram records to add
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Add all diagrams
        diagram_ids = []
        for diagram_record in diagram_records:
            add_diagram(**diagram_record)
            diagram_ids.append(diagram_record["diagram_id"])
        
        # Update message
        update_message(
            message_id=message_id,
            diagram_ids=diagram_ids,
            completed_timestamp=datetime.now().isoformat()
        )
        
        return True
    
    except Exception as e:
        print(f"Error updating database after run: {e}")
        return False


# ===== UTILITY FUNCTIONS =====

def thread_exists(thread_id: str) -> bool:
    """
    Check if a thread exists
    
    Args:
        thread_id: Thread identifier
        
    Returns:
        True if thread exists, False otherwise
    """
    messages = _load_messages()
    
    for message in messages:
        if message["thread_id"] == thread_id:
            return True
    
    return False


def get_user_threads(user_id: str) -> List[str]:
    """
    Get all thread IDs for a user
    
    Args:
        user_id: User identifier
        
    Returns:
        List of unique thread IDs
    """
    messages = _load_messages()
    
    thread_ids = set()
    for message in messages:
        if message["user_id"] == user_id:
            thread_ids.add(message["thread_id"])
    
    return sorted(list(thread_ids))


def get_thread_diagrams(thread_id: str) -> List[Dict[str, Any]]:
    """
    Get all diagrams in a thread
    
    Args:
        thread_id: Thread identifier
        
    Returns:
        List of diagram records
    """
    diagrams = _load_diagrams()
    
    thread_diagrams = [
        d for d in diagrams
        if d["thread_id"] == thread_id
    ]
    
    # Sort by created_timestamp
    thread_diagrams.sort(key=lambda x: x["created_timestamp"])
    
    return thread_diagrams