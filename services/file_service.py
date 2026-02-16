"""
File Service
Handles saving uploaded user files
"""

import os
from typing import List
from pathlib import Path


def save_uploaded_files(
    uploaded_files,
    user_id: str,
    thread_id: str,
    message_id: str
) -> str:
    """
    Save uploaded files to:
    data/user_files/{user_id}/{thread_id}/{message_id}/
    
    Returns:
        directory_path
    """

    base_dir = f"data/user_files/{user_id}/{thread_id}/{message_id}"
    Path(base_dir).mkdir(parents=True, exist_ok=True)

    for file in uploaded_files:
        file_path = os.path.join(base_dir, file.name)

        with open(file_path, "wb") as f:
            f.write(file.getbuffer())

    return base_dir
