# Project Aether: The Self-Evolving Digital Twin
**Vision:** A persistent, autonomous agent that controls the host OS, learns from user demonstrations, and manages the user's digital life.

---

## 1. System Capabilities
- **Proactive Engagement:** Greets the user on boot-up and suggests tasks based on time/day.
- **Learning by Demonstration:** A "Teach" mode where the agent records browser steps to automate new sites (like Brightspace).
- **System Command Center:** Full control over Spotify, Browser, File System, and System Volume.
- **Recursive Memory:** Not just mistakes, but a "Knowledge Graph" of the user's preferences, routines, and relationships.

## 2. Technical Architecture
### A. The "Vibe" Interface (The Shell)
- A dedicated Python GUI (using CustomTkinter or a web-based Streamlit local dash) that replaces the terminal.
- Always-on "Ear" (Whisper) waiting for the "Aether" wake-word.

### B. The Action Engine (The Hands)
- **Browser Automation:** Using Playwright or Selenium to log into Brightspace, check grades, and navigate YouTube.
- **OS Integration:** Using `pyautogui` and `os` libraries to control Spotify and system apps.

### C. The Neural Memory (The Soul)
- **Persistent RAG:** Obsidian vault acting as the Long-Term Memory (LTM).
- **Dynamic Context:** The agent pulls "Yesterday's Context" every morning to know where you left off.

## 3. Technology Stack (Expanded)
| Layer | Tech | Purpose |
| :--- | :--- | :--- |
| **Cognition** | Ollama (Llama 3.2 3B/8B) | Reasoning and Logic |
| **Automation** | Playwright / PyAutoGUI | Browsing & OS Control |
| **Memory** | Obsidian / ChromaDB | Long-term knowledge storage |
| **Voice** | OpenAI Whisper / Piper | Hands-free communication |
| **Trigger** | Windows Task Scheduler | Boot-time initialization |

---

## 4. The Roadmap to "Total Agent"
### Phase 1: The Foundation (Current)
- Establish Tool-Calling (JSON to Action).
- Connect Obsidian Memory.
- Fix Identity (AI knows it is Aether, the User is Adithya).

### Phase 2: The Browser "Eyes"
- Integrate Playwright so Aether can "Log in" to sites.
- Teach Aether how to navigate Carleton Brightspace.

### Phase 3: The Presence
- Build the "Startup Greeting" script.
- Implement the "Teach Mode" for custom actions.

### Phase 4: Full Autonomy
- Aether starts suggesting actions ("I see you have an assignment due at 11:59 PM, shall I open your notes?").