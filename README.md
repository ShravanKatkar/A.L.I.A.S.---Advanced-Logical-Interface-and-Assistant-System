<div align="center">

<img src="frontend/public/logo.png" alt="ALIAS Logo" width="120" height="120" style="border-radius:50%"/>

# A.L.I.A.S.
### Advanced Logical Interface and Assistant System

*A powerful, voice-activated AI desktop assistant with persistent memory and multi-model intelligence.*

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![Electron](https://img.shields.io/badge/Electron-40-47848F?style=for-the-badge&logo=electron&logoColor=white)](https://electronjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![SQLite](https://img.shields.io/badge/SQLite-Local%20DB-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

</div>

---

## 📖 Overview

**ALIAS** is a feature-rich AI desktop assistant that runs natively on Windows as an Electron app. Unlike cloud-only assistants, ALIAS runs a local Python backend that gives it real system access — it can open apps, control media, manage files, read your active window, and even generate AI images.

With **persistent chat history** and an **intelligent long-term memory system**, ALIAS behaves like a true personal AI — it learns who you are across sessions and uses that context to personalize every response. You can chat with it over text or voice, switch between multiple state-of-the-art AI models on the fly, and have it remember important facts about you forever.

---

## ✨ Features

### 🧠 Intelligence & Memory
| Feature | Description |
|---|---|
| **Persistent Chat History** | Every conversation is saved to a local SQLite database. Sessions survive restarts. |
| **ChatGPT-style Sidebar** | Browse, open, rename, and delete past chats from a sleek history panel. |
| **Keyword History Search** | Filter past conversations in real time from the sidebar search bar. |
| **Long-Term Memory Extraction** | ALIAS automatically extracts personal facts (name, skills, projects, goals) from your conversations using Gemini and stores them. |
| **Proactive Context Injection** | Before every response, ALIAS loads your memories and relevant past chat excerpts and prepends them to the LLM system prompt. |
| **Memory Management Dashboard** | View and delete individual memories at any time from the **Memory** tab in Settings. |
| **Natural Memory Commands** | Tell ALIAS to remember, forget, or update facts in plain English. |

### 🤖 AI & Models
| Feature | Description |
|---|---|
| **Multi-Model Support** | Switch between Gemini, GPT-4o, DeepSeek, Groq Llama, and Qubrid GPT-OSS live from the sidebar. |
| **Creativity Slider** | Real-time temperature control (0.0 – 1.0) for precise vs. creative responses. |
| **Markdown Rendering** | AI output is rendered with full GFM markdown — tables, code blocks, bold, lists. |
| **Syntax Highlighting** | Code responses use VS Code dark theme highlighting with one-click copy. |
| **Mermaid Diagrams** | Ask for architecture diagrams and ALIAS renders them inline. |
| **Strict Formatting Mode** | Enforced "no asterisk" policy and dash-only bullet points for cleaner tech output. |

### 🎨 Image Generation
| Feature | Description |
|---|---|
| **AI Image Generation** | Trigger image generation with natural language: *"Generate an image of a futuristic city."* |
| **Custom Dimensions** | Specify width and height for generated images via the Image Generation modal. |
| **Model Selection** | Choose between `flux`, `turbo`, and other AI Horde models. |
| **Inline Preview** | Generated images are served from the local backend and rendered directly in chat. |

### 🖥️ Desktop Control
| Feature | Description |
|---|---|
| **App Launcher** | Open any application: *"Open Chrome"*, *"Open Calculator"*. |
| **Media Control** | Play, pause, skip tracks system-wide. |
| **File Search & Open** | Search for files by name and auto-open them. |
| **Window Awareness** | ALIAS reads your active window title to provide context-aware answers. |
| **Email Sending** | Send emails directly via Gmail using a simple voice command. |

### 🎤 Voice & Speech
| Feature | Description |
|---|---|
| **Speech-to-Text** | System microphone STT via Python backend. |
| **Text-to-Speech** | High-quality Edge TTS neural voices (online). |
| **Voice Selection** | Switch between Christopher (Male) and Nova (Female) from Settings. |
| **Stop Speaking** | Immediately silence ALIAS mid-speech with the Stop button. |

### 🎨 UI & Customization
| Feature | Description |
|---|---|
| **Dark / Light / System Theme** | Full theme switching with Tailwind CSS dark mode. |
| **Responsive Layout** | Collapsible sidebar for focus mode on smaller screens. |
| **Glassmorphism Design** | Premium blur effects, smooth animations via Framer Motion. |
| **Real-time Streaming Feel** | Instant UI updates via Socket.IO WebSocket events. |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Electron Desktop App                         │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                     React Frontend (Vite)                     │   │
│  │  ┌─────────────┐  ┌──────────────────┐  ┌────────────────┐  │   │
│  │  │  Sidebar    │  │   Chat Window     │  │  Settings      │  │   │
│  │  │  - History  │  │   - Messages      │  │  - Theme       │  │   │
│  │  │  - Search   │  │   - Markdown      │  │  - Voice       │  │   │
│  │  │  - Rename   │  │   - Code Blocks   │  │  - Memory      │  │   │
│  │  │  - Delete   │  │   - Image Preview │  │    Dashboard   │  │   │
│  │  └─────────────┘  └──────────────────┘  └────────────────┘  │   │
│  └──────────────────────────┬───────────────────────────────────┘   │
│                             │ Socket.IO (WebSocket)                   │
└─────────────────────────────┼───────────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────────┐
│                   Python Backend (FastAPI + Uvicorn)                  │
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐   │
│  │   main.py    │  │ processor.py │  │       llm.py             │   │
│  │              │  │              │  │                          │   │
│  │ Socket.IO    │  │ - Route cmds │  │ - Gemini 2.5 Flash/Pro   │   │
│  │ Events:      │──│ - Load ctx   │  │ - GPT-4o                 │   │
│  │ process_text │  │ - Save msgs  │  │ - DeepSeek R1            │   │
│  │ get_convs    │  │ - Apply mem  │  │ - Groq Llama 3.3         │   │
│  │ get_conv     │  │ - Image gen  │  │ - Qubrid GPT-OSS 120B    │   │
│  │ rename/del   │  └──────────────┘  │ - Memory Extraction      │   │
│  │ get_memories │                    └──────────────────────────┘   │
│  └──────────────┘                                                     │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                   history_memory.py (SQLite)                  │   │
│  │   conversations │ messages │ memories │ users                 │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  ┌──────────┐  ┌──────────┐  ┌───────────────┐  ┌──────────────┐   │
│  │  tts.py  │  │  stt.py  │  │ app_control.py│  │image_gen.py  │   │
│  │ Edge-TTS │  │ PyAudio  │  │ System Control│  │ AI Horde API │   │
│  └──────────┘  └──────────┘  └───────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🗂️ Project Structure

```
Alias2.0/
├── run_alias.bat              # One-click launcher
├── README.md
├── .gitignore
│
├── backend/
│   ├── main.py                # FastAPI app + Socket.IO event handlers
│   ├── requirements.txt       # Python dependencies
│   ├── .env                   # API keys (not committed)
│   ├── .env.example           # Template for .env setup
│   │
│   ├── core/
│   │   ├── auth.py            # User registration, login, password hashing
│   │   ├── history_memory.py  # SQLite CRUD: conversations, messages, memories
│   │   ├── llm.py             # LLM routing (Gemini, GPT, DeepSeek, Groq, Qubrid)
│   │   ├── processor.py       # Command routing, context injection, memory pipeline
│   │   ├── tts.py             # Edge-TTS neural text-to-speech
│   │   └── stt.py             # PyAudio speech recognition
│   │
│   └── modules/
│       ├── app_control.py     # Open apps, control media playback
│       ├── file_ops.py        # File search and open
│       ├── window_awareness.py# Read active window title
│       └── email_ops.py       # Send emails via Gmail SMTP
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── electron/
│   │   └── main.js            # Electron shell
│   │
│   └── src/
│       ├── App.jsx            # Main application: chat, sidebar, history, state
│       ├── main.jsx           # React entry point
│       ├── index.css          # Global styles + Tailwind theme
│       │
│       └── components/
│           ├── Auth.jsx       # Login & registration forms
│           ├── SettingsModal.jsx # Theme, voice, memory management
│           └── ImageModal.jsx # AI image generation controls
│
└── friday/
    ├── image_generator.py     # AI Horde image generation engine
    ├── main.py                # CLI image generation entry point
    └── requirements.txt
```

---

## 🚀 Quick Start

### Prerequisites

- **OS**: Windows 10 / 11
- **Node.js**: v18+ and npm
- **Python**: 3.10 or higher
- **Git**

### 1. Clone the Repository

```bash
git clone https://github.com/ShravanKatkar/A.L.I.A.S.---Advanced-Logical-Interface-and-Assistant-System.git
cd A.L.I.A.S.---Advanced-Logical-Interface-and-Assistant-System
```

### 2. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Frontend Setup

```bash
cd frontend

# Install Node.js dependencies
npm install
```

### 4. Configure API Keys

Create a `.env` file inside the `backend/` directory:

```env
# Required — powers the core AI and memory extraction
GEMINI_API_KEY=your_gemini_api_key

# Optional — unlocks additional models
OPENAI_API_KEY=your_openai_or_github_models_key
DEEPSEEK_API_KEY=your_deepseek_key
GROQ_API_KEY=your_groq_key
QUBRID_API_KEY=your_qubrid_key

# Optional — for email sending
EMAIL_ADDRESS=your_gmail@gmail.com
EMAIL_PASSWORD=your_gmail_app_password
```

> **Get a free Gemini API key** at [Google AI Studio](https://aistudio.google.com/app/apikey)
> **Get a free Groq key** at [console.groq.com](https://console.groq.com)
> **Get a free Qubrid key** at [platform.qubrid.com](https://platform.qubrid.com)

### 5. Launch ALIAS

**Option A — One Click (Recommended):**
```
Double-click run_alias.bat
```

**Option B — Manual (for development):**
```bash
# Terminal 1: Start backend
cd backend
venv\Scripts\activate
python main.py

# Terminal 2: Start frontend
cd frontend
npm run electron:dev
```

---

## 🤖 Supported AI Models

| Model | Provider | Best For |
|---|---|---|
| `gemini-2.5-flash` | Google | Fast, everyday tasks *(default)* |
| `gemini-2.5-pro` | Google | Complex reasoning & analysis |
| `gemini-2.0-flash` | Google | Balanced speed and quality |
| `gpt-4o` | OpenAI / GitHub Models | General purpose |
| `deepseek-chat` | DeepSeek | Coding & technical tasks |
| `deepseek-reasoner` | DeepSeek | Step-by-step problem solving |
| `groq/llama-3.3-70b-versatile` | Groq | Ultra-fast inference |
| `openai/gpt-oss-120b` | Qubrid | High-capacity open model |

> Switch models at any time using the **Intelligence** dropdown in the sidebar — no restart required.

---

## 🧠 How Memory Works

ALIAS uses a **3-stage memory pipeline** powered by Gemini:

```
User sends message
       │
       ▼
┌─────────────────────────────────────────┐
│  STAGE 1: Context Loading (Pre-Gen)      │
│                                          │
│  • Load all stored memories for user     │
│  • Extract keywords from the message     │
│  • Search past conversations for matches │
│  • Prepend memories + past excerpts to   │
│    LLM system prompt                     │
└─────────────────────────────────────────┘
       │
       ▼
   LLM generates response
       │
       ▼
┌─────────────────────────────────────────┐
│  STAGE 2: Message Saving                 │
│  • Save user message to `messages` table │
│  • Save AI response to `messages` table  │
└─────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  STAGE 3: Memory Extraction (Post-Gen)   │
│                                          │
│  Gemini analyzes the conversation and    │
│  outputs a JSON list of operations:      │
│                                          │
│  [{"action": "add",    "fact": "..."},   │
│   {"action": "update", "id": 2,          │
│               "fact": "..."},            │
│   {"action": "delete", "id": 5}]         │
│                                          │
│  ALIAS applies these to the DB silently  │
└─────────────────────────────────────────┘
```

### Memory Commands (Natural Language)

| Intent | Example |
|---|---|
| Store a fact | *"Remember that I'm studying B.Sc Computer Science."* |
| Update a fact | *"Actually I'm now studying M.Sc AI."* |
| Recall memories | *"What do you remember about me?"* |
| Forget a fact | *"Forget that I use Windows."* |
| Search past chats | *"What did we discuss about Python last time?"* |

---

## 🗂️ Chat History Panel

The left sidebar gives you full control over your conversation history:

- **New Chat** — starts a fresh session (resets current conversation ID)
- **Conversation List** — shows all past chats sorted by most recently active
- **Click to Open** — loads the full message history of a past conversation
- **Rename** — click the ✏️ icon, type, and press Enter to rename
- **Delete** — click the 🗑️ icon to permanently delete a chat and its messages
- **Search** — real-time filter by conversation title

---

## ⚙️ Settings

Open the **Settings** panel from the bottom of the sidebar:

| Tab | Options |
|---|---|
| **General** | Switch between Dark / Light / System theme |
| **Voice** | Choose between Christopher (Male) or Nova (Female) neural TTS voices |
| **Memory** | View all stored facts about you; hover any fact and click 🗑️ to delete it |

---

## 💬 Example Interactions

```
You:    "My name is Shravan and I'm a 3rd year CS student."
ALIAS:  "Got it Shravan! I'll remember that."
        → Saved: "User's name is Shravan, 3rd year CS student."

You:    "What projects should I build for my portfolio?"
ALIAS:  "[Uses context: Shravan is a 3rd year CS student]
         Here are some great portfolio ideas for a CS student..."

--- New conversation, days later ---

You:    "Help me write a resume."
ALIAS:  "[Uses stored memory]
         Sure Shravan! Since you're in your 3rd year of CS,
         here's how to structure your student resume..."
```

---

## 🛠️ Development

### Run Backend Only (API mode)
```bash
cd backend
venv\Scripts\activate
uvicorn main:socket_app --host 0.0.0.0 --port 8000 --reload
```

### Run Frontend Only (browser mode)
```bash
cd frontend
npm run dev
# Open http://localhost:5173
```

### Run Diagnostics
```bash
cd backend
venv\Scripts\activate
python diagnose.py
```

### Build Production Electron App
```bash
cd frontend
npm run electron:build
```

---

## 📦 Dependencies

### Backend (`requirements.txt`)
| Package | Purpose |
|---|---|
| `fastapi` + `uvicorn` | ASGI web server & REST API |
| `python-socketio` | Real-time WebSocket event system |
| `google-generativeai` | Gemini LLM API |
| `openai` | OpenAI, Groq, DeepSeek, Qubrid API client |
| `edge-tts` + `pygame` | Neural text-to-speech playback |
| `SpeechRecognition` + `pyaudio` | Microphone speech-to-text |
| `python-dotenv` | Environment variable loading |
| `pyautogui` + `pygetwindow` | Desktop control & window awareness |
| `langchain` + `chromadb` | RAG pipeline (document Q&A) |

### Frontend (`package.json`)
| Package | Purpose |
|---|---|
| `react` + `vite` | UI framework & build tool |
| `electron` | Desktop app shell |
| `socket.io-client` | WebSocket client |
| `framer-motion` | Smooth animations |
| `react-markdown` + `rehype-raw` | Markdown rendering |
| `react-syntax-highlighter` | Code syntax highlighting |
| `lucide-react` | Icon library |
| `tailwindcss` | Utility-first CSS framework |

---

## 🗺️ Roadmap

- [ ] Streaming token-by-token responses
- [ ] RAG Document Q&A (upload PDFs, DOCX, and query them)
- [ ] Plugin system for custom skills
- [ ] Cross-platform support (macOS, Linux)
- [ ] Multiple user profiles
- [ ] Voice wake word detection ("Hey ALIAS")
- [ ] Calendar & reminder integration
- [ ] Web search tool integration

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m "feat: add my feature"`
4. Push to the branch: `git push origin feature/my-feature`
5. Open a Pull Request

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Built by [Shravan Katkar](https://github.com/ShravanKatkar)**

⭐ **Star this repo if you find it useful!** ⭐

</div>
