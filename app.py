import streamlit as st
import os
import shutil
from pathlib import Path

from driver import run_driver
from utils.dataclasses import DiagramType

# ===== CONFIG =====
st.set_page_config(layout="wide")

USER_ID = "user_001"

# ===== CLEAN DATA ON START =====
if "initialized" not in st.session_state:
    if Path("data").exists():
        shutil.rmtree("data")
    if Path("database").exists():
        shutil.rmtree("database")

    st.session_state.initialized = True

# ===== SESSION STATE =====
if "thread_id" not in st.session_state:
    st.session_state.thread_id = "thread_001"
    st.session_state.thread_count = 1

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []

if "show_upload_modal" not in st.session_state:
    st.session_state.show_upload_modal = False


# ===== HEADER =====
st.title("📊 UML Diagram Generator")
st.divider()


# ===== DISPLAY CHAT =====
for msg in st.session_state.chat_history:
    with st.chat_message("user"):
        st.write(msg["prompt"])

    with st.chat_message("assistant"):
        for dtype, path in msg["images"].items():
            st.image(path, caption=dtype)


# ===== FILE UPLOAD MODAL =====
if st.session_state.show_upload_modal:
    with st.modal("Upload Files"):
        files = st.file_uploader(
            "Upload supporting files",
            accept_multiple_files=True
        )

        if st.button("Save Files"):
            st.session_state.uploaded_files = files
            st.session_state.show_upload_modal = False
            st.rerun()


# ===== CHAT INPUT BAR =====
col1, col2, col3, col4 = st.columns([1, 6, 2, 1])

# ➕ BUTTON
with col1:
    if st.button("➕"):
        st.session_state.show_upload_modal = True

# PROMPT
with col2:
    prompt = st.text_input(
        "Type your message...",
        label_visibility="collapsed"
    )

# DIAGRAM TYPE DROPDOWN
with col3:
    diagram_options = [dt.value for dt in DiagramType]
    selected_types = st.multiselect(
        "Diagram Type",
        diagram_options,
        label_visibility="collapsed"
    )

# SEND BUTTON
with col4:
    send_clicked = st.button("➤")


# ===== HANDLE SEND =====
if send_clicked and prompt:

    # VALIDATION
    if len(st.session_state.chat_history) > 0 and not selected_types:
        st.error("Please select at least one diagram type")
        st.stop()

    # ===== SAVE FILES =====
    file_dir = None

    if st.session_state.uploaded_files:
        msg_index = len(st.session_state.chat_history) + 1
        message_id = f"msg_{str(msg_index).zfill(3)}"

        file_dir = f"data/user_files/{USER_ID}/{st.session_state.thread_id}/{message_id}"
        Path(file_dir).mkdir(parents=True, exist_ok=True)

        for file in st.session_state.uploaded_files:
            with open(os.path.join(file_dir, file.name), "wb") as f:
                f.write(file.getbuffer())

    # ===== RUN DRIVER =====
    diagram_types = [DiagramType(dt) for dt in selected_types] if selected_types else None

    with st.spinner("🚀 Running pipeline..."):
        response = run_driver(
            user_id=USER_ID,
            thread_id=st.session_state.thread_id,
            prompt=prompt,
            supporting_files_directory_path=file_dir,
            diagram_types=diagram_types
        )

    # ===== FETCH IMAGES =====
    images = {}
    for diag_id in response["diagram_ids"]:
        parts = diag_id.split("_")
        dtype = parts[-1]

        path = f"data/diagrams/{USER_ID}/{st.session_state.thread_id}/{dtype}.png"
        if os.path.exists(path):
            images[dtype] = path

    # ===== STORE CHAT =====
    st.session_state.chat_history.append({
        "prompt": prompt,
        "images": images
    })

    # RESET FILES
    st.session_state.uploaded_files = []

    st.rerun()


# ===== NEW THREAD BUTTON =====
if st.button("🆕 New Thread"):
    st.session_state.thread_count += 1
    st.session_state.thread_id = f"thread_{str(st.session_state.thread_count).zfill(3)}"
    st.session_state.chat_history = []
    st.session_state.uploaded_files = []
    st.rerun()
