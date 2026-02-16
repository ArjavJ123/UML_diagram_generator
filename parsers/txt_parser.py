"""
Text file parser
"""
from typing import Optional


def parse_txt(file_path: str) -> str:
    """
    Parse a text file and return its content
    
    Args:
        file_path: Path to the .txt file
        
    Returns:
        Text content as string
        
    Raises:
        FileNotFoundError: If file doesn't exist
        UnicodeDecodeError: If file encoding is not supported
    """
    try:
        # Try UTF-8 first
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        # Fallback to latin-1
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()
        except Exception as e:
            raise UnicodeDecodeError(
                f"Failed to decode file {file_path} with UTF-8 or latin-1",
                b'', 0, 1, str(e)
            )