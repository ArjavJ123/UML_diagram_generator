"""
Data classes for state management and node abstraction
"""
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Optional, Any


class DiagramType(Enum):
    """
    Supported UML diagram types
    """
    CLASS = "class"
    SEQUENCE = "sequence"
    COMPONENT = "component"
    ACTIVITY = "activity"
    STATE = "state"
    USECASE = "usecase"
    DEPLOYMENT = "deployment"
    PACKAGE = "package"
    OBJECT = "object"
    TIMING = "timing"


class DiagramState:
    """
    Holds all paths and operations for a single diagram
    """
    
    def __init__(
        self,
        diagram_type: DiagramType,
        context_file_path: Optional[str] = None,
        plantuml_code_file_path: Optional[str] = None,
        diagram_png_file_path: Optional[str] = None,
        context_operations: Optional[List[Dict[str, Any]]] = None,
        code_operations: Optional[List[Dict[str, Any]]] = None,
        version: Optional[int] = None
    ):
        self.diagram_type = diagram_type
        self.context_file_path = context_file_path
        self.plantuml_code_file_path = plantuml_code_file_path
        self.diagram_png_file_path = diagram_png_file_path
        self.version = version or 1
        
        # Store operations for incremental updates
        self.context_operations = context_operations or []  # Operations from Node 2
        self.code_operations = code_operations or []  # Operations from Node 3
    
    def add_context_operations(self, operations: List[Dict[str, Any]]) -> None:
        """Add context operations from Node 2"""
        self.context_operations = operations
    
    def add_code_operations(self, operations: List[Dict[str, Any]]) -> None:
        """Add code operations from Node 3"""
        self.code_operations = operations
    
    def __repr__(self):
        return (f"DiagramState(type={self.diagram_type.value}, "
                f"context={self.context_file_path}, "
                f"context_ops={len(self.context_operations)}, "
                f"code_ops={len(self.code_operations)}, "
                f"version={self.version})")


class State:
    """
    Holds references and metadata for diagram generation
    Does NOT store file contents - only paths
    Contents are read on-demand using paths
    """
    
    def __init__(
        self,
        user_id: str,
        thread_id: str,
        message_id: str,
        prompt: str,
        parent_message_id: Optional[str] = None,
        supporting_file_directory_path: Optional[str] = None,
        diagram_types: Optional[List[DiagramType]] = None
    ):
        # User context
        self.user_id = user_id
        self.thread_id = thread_id
        self.message_id = message_id
        self.parent_message_id = parent_message_id
        
        # Input
        self.prompt = prompt
        self.supporting_file_directory_path = supporting_file_directory_path
        self.diagram_types = diagram_types  # None means auto-detect
        
        # Parsed file contents: {file_path: content}
        self.parsed_files: Dict[str, str] = {}
        
        # Diagram states: {diagram_type.value: DiagramState}
        self.diagram_states: Dict[str, DiagramState] = {}
    
    def add_parsed_file(self, file_path: str, content: str) -> None:
        """Add parsed file content"""
        self.parsed_files[file_path] = content
    
    def get_parsed_file(self, file_path: str) -> Optional[str]:
        """Get parsed file content"""
        return self.parsed_files.get(file_path)
    
    def add_diagram_state(self, diagram_state: DiagramState) -> None:
        """Add or update diagram state"""
        self.diagram_states[diagram_state.diagram_type.value] = diagram_state
    
    def get_diagram_state(self, diagram_type: DiagramType) -> Optional[DiagramState]:
        """Get diagram state by type"""
        return self.diagram_states.get(diagram_type.value)
    
    def is_update_flow(self) -> bool:
        """Check if this is an update flow"""
        return self.parent_message_id is not None
    
    def __repr__(self):
        return (f"State(user_id={self.user_id}, thread_id={self.thread_id}, "
                f"message_id={self.message_id}, diagrams={len(self.diagram_states)})")


class Node(ABC):
    """Abstract base class for all processing nodes"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def create_user_prompt(self, state: State) -> str:
        """Generate user message from state"""
        pass
    
    @abstractmethod
    def call_llm(self, prompt: str) -> str:
        """Call LLM with prompt"""
        pass
    
    @abstractmethod
    def execute(self, state: State) -> State:
        """Execute node and update state"""
        pass