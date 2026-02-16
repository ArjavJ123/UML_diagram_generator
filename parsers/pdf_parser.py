"""
PDF file parser - converts PDF to markdown
Handles text, tables, and basic formatting
"""
import pdfplumber
from typing import List, Dict, Any


def _table_to_markdown(table: List[List[str]]) -> str:
    """
    Convert a table (list of lists) to markdown format
    
    Args:
        table: 2D list representing table data
        
    Returns:
        Markdown formatted table string
    """
    if not table or len(table) == 0:
        return ""
    
    markdown_lines = []
    
    # Header row
    header = table[0]
    markdown_lines.append("| " + " | ".join(str(cell) if cell else "" for cell in header) + " |")
    
    # Separator row
    markdown_lines.append("| " + " | ".join("---" for _ in header) + " |")
    
    # Data rows
    for row in table[1:]:
        markdown_lines.append("| " + " | ".join(str(cell) if cell else "" for cell in row) + " |")
    
    return "\n".join(markdown_lines)


def parse_pdf(file_path: str) -> str:
    """
    Parse a PDF file and convert to markdown format
    Extracts text and tables, preserves structure
    
    Args:
        file_path: Path to the .pdf file
        
    Returns:
        Markdown formatted content as string
        
    Raises:
        FileNotFoundError: If file doesn't exist
        Exception: If PDF parsing fails
    """
    markdown_content = []
    
    try:
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                # Add page marker
                markdown_content.append(f"\n## Page {page_num}\n")
                
                # Extract tables first
                tables = page.extract_tables()
                
                # Extract text
                text = page.extract_text()
                
                if text:
                    # If there are tables, we need to be careful about text extraction
                    # to avoid duplicating table content in the text
                    if tables:
                        # Add text (pdfplumber's extract_text already excludes table areas)
                        markdown_content.append(text)
                        markdown_content.append("\n")
                        
                        # Add tables
                        for table_num, table in enumerate(tables, start=1):
                            if table:
                                markdown_content.append(f"\n**Table {table_num}:**\n")
                                markdown_content.append(_table_to_markdown(table))
                                markdown_content.append("\n")
                    else:
                        # No tables, just add text
                        markdown_content.append(text)
                        markdown_content.append("\n")
        
        return "\n".join(markdown_content)
    
    except FileNotFoundError:
        raise FileNotFoundError(f"PDF file not found: {file_path}")
    except Exception as e:
        raise Exception(f"Failed to parse PDF {file_path}: {str(e)}")