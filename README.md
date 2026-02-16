# UML Diagram Generator

An AI-powered system that automatically generates UML diagrams from natural language descriptions and uploaded files. Supports multiple diagram types including class, sequence, component, activity, and more.

## Features

- 🤖 **AI-Powered Generation**: Uses GPT-4 to extract context and generate PlantUML code
- 🔄 **Incremental Updates**: Update existing diagrams with new requirements
- 📊 **Multiple Diagram Types**: Class, Sequence, Component, Activity, State, Use Case, and more
- 📁 **File Upload Support**: Upload requirements documents (.txt, .pdf, .doc, .docx, .md)
- 🎨 **Real-time Progress**: Live progress updates during diagram generation
- ⭐ **Feedback System**: Rate and provide feedback on generated diagrams
- 💾 **Version History**: Track diagram evolution across conversation turns
- 🌊 **Multi-threading**: Separate conversation threads for different projects

## Architecture
```
Frontend (React)
    ↓
Backend (FastAPI)
    ↓
Driver (Orchestrator)
    ↓
├─ Node 2: Context Extractor (GPT-4)
├─ Node 3: PlantUML Code Generator (GPT-4)
└─ PlantUML Renderer (Java)
    ↓
Database (JSON files)
```

## Prerequisites

- **Python 3.9+**
- **Node.js 16+** and npm
- **Java 11+** (for PlantUML rendering)
- **OpenAI API Key**

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/ArjavJ123/UML_diagram_generator.git
```

### 2. Backend Setup

#### Install Python Dependencies
```bash
pip install -r requirements.txt
```

#### Download PlantUML JAR

Download the PlantUML JAR file:
```bash
# For macOS/Linux
wget http://sourceforge.net/projects/plantuml/files/plantuml.jar/download -O ~/plantuml.jar

# For Windows (using PowerShell)
Invoke-WebRequest -Uri "http://sourceforge.net/projects/plantuml/files/plantuml.jar/download" -OutFile "$env:USERPROFILE\plantuml.jar"
```

Or download manually from: https://plantuml.com/download

#### Set Environment Variables

Create a `.env` file in the `backend` directory:
```bash
# .env
OPENAI_API_KEY=sk-proj-your-openai-api-key-here
```

Update `utils/constants.py` with your PlantUML JAR path:
```python
# For macOS/Linux
PLANTUML_JAR_PATH = os.path.expanduser("~/plantuml.jar")

# For Windows
PLANTUML_JAR_PATH = os.path.expanduser("~\\plantuml.jar")
```

### 3. Frontend Setup

#### Install Node Dependencies
```bash
cd frontend
npm install
```

## Running the Application

### 1. Start the Backend
```bash
uvicorn main:app --reload
```

The backend will start at: `http://localhost:8000`

**Verify backend is running:**
- Open: `http://localhost:8000/docs`
- You should see the FastAPI Swagger documentation

### 2. Start the Frontend

In a new terminal:
```bash
cd frontend
npm run dev
```

The frontend will start at: `http://localhost:5173` (or another port if 5173 is taken)

### 3. Open the Application

Open your browser and go to: `http://localhost:5173`

## Usage

### Creating a New Diagram

1. **Start a conversation**: The app automatically creates a new thread on load
2. **Enter your requirements**: Type your diagram requirements in natural language
```
   Example: "Create a class diagram for a user management system with User, Role, and Profile entities"
```
3. **Select diagram type** (optional): Choose from class, sequence, component, etc.
4. **Upload files** (optional): Upload requirements documents
5. **Click Send**: Watch the real-time progress as your diagram is generated

### Updating an Existing Diagram

Simply send a follow-up message in the same thread:
```
Example: "Add a Payment entity with payment_id, amount, and status. User can have multiple Payments"
```

The system will automatically update the existing diagram instead of creating a new one.

### Creating Multiple Threads

Click **"+ New Thread"** in the sidebar to start a fresh conversation with no previous context.

### Providing Feedback

1. Click on any generated diagram
2. A modal will open showing the diagram
3. Rate the diagram (1-5 stars)
4. Optionally add text feedback
5. Click "Submit Feedback"

## Tech Stack

**Backend:**
- FastAPI - Web framework
- LangChain + OpenAI - LLM integration
- Pydantic - Data validation
- PlantUML - Diagram rendering

**Frontend:**
- React - UI framework
- Vite - Build tool
- Vanilla CSS - Styling
