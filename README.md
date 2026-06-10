# ALIAS 2.0 - AI Desktop Assistant

ALIAS is a powerful, voice-activated AI assistant designed to control your Windows desktop, analyze context, and assist with coding and daily tasks. It features a modern Electron-based frontend and a robust Python backend powered by advanced LLMs (Gemini, OpenAI, Groq, DeepSeek).

## 🚀 Key Features

*   **Voice Control**: Hands-free interaction using efficient Speech-to-Text (STT) and high-quality Text-to-Speech (TTS).
*   **Desktop App**: Runs as a standalone application using Electron.
*   **Multi-Model Intelligence**: Seamlessly switch between Gemini 2.0, OpenAI GPT-4o, DeepSeek R1, Groq Llama 3.3, and Qubrid GPT-OSS.
*   **Persistent Chat History**: Conversations are automatically saved to a local SQLite database. View, continue, rename, delete, or search past chats from a ChatGPT-style sidebar history panel.
*   **Intelligent Long-Term Memory**: ALIAS automatically extracts and remembers important facts about you (e.g., name, education, skills, preferences, projects) across conversations. It injects relevant facts and past chat logs as context for future prompts.
*   **Memory Management Dashboard**: Complete control over what ALIAS remembers. View and delete learned facts directly from the **Memory** tab under Settings.
*   **Context Awareness**: Can "see" what window you are focusing on (e.g., VS Code, Browser) to provide relevant answers.
*   **System Control**: Open applications, control media playback (Play/Pause/Next), and manage files.
*   **Strict Coding Mode**: Technical output is formatted in clean Console-style blocks with syntax highlighting and NO markdown asterisks (`*`) for cleaner readability.
*   **Custom Persona**: Responds with a personalized greeting ("Hey Shravan...") and respects strict behavioral rules.

## 🛠️ Tech Stack

*   **Frontend**: React, Vite, Electron, TailwindCSS, Socket.IO Client.
*   **Backend**: Python, FastAPI, Socket.IO Server, SQLite, PyAudio, Edge-TTS.
*   **AI Models**: Google Gemini (powering core intelligence & memory extraction), OpenAI, Groq, DeepSeek, Qubrid.

## 📦 Installation

### Prerequisites
*   Node.js & npm
*   Python 3.10+
*   Virtual Environment (Recommended)

### Setup

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/yourusername/alias-2.0.git
    cd alias-2.0
    ```

2.  **Backend Setup**
    ```bash
    cd backend
    python -m venv venv
    venv\Scripts\activate
    pip install -r requirements.txt
    ```

3.  **Frontend Setup**
    ```bash
    cd frontend
    npm install
    # Note: Install Electron deps if needed
    npm install electron electron-builder --save-dev
    ```

4.  **Environment Configuration**
    Create a `.env` file in the `backend/` directory with your API keys:
    ```env
    GEMINI_API_KEY=your_key
    OPENAI_API_KEY=your_key
    GROQ_API_KEY=your_key
    DEEPSEEK_API_KEY=your_key
    QUBRID_API_KEY=your_key
    ```

## 🚀 Usage

**One-Click Launcher**:
Simply run the `run_alias.bat` file in the root directory.
*   It automatically starts the Python backend.
*   It launches the Electron desktop interface.
*   It handles cleanup of old processes.

### Voice/Text Commands for Memory
*   **"Remember that my favorite programming language is Python."** - Learns and saves the fact.
*   **"What do you remember about me?"** - ALIAS returns the relevant facts it has stored.
*   **"Forget my college details."** - Deletes the matching fact from memory.

### Voice Commands
*   **"Hello"**: Triggers custom greeting ("Hey Shravan...").
*   **"Open [App Name]"**: Opens applications (e.g., "Open Calculator").
*   **"Play Music" / "Pause"**: Controls system media.
*   **"Stop"**: Click the Red Square button in the UI to stop ALIAS from speaking.

## 🎨 Customization

*   **Creativity Slider**: Adjust the slider (Red) to control AI temperature.
*   **Voice Settings**: Toggle between Male/Female voices in Settings.
*   **Theme**: System-aware Light/Dark mode.

## 📝 Recent Updates
*   **Persistent Chat History Sidebar**: Restructured navigation panel supporting recent chats with inline renaming and deletion.
*   **Intelligent Memory Extraction**: Dynamic background processing pipeline powered by Gemini that detects facts and manages database records.
*   **Memory Management Tab**: User dashboard added inside settings to display and prune learned memories.
*   **Desktop Mode**: Switched from Browser to Electron.
*   **UI Polish**: Red accent slider, Console-style code blocks.
*   **Stop Button**: Immediate TTS interruption.

---
**Author**: Shravan
