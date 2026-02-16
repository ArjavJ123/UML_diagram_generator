"""
PlantUML Code Generation Node
Generates PlantUML code from context operations
"""
import json
import os
from typing import Dict, Any, Optional, List, Tuple, Union
from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from utils.dataclasses import Node, State, DiagramState, DiagramType
from utils.prompts import PLANTUML_GENERATION_SYSTEM_PROMPT
from utils.constants import OPENAI_MODEL, PLANTUML_CODE_DIR
from utils.file_utils import load_json, load_file, save_file
from utils.db_utils import get_latest_diagram
from utils.decorators import retry_on_failure


# ===== PYDANTIC OUTPUT MODEL =====

class PlantUMLLocation(BaseModel):
    """Location for PlantUML code insertion in update flow"""
    after_line: str = Field(description="Line pattern to insert after, format: (text)[occurrence]")
    before_line: str = Field(description="Line pattern to insert before, format: (text)[occurrence]")


class PlantUMLOperation(BaseModel):
    """Single PlantUML code operation"""
    operation: str = Field(description="Operation type: add or delete")
    location: Union[str, PlantUMLLocation] = Field(
        description="'root' for new diagrams, or location object for updates"
    )
    block: str = Field(description="PlantUML code snippet as string")
    reasoning: str = Field(description="How this operation reflects context changes")


class PlantUMLGenerationOutput(BaseModel):
    """Structured output for PlantUML generation"""
    operations: List[PlantUMLOperation] = Field(description="List of PlantUML operations")


# ===== NODE IMPLEMENTATION =====

class CodeGenerator(Node):
    """
    Node for generating PlantUML code from context operations
    Handles both new diagram creation and updates
    """
    
    def __init__(self):
        super().__init__("CodeGenerator")
        self.llm = ChatOpenAI(
            model=OPENAI_MODEL,
            temperature=0
        )
        self.llm_structured = self.llm.with_structured_output(
            PlantUMLGenerationOutput,
            method="function_calling"
        )
        self.current_diagram_type: Optional[DiagramType] = None
    
    # ===== USER PROMPT BUILDERS =====
    
    def _build_base_prompt(self, context_operations: List[Dict[str, Any]], diagram_type: DiagramType) -> str:
        """
        Common prompt prefix for both flows
        
        Args:
            context_operations: Context change operations
            diagram_type: Type of diagram to generate
            
        Returns:
            Base prompt string
        """
        prompt = f"Diagram Type: {diagram_type.value}\n\n"
        
        prompt += "Context Changes:\n"
        prompt += f"```json\n{json.dumps(context_operations, indent=2)}\n```\n\n"
        
        return prompt
    
    def _create_flow1_prompt(self, base_prompt: str) -> str:
        """
        NEW diagram (Flow 1)
        
        Args:
            base_prompt: Base prompt with diagram type and context operations
            
        Returns:
            Complete Flow 1 prompt
        """
        return base_prompt + """Task: Create a NEW PlantUML diagram.

Instructions:
- Analyze the context changes to understand the complete diagram structure
- Generate EXACTLY ONE operation
- operation MUST be "add"
- location MUST be "root"
- block MUST contain complete PlantUML code from @startuml to @enduml
- Use proper syntax for the diagram type
- Include all entities, relationships, and details from the context
- Ensure proper formatting and indentation
- Follow PlantUML best practices

Remember:
- Start with @startuml
- End with @enduml
- Use correct syntax for the diagram type (class, sequence, component, etc.)
- Make the code clean and readable
"""
    
    def _create_flow2_prompt(self, base_prompt: str, previous_code: str) -> str:
        """
        UPDATE diagram (Flow 2)
        
        Args:
            base_prompt: Base prompt with diagram type and context operations
            previous_code: Previous PlantUML code to update
            
        Returns:
            Complete Flow 2 prompt
        """
        prompt = base_prompt
        
        prompt += "Previous PlantUML Code:\n"
        prompt += f"```plantuml\n{previous_code}\n```\n\n"
        
        prompt += """Task: Update the PlantUML code to reflect the context changes.

Instructions:
- Map each context change to PlantUML operation(s)
- Generate MINIMAL operations (only what changed)
- Use location objects with after_line and before_line patterns
- Ensure line patterns exist in the previous code
- Use occurrence numbers [1], [2], etc. for duplicate lines
- Block must be valid PlantUML code snippet
- Preserve existing code structure
- DO NOT regenerate entire code

Context Change → PlantUML Operation Mapping:
- Add entity → Add class/component/participant
- Add relationship → Add association/dependency/message
- Delete entity → Delete class/component/participant
- Delete relationship → Delete association/dependency/message
- Modify entity → Delete + Add operations

Location Format:
{
  "after_line": "(exact text from code)[occurrence_number]",
  "before_line": "(exact text from code)[occurrence_number]"
}

Example:
{
  "after_line": "(class User {)[1]",
  "before_line": "(@enduml)[1]"
}

Remember:
- Use precise line patterns that exist in the previous code
- Occurrence starts at [1] for first match
- Keep changes minimal and targeted
- Maintain code formatting and style
- Validate that the final code is syntactically correct PlantUML if you perform operation at a given location, ensure that the block you are adding is valid in that context (e.g., don't add a relationship inside a class definition)
"""
        
        return prompt
    
    def create_user_prompt(self, state: State) -> str:
        """
        Main entry point for prompt creation
        
        Args:
            state: Current state
            
        Returns:
            User prompt string
        """
        if not self.current_diagram_type:
            raise ValueError("current_diagram_type must be set before creating prompt")
        
        print(f"[{self.name}] Creating user prompt...")
        
        # Get context operations from diagram state
        diagram_state = state.get_diagram_state(self.current_diagram_type)
        if not diagram_state or not diagram_state.context_operations:
            raise ValueError("No context operations found in diagram state")
        
        context_operations = diagram_state.context_operations
        
        # Build base prompt
        base_prompt = self._build_base_prompt(context_operations, self.current_diagram_type)
        
        # Determine which flow to use
        previous_code = None
        
        if state.is_update_flow():
            # Try to get previous code
            latest_diagram = get_latest_diagram(
                user_id=state.user_id,
                thread_id=state.thread_id,
                diagram_type=self.current_diagram_type.value
            )
            
            if latest_diagram and latest_diagram.get('plantuml_code_file_path'):
                previous_code = load_file(latest_diagram['plantuml_code_file_path'])
        
        if previous_code:
            print(f"[{self.name}] Using Flow 2 (update)")
            return self._create_flow2_prompt(base_prompt, previous_code)
        
        # Flow 1: New diagram
        print(f"[{self.name}] Using Flow 1 (new diagram)")
        return self._create_flow1_prompt(base_prompt)
    
    def call_llm(self, prompt: str) -> str:
        """
        Call LLM with structured output
        
        Args:
            prompt: User message
            
        Returns:
            JSON string of PlantUMLGenerationOutput
        """
        print(f"[{self.name}] Calling LLM...")
        
        messages = [
            SystemMessage(content=PLANTUML_GENERATION_SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ]
        
        result: PlantUMLGenerationOutput = self.llm_structured.invoke(messages)
        
        print(f"[{self.name}] LLM returned {len(result.operations)} operations")
        
        return result.model_dump_json()
    
    def apply_operations(
        self,
        previous_code: Optional[str],
        operations: List[PlantUMLOperation]
    ) -> str:
        """
        Apply PlantUML operations to create final code
        
        Args:
            previous_code: Previous PlantUML code (None for new diagrams)
            operations: List of operations to apply
            
        Returns:
            Final PlantUML code as string
        """
        print(f"\n[{self.name}] Applying {len(operations)} operations...")
        
        code = previous_code if previous_code else ""
        
        for i, op in enumerate(operations):
            operation = op.operation
            location = op.location
            block = op.block
            reasoning = op.reasoning
            
            print(f"\n[{self.name}] {'='*60}")
            print(f"[{self.name}] Operation {i+1}:")
            print(f"[{self.name}]   Type: {operation}")
            print(f"[{self.name}]   Location: {location}")
            
            # Pretty print block
            if len(block) > 100:
                print(f"[{self.name}]   Block preview (first 100 chars): {block[:100]}...")
            else:
                print(f"[{self.name}]   Block:\n{block}")
            
            print(f"[{self.name}]   Reasoning: {reasoning}")
            print(f"[{self.name}] {'='*60}")
            
            if location == "root":
                # Replace entire code
                print(f"[{self.name}]   → Replacing entire code")
                code = block
            elif isinstance(location, PlantUMLLocation):
                # Apply specific operation with location object
                print(f"[{self.name}]   → Applying at specific location")
                code = self._apply_operation(code, operation, location, block)
            else:
                # Handle dict location (from Pydantic)
                if isinstance(location, dict):
                    location_obj = PlantUMLLocation(**location)
                    code = self._apply_operation(code, operation, location_obj, block)
                else:
                    raise ValueError(f"Invalid location type: {type(location)}")
        
        print(f"\n[{self.name}] Final code length: {len(code)} characters")
        
        return code
    
    def _apply_operation(
        self,
        code: str,
        operation: str,
        location: PlantUMLLocation,
        block: str
    ) -> str:
        """
        Apply a single operation to code
        
        Args:
            code: Current PlantUML code
            operation: 'add' or 'delete'
            location: Location object with after_line and before_line
            block: Code snippet to add/delete
            
        Returns:
            Updated code
        """
        import re
        
        if operation == "add":
            # Parse location patterns
            after_pattern, after_occurrence = self._parse_location_pattern(location.after_line)
            before_pattern, before_occurrence = self._parse_location_pattern(location.before_line)
            
            # Find insertion point
            lines = code.split('\n')
            after_idx = self._find_line_index(lines, after_pattern, after_occurrence)
            before_idx = self._find_line_index(lines, before_pattern, before_occurrence)
            
            if after_idx == -1:
                print(f"[{self.name}]     Warning: after_line pattern not found: {after_pattern}")
                print(f"[{self.name}]     Appending to end instead")
                return code + "\n" + block
            
            if before_idx == -1:
                print(f"[{self.name}]     Warning: before_line pattern not found: {before_pattern}")
                before_idx = len(lines)
            
            # Insert block after after_idx
            insertion_idx = after_idx + 1
            lines.insert(insertion_idx, block)
            
            print(f"[{self.name}]     Inserted at line {insertion_idx}")
            
            return '\n'.join(lines)
        
        elif operation == "delete":
            # Find and remove the block
            block_lines = block.split('\n')
            code_lines = code.split('\n')
            
            # Find block in code
            for i in range(len(code_lines) - len(block_lines) + 1):
                if code_lines[i:i+len(block_lines)] == block_lines:
                    # Found the block, remove it
                    del code_lines[i:i+len(block_lines)]
                    print(f"[{self.name}]     Deleted {len(block_lines)} lines starting at line {i}")
                    return '\n'.join(code_lines)
            
            print(f"[{self.name}]     Warning: Block not found for deletion")
            return code
        
        return code
    
    def _parse_location_pattern(self, pattern: str) -> Tuple[str, int]:
        """
        Parse location pattern like "(class User {)[1]"
        
        Args:
            pattern: Pattern string
            
        Returns:
            (text_pattern, occurrence_number)
        """
        import re
        
        # Extract text and occurrence: "(text)[n]"
        match = re.match(r'\((.+?)\)\[(\d+)\]', pattern)
        if match:
            text = match.group(1)
            occurrence = int(match.group(2))
            return (text, occurrence)
        
        # If no brackets, treat as first occurrence
        return (pattern, 1)
    
    def _find_line_index(self, lines: List[str], pattern: str, occurrence: int) -> int:
        """
        Find the nth occurrence of a pattern in lines
        
        Args:
            lines: List of code lines
            pattern: Pattern to search for (or "EMPTY_LINE" for empty lines)
            occurrence: Which occurrence to find (1-indexed)
            
        Returns:
            Line index (0-indexed) or -1 if not found
        """
        import re
        
        count = 0
        
        # Special case: empty line matching
        if pattern == "EMPTY_LINE":
            for i, line in enumerate(lines):
                if line.strip() == "":  # Match empty or whitespace-only lines
                    count += 1
                    if count == occurrence:
                        return i
            return -1
        
        # Normal pattern matching
        for i, line in enumerate(lines):
            if re.search(re.escape(pattern), line):
                count += 1
                if count == occurrence:
                    return i
        
        return -1
    
    def validate_output(self, state: State) -> Tuple[bool, str]:
        """
        Validate that the generated PlantUML code is syntactically valid
        
        Args:
            state: State after execution
            
        Returns:
            (is_valid, error_message) tuple
        """
        try:
            diagram_state = state.get_diagram_state(self.current_diagram_type)
            
            if not diagram_state:
                return (False, "No diagram state found")
            
            if not diagram_state.plantuml_code_file_path:
                return (False, "No PlantUML code file path found")
            
            # Load the code
            code_file_path = diagram_state.plantuml_code_file_path
            
            if not os.path.exists(code_file_path):
                return (False, f"Code file does not exist: {code_file_path}")
            
            code = load_file(code_file_path)
            
            if not code:
                return (False, "PlantUML code is empty")
            
            code = code.strip()
            
            # Basic validation
            if '@startuml' not in code:
                return (False, "Missing @startuml tag")
            
            if '@enduml' not in code:
                return (False, "Missing @enduml tag")
            
            start_pos = code.find('@startuml')
            end_pos = code.find('@enduml')
            
            if start_pos >= end_pos:
                return (False, "@startuml must come before @enduml")
            
            content = code[start_pos+9:end_pos].strip()
            if not content:
                return (False, "Empty diagram content between tags")
            
            print(f"[{self.name}] ✓ PlantUML code validation passed")
            return (True, "")
        
        except Exception as e:
            return (False, f"Validation error: {e}")
    
    def save_code_file(self, state: State, diagram_type: DiagramType, code: str) -> str:
        """
        Save PlantUML code to file
        
        Args:
            state: Current state
            diagram_type: Diagram type
            code: PlantUML code string
            
        Returns:
            File path where code was saved
        """
        file_path = os.path.join(
            PLANTUML_CODE_DIR,
            state.thread_id,
            state.message_id,
            diagram_type.value,
            "diagram.puml"
        )
        
        print(f"[{self.name}] Saving to: {file_path}")
        
        try:
            save_file(code, file_path)
            print(f"[{self.name}] ✓ Saved successfully")
        except Exception as e:
            print(f"[{self.name}] ✗ Failed to save: {e}")
            raise
        
        return file_path
    
    @retry_on_failure(max_retries=3, validation_method='validate_output')
    def execute(self, state: State) -> State:
        """
        Execute PlantUML code generation for a specific diagram type
        
        Args:
            state: Current state
            
        Returns:
            Updated state with PlantUML code added
        """
        if not self.current_diagram_type:
            raise ValueError("current_diagram_type must be set before calling execute")
        
        print(f"\n{'='*70}")
        print(f"[{self.name}] Starting execution for {self.current_diagram_type.value}")
        print(f"{'='*70}")
        
        # Create user prompt
        user_prompt = self.create_user_prompt(state)
        
        # Call LLM
        llm_output_json = self.call_llm(user_prompt)
        
        # Parse structured output
        output = PlantUMLGenerationOutput.model_validate_json(llm_output_json)
        
        # Get previous code if update flow
        previous_code = None
        if state.is_update_flow():
            latest_diagram = get_latest_diagram(
                user_id=state.user_id,
                thread_id=state.thread_id,
                diagram_type=self.current_diagram_type.value
            )
            if latest_diagram and latest_diagram.get('plantuml_code_file_path'):
                previous_code = load_file(latest_diagram['plantuml_code_file_path'])
                if previous_code:
                    print(f"[{self.name}] Loaded previous code")
        
        # Apply operations
        final_code = self.apply_operations(previous_code, output.operations)
        
        # Save code file
        code_file_path = self.save_code_file(state, self.current_diagram_type, final_code)
        
        # Store operations in state
        operations_dict = [op.model_dump() for op in output.operations]
        
        # Update diagram state
        diagram_state = state.get_diagram_state(self.current_diagram_type)
        if diagram_state:
            diagram_state.plantuml_code_file_path = code_file_path
            diagram_state.add_code_operations(operations_dict)
        else:
            raise ValueError(f"Diagram state not found for {self.current_diagram_type.value}")
        
        print(f"[{self.name}] Stored {len(operations_dict)} code operations in state")
        
        print(f"\n{'='*70}")
        print(f"[{self.name}] ✓ Execution completed")
        print(f"{'='*70}\n")
        
        return state