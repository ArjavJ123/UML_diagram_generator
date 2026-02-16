"""
Context Extraction Node
Extracts structured JSON context for diagram generation
"""
import json
import os
from typing import Dict, Any, Optional, List, Tuple, Union
from pydantic import BaseModel, Field

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from utils.dataclasses import Node, State, DiagramState, DiagramType
from utils.prompts import CONTEXT_EXTRACTION_SYSTEM_PROMPT
from utils.constants import GEMINI_MODEL, CONTEXT_DIR, OPENAI_MODEL
from utils.file_utils import load_json, save_json
from utils.db_utils import get_latest_diagram
from utils.decorators import retry_on_failure

# ===== PYDANTIC OUTPUT MODEL =====

class Operation(BaseModel):
    operation: str = Field(description="Operation type: add or delete")
    location: str = Field(description="Location path in JSON")
    block: Union[Dict[str, Any], List[Any], str] = Field(
        description="Value to add or delete. Must be object, list, or string. NEVER number, boolean, or null."
    )
    reasoning: str = Field(description="Explanation of why this block is the right block")


class ContextExtractionOutput(BaseModel):
    """Structured output for context extraction"""
    operations: List[Operation] = Field(description="List of operations")


# ===== NODE IMPLEMENTATION =====

class ContextExtractor(Node):
    """
    Node for extracting structured context from user request
    Handles both new diagram creation and updates
    """
    
    def __init__(self):
        super().__init__("ContextExtractor")
        self.llm = ChatOpenAI(
            model=OPENAI_MODEL,
            temperature=0
        )
        self.llm_structured = self.llm.with_structured_output(ContextExtractionOutput, method= "function_calling")
        self.current_diagram_type: Optional[DiagramType] = None
    # ===== USER PROMPT BUILDERS =====

    def _build_base_prompt(self, state: State, diagram_type: DiagramType) -> str:
        """Common prompt prefix for both flows"""
        
        user_message = f"User Request:\n{state.prompt}\n\n"
        user_message += f"Diagram Type: {diagram_type.value}\n\n"

        # Supporting files
        if state.parsed_files:
            user_message += "Supporting File Information:\n"
            for file_path, content in state.parsed_files.items():
                truncated = content[:2000] + "..." if len(content) > 2000 else content
                user_message += f"\n--- {file_path} ---\n{truncated}\n"

        return user_message


    def _create_flow1_prompt(self, base_prompt: str) -> str:
        """NEW diagram (Flow 1)"""

        return """
    Task: Create a NEW UML diagram context JSON dictionary.

    Strict Instructions:
    - Generate EXACTLY ONE operation
    - operation MUST be "add"
    - location MUST be "root"
    - block MUST be a complete JSON dictionary only, no other datatype allowed.
    - Do NOT generate partial structures
    - Follow the system rules strictly

    Example:
        {
        "operation": "add",
        "location" : "root",
        "block": {
            "entities": [
                {
                    "name": "employee",
                    "attributes": ["id", "name", "department"]
                },
                {
                    "name": "department",
                    "attributes": ["id", "name"]
                }
            ]
            "relationships": [
                {
                    "from": "employee", 
                    "to": "department",
                    "type": "many-to-one"
                }
            ]
    }
    
    ONLY GENERATE A DICTIONARY ELSE THE BLOCK WILL NOT PARSE AND THE AGENT WILL FAIL
    """ + base_prompt


    def _create_flow2_prompt(self, base_prompt: str, previous_context: Dict[str, Any]) -> str:
        """UPDATE diagram (Flow 2)"""

        prompt = base_prompt

        prompt += "\nPrevious Context (Current State):\n"
        prompt += f"```json\n{json.dumps(previous_context, indent=2)}\n```\n\n"

        prompt += """
    Task: Update the existing UML diagram.

    Instructions:
    - Generate ONLY necessary operations
    - Use precise locations (e.g., "entities[end]", "relationships[0]")
    - DO NOT recreate full context
    - Follow existing structure exactly
    - Replace = delete + add (never use replace)
    - Do NOT use numbers, booleans, or null
    - If unsure, SKIP the operation
    - Keep changes minimal and consistent

    ----------------------------------------
    VALID EXAMPLE
    ----------------------------------------

    {
    "operation": "add",
    "location": "entities[end]",
    "block": {
        "name": "Payment",
        "attributes": ["payment_id", "amount", "status", "payment_date"]
    }
    }
    """

        return prompt


    def create_user_prompt(self, state: State) -> str:
        """Main entry point for prompt creation"""

        if not self.current_diagram_type:
            raise ValueError("current_diagram_type must be set before creating prompt")

        print(f"[{self.name}] Creating user prompt...")

        base_prompt = self._build_base_prompt(state, self.current_diagram_type)

        previous_context = None

        if state.is_update_flow():
            latest_diagram = get_latest_diagram(
                user_id=state.user_id,
                thread_id=state.thread_id,
                diagram_type=self.current_diagram_type.value
            )

            if latest_diagram and latest_diagram['context_file_path']:
                previous_context = load_json(latest_diagram['context_file_path'])

        if previous_context:
            print(f"[{self.name}] Using Flow 2 (update)")
            print(f"USING THE UPDATED METHOD")
            return self._create_flow2_prompt(base_prompt, previous_context)

        print(f"[{self.name}] Using Flow 1 (new diagram)")
        return self._create_flow1_prompt(base_prompt)

        
    def call_llm(self, prompt: str) -> str:
        """Call LLM with structured output"""
        print(f"[{self.name}] Calling LLM...")
        
        messages = [
            SystemMessage(content=CONTEXT_EXTRACTION_SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ]
        print(f"[{self.name}] User prompt length: {len(prompt)}")
        result: ContextExtractionOutput = self.llm_structured.invoke(messages)
        
        print(f"[{self.name}] LLM returned {len(result.operations)} operations")
        
        return result.model_dump_json()
    
    def parse_block_value(self, block: Any) -> Any:
        """
        Parse block value - handle JSON strings returned by Gemini
        
        Args:
            block: Raw block value from LLM
            
        Returns:
            Parsed block value (dict/list/str)
        """
        # If it's a string, try to parse as JSON
        if isinstance(block, str):
            # Check if it looks like JSON
            stripped = block.strip()
            if (stripped.startswith('{') and stripped.endswith('}')) or \
               (stripped.startswith('[') and stripped.endswith(']')):
                try:
                    parsed = json.loads(block)
                    print(f"[{self.name}]   Parsed JSON string to {type(parsed).__name__}")
                    return parsed
                except json.JSONDecodeError as e:
                    print(f"[{self.name}]   Failed to parse JSON string: {e}")
                    print(f"[{self.name}]   Keeping as plain string")
                    return block
        
        # Return as-is if not a JSON string
        return block
    
    def apply_operations(self, previous_context: Optional[Dict[str, Any]], operations: List[Operation]) -> Dict[str, Any]:
        """Apply operations to create new context"""
        print(f"\n[{self.name}] Applying {len(operations)} operations...")
        
        context = previous_context.copy() if previous_context else {}
        
        for i, op in enumerate(operations):
            operation = op.operation
            location = op.location
            block = op.block
            reasoning = op.reasoning
            
            # Parse block value (handles JSON strings)
            parsed_block = self.parse_block_value(block)
            
            print(f"\n[{self.name}] {'='*60}")
            print(f"[{self.name}] Operation {i+1}:")
            print(f"[{self.name}]   Type: {operation}")
            print(f"[{self.name}]   Location: {location}")
            print(f"[{self.name}]   Block type (original): {type(block).__name__}")
            print(f"[{self.name}]   Block value (original): {block}")

            print(f"[{self.name}]   Block type (parsed): {type(parsed_block).__name__}")

            # Pretty print parsed block
            if isinstance(parsed_block, (dict, list)):
                try:
                    pretty_block = json.dumps(parsed_block, indent=2)
                    print(f"[{self.name}]   Block value (parsed):\n{pretty_block}")
                except Exception:
                    print(f"[{self.name}]   Block value (parsed): {parsed_block}")
            else:
                print(f"[{self.name}]   Block value (parsed): {parsed_block}")

            print(f"[{self.name}]   Reasoning: {reasoning}")
            print(f"[{self.name}] {'='*60}")
            
            if location == "root":
                # Validate root must be dict
                if not isinstance(parsed_block, dict):
                    raise ValueError(
                        f"Root location requires a dictionary block. "
                        f"Got {type(parsed_block).__name__}: {parsed_block}"
                    )
                
                print(f"[{self.name}]   → Replacing entire context")
                context = parsed_block
            else:
                print(f"[{self.name}]   → Applying at specific location")
                context = self._apply_operation(context, operation, location, parsed_block)
        
        print(f"\n[{self.name}] Final context type: {type(context).__name__}")
        if isinstance(context, dict):
            print(f"[{self.name}] Final context keys: {list(context.keys())}")
        
        return context
    
    def _apply_operation(self, context: Dict[str, Any], operation: str, location: str, value: Any) -> Dict[str, Any]:
        """Apply a single operation to context"""
        import re
        
        parts = []
        tokens = re.split(r'\.', location)
        
        for token in tokens:
            match = re.match(r'([^\[]+)(?:\[(\d+|end)\])?', token)
            if match:
                key = match.group(1)
                index_str = match.group(2)
                
                if index_str:
                    index = "end" if index_str == "end" else int(index_str)
                else:
                    index = None
                
                parts.append((key, index))
        
        current = context
        
        # Navigate to parent
        for i, (key, index) in enumerate(parts[:-1]):
            if key not in current:
                current[key] = [] if index is not None else {}
            
            if index is not None:
                if index != "end":
                    if index < len(current[key]):
                        current = current[key][index]
                    else:
                        while len(current[key]) <= index:
                            current[key].append({})
                        current = current[key][index]
            else:
                current = current[key]
        
        # Apply operation at target
        last_key, last_index = parts[-1]
        
        if operation == "add":
            if last_index is not None:
                if last_key not in current:
                    current[last_key] = []
                
                if last_index == "end":
                    current[last_key].append(value)
                    print(f"[{self.name}]     Added to {last_key}[end]")
                else:
                    if last_index <= len(current[last_key]):
                        current[last_key].insert(last_index, value)
                        print(f"[{self.name}]     Inserted at {last_key}[{last_index}]")
            else:
                current[last_key] = value
                print(f"[{self.name}]     Set {last_key}")
        
        elif operation == "delete":
            if last_index is not None:
                if last_key in current and isinstance(current[last_key], list):
                    if last_index != "end" and 0 <= last_index < len(current[last_key]):
                        del current[last_key][last_index]
                        print(f"[{self.name}]     Deleted {last_key}[{last_index}]")
            else:
                if last_key in current:
                    del current[last_key]
                    print(f"[{self.name}]     Deleted key {last_key}")
        
        return context
    
    def validate_output(self, state: State) -> Tuple[bool, str]:
        """
        Validate that the generated context is valid JSON
        
        Args:
            state: State after execution
            
        Returns:
            (is_valid, error_message) tuple
        """
        try:
            # Get the diagram state
            diagram_state = state.get_diagram_state(self.current_diagram_type)
            
            if not diagram_state:
                return (False, "No diagram state found")
            
            if not diagram_state.context_file_path:
                return (False, "No context file path found")
            
            # Validate the file exists and is valid JSON
            context_file_path = diagram_state.context_file_path
            
            if not os.path.exists(context_file_path):
                return (False, f"Context file does not exist: {context_file_path}")
            
            # Load and validate JSON
            try:
                with open(context_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                context = json.loads(content)
                
                # Check if it's a dict
                if not isinstance(context, dict):
                    return (False, f"Context is not a dictionary, got {type(context).__name__}")
                
                # Check if it has any content
                if not context:
                    return (False, "Context is an empty dictionary")
                
                print(f"[{self.name}] ✓ Context validation passed")
                return (True, "")
                
            except json.JSONDecodeError as e:
                return (False, f"Invalid JSON in context file: {e}")
        
        except Exception as e:
            return (False, f"Validation error: {e}")
    
    def save_context_file(self, state: State, diagram_type: DiagramType, context: Dict[str, Any]) -> str:
        """Save context to file with proper formatting"""
        file_path = os.path.join(
            CONTEXT_DIR,
            state.thread_id,
            state.message_id,
            diagram_type.value,
            "context.json"
        )
        
        print(f"[{self.name}] Saving to: {file_path}")
        
        try:
            # Validate it's a dict
            if not isinstance(context, dict):
                raise ValueError(f"Context must be dict, got {type(context).__name__}")
            
            # Save with proper formatting
            save_json(context, file_path)
            print(f"[{self.name}] ✓ Saved successfully")
        except Exception as e:
            print(f"[{self.name}] ✗ Failed to save: {e}")
            raise
        
        return file_path
    
    def _infer_version(self, state: State) -> int:
        """Infer version based on latest diagram in DB"""
        latest = get_latest_diagram(
            user_id=state.user_id,
            thread_id=state.thread_id,
            diagram_type=self.current_diagram_type.value
        )

        if not latest:
            print(f"[{self.name}] No previous diagram → version = 1")
            return 1

        new_version = latest["version"] + 1
        print(f"[{self.name}] Previous version = {latest['version']} → new version = {new_version}")
        return new_version

    @retry_on_failure(max_retries=3, validation_method='validate_output')
    def execute(self, state: State) -> State:
        """Execute context extraction for a specific diagram type"""
        if not self.current_diagram_type:
            raise ValueError("current_diagram_type must be set before calling execute")
        
        print(f"\n{'='*70}")
        print(f"[{self.name}] Starting execution for {self.current_diagram_type.value}")
        print(f"{'='*70}")
        
        user_prompt = self.create_user_prompt(state)
        llm_output_json = self.call_llm(user_prompt)
        output = ContextExtractionOutput.model_validate_json(llm_output_json)
        
        previous_context = None
        if state.is_update_flow():
            latest_diagram = get_latest_diagram(
                user_id=state.user_id,
                thread_id=state.thread_id,
                diagram_type=self.current_diagram_type.value
            )
            if latest_diagram and latest_diagram['context_file_path']:
                previous_context = load_json(latest_diagram['context_file_path'])
                print(f"[{self.name}] Loaded previous context")
        
        new_context = self.apply_operations(previous_context, output.operations)
        context_file_path = self.save_context_file(state, self.current_diagram_type, new_context)
        
        # ===== VERSION INFERENCE =====
        version = self._infer_version(state)

        # Convert Pydantic operations to dict for storage
        operations_dict = [op.model_dump() for op in output.operations]
        
        diagram_state = state.get_diagram_state(self.current_diagram_type)

        if diagram_state:
            diagram_state.context_file_path = context_file_path
            diagram_state.add_context_operations(operations_dict)
            diagram_state.version = version   # ✅ NEW
        else:
            diagram_state = DiagramState(
                diagram_type=self.current_diagram_type,
                context_file_path=context_file_path,
                context_operations=operations_dict,
                version=version   # ✅ NEW
            )
            state.add_diagram_state(diagram_state)
        
        print(f"[{self.name}] Stored {len(operations_dict)} context operations in state")
        print(f"[{self.name}] Version set to {version}")
        
        print(f"\n{'='*70}")
        print(f"[{self.name}] ✓ Execution completed")
        print(f"{'='*70}\n")
        
        return state