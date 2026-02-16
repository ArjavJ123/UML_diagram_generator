"""
Constants and configuration
"""
import os
from enum import Enum


# ===== DATABASE PATHS =====
DB_DIR = "database"
MESSAGES_DB = os.path.join(DB_DIR, "messages.json")
DIAGRAMS_DB = os.path.join(DB_DIR, "diagrams.json")


# ===== DATA DIRECTORIES =====
DATA_DIR = "data"
USER_FILES_DIR = os.path.join(DATA_DIR, "user_files")
CONTEXT_DIR = os.path.join(DATA_DIR, "context")
PLANTUML_CODE_DIR = os.path.join(DATA_DIR, "plantuml_code")
DIAGRAMS_DIR = os.path.join(DATA_DIR, "diagrams")

# ===== LLM CONFIGURATION =====
GEMINI_MODEL = "gemini-2.5-pro"  
OPENAI_MODEL = "gpt-5"  # Alternative LLM

# ===== Plant UML path=====
PLANTUML_JAR_PATH = "/Users/arjavjain/plantuml.jar"  # Update this path to your PlantUML jar file