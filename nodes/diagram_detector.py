"""
Diagram Type Detection Node
Identifies which UML diagram types are appropriate for the user's request
"""
import json
from typing import List
from pydantic import BaseModel, Field

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from utils.dataclasses import Node, State, DiagramType
from utils.prompts import DIAGRAM_DETECTION_SYSTEM_PROMPT
from utils.constants import GEMINI_MODEL, OPENAI_MODEL


# ===== PYDANTIC OUTPUT MODEL =====

class DiagramDetectionOutput(BaseModel):
    """Structured output for diagram type detection"""
    diagram_types: List[DiagramType] = Field(
        description="List of recommended UML diagram types"
    )
    confidence_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score for the recommendations (0.0 to 1.0)"
    )


# ===== NODE IMPLEMENTATION =====

class DiagramTypeDetector(Node):
    """
    Node for detecting appropriate diagram types from user request
    """
    
    def __init__(self):
        super().__init__("DiagramTypeDetector")
        self.llm = ChatOpenAI(
            model=OPENAI_MODEL,
            temperature=0
        )
        # Configure LLM for structured output
        self.llm_structured = self.llm.with_structured_output(DiagramDetectionOutput)
    
    def create_user_prompt(self, state: State) -> str:
        """
        Create user message with the actual request
        
        Args:
            state: Current state with prompt and parsed files
            
        Returns:
            User message string
        """
        user_message = f"User's Request:\n{state.prompt}\n"
        
        # Add supporting files if present
        if state.parsed_files:
            user_message += "\nSupporting Files:\n"
            for file_path, content in state.parsed_files.items():
                # Truncate long content to avoid token limits
                truncated = content[:1000] + "..." if len(content) > 1000 else content
                user_message += f"\n--- {file_path} ---\n{truncated}\n"
        
        return user_message
    
    def call_llm(self, prompt: str) -> str:
        """
        Call LLM with structured output
        
        Args:
            prompt: User message
            
        Returns:
            JSON string of DiagramDetectionOutput
        """
        messages = [
            SystemMessage(content=DIAGRAM_DETECTION_SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ]
        
        # Call LLM with structured output
        result: DiagramDetectionOutput = self.llm_structured.invoke(messages)
        
        # Convert to JSON string for consistency with base class
        return result.model_dump_json()
    
    def execute(self, state: State) -> State:
        """
        Execute diagram detection and update state
        
        Args:
            state: Current state
            
        Returns:
            Updated state with diagram_types populated
        """
        try:
            print(f"[{self.name}] Starting execution")
            
            # Create user prompt
            user_prompt = self.create_user_prompt(state)
            
            # Call LLM
            llm_output_json = self.call_llm(user_prompt)
            
            # Parse structured output
            output = DiagramDetectionOutput.model_validate_json(llm_output_json)
            
            # Update state
            state.diagram_types = output.diagram_types
            
            print(f"[{self.name}] Detected diagrams: {[dt.value for dt in output.diagram_types]}")
            print(f"[{self.name}] Confidence: {output.confidence_score}")
            
            return state
            
        except Exception as e:
            print(f"[{self.name}] Error during execution: {e}")
            # Set empty list on error
            state.diagram_types = []
            return state