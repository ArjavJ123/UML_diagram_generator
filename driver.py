"""
Driver function for end-to-end diagram generation flow
"""

import os
from typing import List, Optional, Generator

from utils.dataclasses import State, DiagramType
from parsers.parser import parse_files
from utils.db_utils import (
    add_message,
    get_thread_messages,
    get_latest_diagram,
    update_after_run
)
from nodes.context_extractor import ContextExtractor
from nodes.code_generator import CodeGenerator
from tools.plant_uml_renderer import render_plantuml_to_png


def _generate_diagram_id(
    user_id: str,
    thread_id: str,
    message_id: str,
    diagram_type: str
) -> str:
    """Deterministic diagram ID"""
    return f"{user_id}_{thread_id}_{message_id}_{diagram_type}"


def run_driver(
    user_id: str,
    thread_id: str,
    message_id: str,
    prompt: str,
    supporting_files_directory_path: Optional[str] = None,
    diagram_types: Optional[List[DiagramType]] = None
) -> Generator[dict, None, dict]:
    """
    Main driver function that yields progress updates
    """
    
    print("\n" + "="*80)
    print("🚀 DRIVER: Starting")
    print("="*80)
    
    yield {
        "status": "started",
        "message": "🚀 Starting diagram generation",
        "progress": 0
    }

    # ===== STEP 1: FETCH THREAD HISTORY =====
    print("📋 DRIVER: Fetching thread history")
    yield {
        "status": "processing",
        "message": "📋 Fetching conversation history",
        "progress": 5
    }
    
    thread_messages = get_thread_messages(thread_id)
    parent_message_id = thread_messages[-1]["message_id"] if thread_messages else None

    # ===== STEP 2: CREATE MESSAGE ENTRY =====
    print("💾 DRIVER: Saving message")
    yield {
        "status": "processing",
        "message": "💾 Saving message",
        "progress": 10
    }
    
    add_message(
        user_id=user_id,
        thread_id=thread_id,
        message_id=message_id,
        prompt=prompt,
        parent_message_id=parent_message_id,
        user_files_directory_path=supporting_files_directory_path
    )

    # ===== STEP 3: CREATE STATE =====
    state = State(
        user_id=user_id,
        thread_id=thread_id,
        message_id=message_id,
        prompt=prompt,
        parent_message_id=parent_message_id,
        supporting_file_directory_path=supporting_files_directory_path
    )

    # ===== STEP 4: PARSE FILES =====
    if supporting_files_directory_path:
        print("📂 DRIVER: Parsing files")
        yield {
            "status": "processing",
            "message": "📂 Parsing uploaded files",
            "progress": 15
        }
        
        parsed_files = parse_files(supporting_files_directory_path)
        for path, content in parsed_files.items():
            state.add_parsed_file(path, content)
        print(f"Parsed {len(parsed_files)} files")

    # ===== STEP 5: DIAGRAM TYPE DETECTION =====
    if not diagram_types:
        diagram_types = [DiagramType.CLASS]

    state.diagram_types = diagram_types
    
    print(f"🧠 DRIVER: Detected diagram types: {[dt.value for dt in diagram_types]}")
    yield {
        "status": "processing",
        "message": f"🧠 Detected {len(diagram_types)} diagram type(s): {', '.join([dt.value for dt in diagram_types])}",
        "progress": 20
    }

    # ===== STEP 6: INITIALIZE NODES =====
    extractor = ContextExtractor()
    generator = CodeGenerator()
    diagram_records = []

    # Calculate progress increments
    total_diagrams = len(diagram_types)
    progress_per_diagram = 70 / total_diagrams

    # ===== STEP 7: PROCESS EACH DIAGRAM TYPE =====
    for idx, diagram_type in enumerate(diagram_types, 1):
        base_progress = 20 + (idx - 1) * progress_per_diagram
        
        print(f"\n🔷 DRIVER: Processing {diagram_type.value} ({idx}/{total_diagrams})")
        yield {
            "status": "processing",
            "message": f"🔷 Processing {diagram_type.value} diagram ({idx}/{total_diagrams})",
            "progress": int(base_progress)
        }

        extractor.current_diagram_type = diagram_type
        generator.current_diagram_type = diagram_type

        # NODE 2
        print(f"📝 DRIVER: Extracting context for {diagram_type.value}")
        yield {
            "status": "processing",
            "message": f"📝 Extracting context for {diagram_type.value} diagram",
            "progress": int(base_progress + progress_per_diagram * 0.2)
        }
        state = extractor.execute(state)

        # NODE 3
        print(f"⚙️ DRIVER: Generating code for {diagram_type.value}")
        yield {
            "status": "processing",
            "message": f"⚙️ Generating PlantUML code for {diagram_type.value} diagram",
            "progress": int(base_progress + progress_per_diagram * 0.5)
        }
        state = generator.execute(state)

        # GET STATE
        diagram_state = state.get_diagram_state(diagram_type)

        # RENDER PNG
        print(f"🖼️ DRIVER: Rendering {diagram_type.value} PNG")
        yield {
            "status": "processing",
            "message": f"🖼️ Rendering {diagram_type.value} diagram image",
            "progress": int(base_progress + progress_per_diagram * 0.8)
        }

        png_output_path = os.path.join(
            "data/diagrams",
            thread_id,
            message_id,
            diagram_type.value,
            "diagram.png"
        )

        png_path = render_plantuml_to_png(
            plantuml_code=open(diagram_state.plantuml_code_file_path).read(),
            output_path=png_output_path
        )

        diagram_state.diagram_png_file_path = png_path

        # VERSIONING
        latest_diagram = get_latest_diagram(
            user_id=user_id,
            thread_id=thread_id,
            diagram_type=diagram_type.value
        )

        if latest_diagram:
            version = latest_diagram["version"] + 1
            parent_diagram_id = latest_diagram["diagram_id"]
        else:
            version = 1
            parent_diagram_id = None

        diagram_state.version = version

        # PREPARE DB RECORD
        diagram_id = _generate_diagram_id(
            user_id=user_id,
            thread_id=thread_id,
            message_id=message_id,
            diagram_type=diagram_type.value
        )

        diagram_record = {
            "diagram_id": diagram_id,
            "user_id": user_id,
            "thread_id": thread_id,
            "message_id": message_id,
            "diagram_type": diagram_type.value,
            "version": version,
            "parent_diagram_id": parent_diagram_id,
            "context_file_path": diagram_state.context_file_path,
            "plantuml_code_file_path": diagram_state.plantuml_code_file_path,
            "diagram_png_file_path": diagram_state.diagram_png_file_path
        }

        diagram_records.append(diagram_record)

        print(f"✅ DRIVER: {diagram_type.value} complete (v{version})")
        yield {
            "status": "processing",
            "message": f"✅ {diagram_type.value} diagram complete (v{version})",
            "progress": int(base_progress + progress_per_diagram)
        }

    # ===== STEP 11: UPDATE DATABASE =====
    print("💾 DRIVER: Updating database")
    yield {
        "status": "processing",
        "message": "💾 Saving to database",
        "progress": 95
    }
    
    update_after_run(
        message_id=message_id,
        diagram_records=diagram_records
    )

    print("✅ DRIVER: Complete")
    yield {
        "status": "complete",
        "message": "✅ All diagrams generated successfully",
        "progress": 100
    }

    print("\n" + "="*80)
    print("✅ DRIVER COMPLETED SUCCESSFULLY")
    print("="*80)

    # Return final result
    return {
        "message_id": message_id,
        "diagram_ids": [d["diagram_id"] for d in diagram_records],
        "png_paths": [d["diagram_png_file_path"] for d in diagram_records]
    }