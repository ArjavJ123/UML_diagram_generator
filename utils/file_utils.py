# utils/file_utils.py

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


def ensure_directory_exists(directory_path: str) -> None:
    """Create directory if it doesn't exist"""
    Path(directory_path).mkdir(parents=True, exist_ok=True)


def load_json(file_path: str) -> Optional[Dict[str, Any]]:
    """Load JSON file"""
    if not os.path.exists(file_path):
        return None
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data: Dict[str, Any], file_path: str) -> None:
    """Save JSON file"""
    directory = os.path.dirname(file_path)
    if directory:
        ensure_directory_exists(directory)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_file(file_path: str) -> Optional[str]:
    """Load text file"""
    if not os.path.exists(file_path):
        return None
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def save_file(content: str, file_path: str) -> None:
    """Save text file"""
    directory = os.path.dirname(file_path)
    if directory:
        ensure_directory_exists(directory)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def save_png_file(source_path: str, destination_path: str) -> None:
    """
    Move/rename generated PNG file to desired location

    Args:
        source_path: Path where PlantUML generated PNG
        destination_path: Final desired path
    """
    directory = os.path.dirname(destination_path)
    if directory:
        ensure_directory_exists(directory)

    # Move (rename) file
    os.replace(source_path, destination_path)
