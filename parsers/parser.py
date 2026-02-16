"""
Combined parser - routes to appropriate parser based on file extension
"""
import os
from typing import Dict, List

from parsers.txt_parser import parse_txt
from parsers.pdf_parser import parse_pdf

def parse_files(directory_path: str) -> Dict[str, str]:
    """
    Parse all supported files in a directory
    """

    if not os.path.exists(directory_path):
        raise FileNotFoundError(f"Directory not found: {directory_path}")

    parsed_files = {}

    for root, _, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(root, file)

            _, extension = os.path.splitext(file_path)
            extension = extension.lower()

            try:
                if extension == '.txt':
                    content = parse_txt(file_path)
                    parsed_files[file_path] = content

                elif extension == '.pdf':
                    content = parse_pdf(file_path)
                    parsed_files[file_path] = content

                else:
                    print(f"Skipping unsupported file: {file_path}")

            except Exception as e:
                print(f"Error parsing {file_path}: {e}")
                parsed_files[file_path] = f"[Error parsing file: {str(e)}]"

    return parsed_files
