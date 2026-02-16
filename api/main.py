"""
FastAPI Server for UML Diagram Generator
"""
from dotenv import load_dotenv
load_dotenv()
import os
import shutil
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel
from driver import run_driver
from utils.dataclasses import DiagramType
from utils.db_utils import (
    get_thread_messages,
    get_thread_diagrams,
    update_diagram_feedback,
    get_diagram
)

from sse_starlette.sse import EventSourceResponse
import json
import asyncio


from utils.constants import MESSAGES_DB, DIAGRAMS_DB


# ===== INIT =====
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

USER_ID = "user_001"

os.makedirs("data", exist_ok=True)
app.mount("/data", StaticFiles(directory="data"), name="data")


# ===== HELPERS =====

def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def _generate_thread_id() -> str:
    existing_threads = set()

    if os.path.exists(MESSAGES_DB):
        from utils.db_utils import _load_messages
        msgs = _load_messages()
        for m in msgs:
            existing_threads.add(m["thread_id"])

    next_id = len(existing_threads) + 1
    return f"thread_{str(next_id).zfill(3)}"


def _generate_message_id(thread_id: str) -> str:
    msgs = get_thread_messages(thread_id)
    next_id = len(msgs) + 1
    return f"msg_{str(next_id).zfill(3)}"


def _message_dir(user_id: str, thread_id: str, message_id: str):
    return f"data/user_files/{user_id}/{thread_id}/{message_id}"


# ===== 1. INITIALISE =====

@app.post("/initialise")
def initialise():
    try:
        if os.path.exists("data"):
            shutil.rmtree("data")

        if os.path.exists("database"):
            shutil.rmtree("database")

        if os.path.exists(MESSAGES_DB):
            os.remove(MESSAGES_DB)

        if os.path.exists(DIAGRAMS_DB):
            os.remove(DIAGRAMS_DB)

        return {"status": "success"}

    except Exception as e:
        return {"status": "error", "message": str(e)}


# ===== 2. CREATE THREAD =====

@app.post("/create-thread")
def create_thread():
    thread_id = _generate_thread_id()
    return {"thread_id": thread_id}


# ===== 3. RUN PIPELINE =====

@app.post("/run")
async def run_pipeline(
    thread_id: str = Form(...),
    prompt: str = Form(...),
    diagram_types: Optional[str] = Form(None),
    files: Optional[List[UploadFile]] = File(None)
):
    """
    Handles:
    - message_id creation
    - file upload
    - driver execution
    """

    # ===== MESSAGE ID =====
    message_id = _generate_message_id(thread_id)

    print(f"\n📩 New message: {message_id}")

    # ===== FILE HANDLING =====
    msg_dir = _message_dir(USER_ID, thread_id, message_id)
    _ensure_dir(msg_dir)

    if files:
        for file in files:
            file_path = os.path.join(msg_dir, file.filename)
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)

    # ===== DIAGRAM TYPES =====
    dt_list = None
    if diagram_types:
        try:
            import json
            parsed = json.loads(diagram_types)
            dt_list = [DiagramType(d) for d in parsed]
        except:
            dt_list = [DiagramType(d.strip()) for d in diagram_types.split(",")]

    # ===== RUN DRIVER =====
    response = run_driver(
        user_id=USER_ID,
        thread_id=thread_id,
        message_id=message_id,
        prompt=prompt,
        supporting_files_directory_path=msg_dir if files else None,
        diagram_types=dt_list
    )

    # ===== FETCH DIAGRAMS =====
    diagrams = get_thread_diagrams(thread_id)

    return {
        "status": "success",
        "message_id": message_id,
        "diagrams": diagrams
    }


# ===== 4. FETCH THREAD =====

@app.get("/thread/{thread_id}")
def fetch_thread(thread_id: str):
    messages = get_thread_messages(thread_id)
    diagrams = get_thread_diagrams(thread_id)

    return {
        "messages": messages,
        "diagrams": diagrams
    }


# ===== 5. SEND FEEDBACK =====

class FeedbackRequest(BaseModel):
    diagram_id: str
    rating: int
    feedback: str


@app.post("/feedback")
def send_feedback(request: FeedbackRequest):  # ← Use Pydantic model
    """Submit feedback for a diagram"""
    print(f"[API] Received feedback for {request.diagram_id}: rating={request.rating}")
    
    success = update_diagram_feedback(
        diagram_id=request.diagram_id,
        user_feedback=request.feedback,
        feedback_rating=request.rating
    )
    
    if success:
        print(f"[API] ✓ Feedback saved successfully")
        return {"success": True, "diagram_id": request.diagram_id}
    else:
        print(f"[API] ✗ Failed to save feedback")
        return {"success": False, "message": "Failed to update feedback"}

# ===== 6. FETCH FEEDBACK =====

@app.get("/feedback/{diagram_id}")
def fetch_feedback(diagram_id: str):
    """
    Fetch feedback for a specific diagram
    """
    
    diagram = get_diagram(diagram_id)
    
    if not diagram:
        return {
            "status": "error",
            "message": f"Diagram not found: {diagram_id}"
        }
    
    return {
        "status": "success",
        "diagram_id": diagram_id,
        "feedback": diagram.get("user_feedback"),
        "rating": diagram.get("feedback_rating"),
        "version": diagram.get("version"),
        "diagram_type": diagram.get("diagram_type")
    }
from sse_starlette.sse import EventSourceResponse
import asyncio
import json

@app.post("/run-stream")
async def run_pipeline_stream(
    thread_id: str = Form(...),
    prompt: str = Form(...),
    diagram_types: Optional[str] = Form(None),
    files: Optional[List[UploadFile]] = File(None)
):
    """
    Streaming version with progress updates
    """
    
    message_id = _generate_message_id(thread_id)
    
    print(f"\n[SSE] Starting stream for message: {message_id}")
    
    # Handle file uploads
    msg_dir = _message_dir(USER_ID, thread_id, message_id)
    _ensure_dir(msg_dir)
    
    if files:
        for file in files:
            file_path = os.path.join(msg_dir, file.filename)
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
    
    # Parse diagram types
    dt_list = None
    if diagram_types:
        try:
            parsed = json.loads(diagram_types)
            dt_list = [DiagramType(d) for d in parsed]
        except:
            dt_list = [DiagramType(d.strip()) for d in diagram_types.split(",")]
    
    # Stream generator
    async def event_generator():
        try:
            print("[SSE] Starting event generator")
            
            # Run driver in executor
            import concurrent.futures
            loop = asyncio.get_event_loop()
            
            # Create the generator
            def run_in_thread():
                return run_driver(
                    user_id=USER_ID,
                    thread_id=thread_id,
                    message_id=message_id,
                    prompt=prompt,
                    supporting_files_directory_path=msg_dir if files else None,
                    diagram_types=dt_list
                )
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_in_thread)
                driver_gen = future.result()
                
                print("[SSE] Got driver generator")
                
                # Stream each progress update
                update_count = 0
                for update in driver_gen:
                    update_count += 1
                    print(f"[SSE] Yielding update #{update_count}: {update.get('message', '')}")
                    
                    yield {
                        "event": "progress",
                        "data": json.dumps(update)
                    }
                    
                    await asyncio.sleep(0.05)  # Small delay
                
                print(f"[SSE] Sent {update_count} updates")
            
            # Send completion
            diagrams = get_thread_diagrams(thread_id)
            print("[SSE] Sending completion event")
            
            yield {
                "event": "complete",
                "data": json.dumps({
                    "status": "success",
                    "message_id": message_id,
                    "diagrams": diagrams
                })
            }
            
        except Exception as e:
            print(f"[SSE] Error: {e}")
            import traceback
            traceback.print_exc()
            
            yield {
                "event": "error",
                "data": json.dumps({
                    "status": "error",
                    "message": str(e)
                })
            }
    
    return EventSourceResponse(event_generator())