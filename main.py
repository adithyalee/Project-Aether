"""
main.py — Aether Executive Agent
LLM   : Google Gemini 2.0 Flash (free) with Ollama phi4-mini offline fallback
Memory: mem0 (auto-extracts facts) + Obsidian vault (skills/logs)
Voice : faster-whisper STT + Kokoro TTS
Tools : web search (DuckDuckGo), open URL, play music, OS control
"""
import asyncio
import time
import os
import re
import sys
import logging
import warnings
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()   # reads .env before anything else

os.environ["PYTHONWARNINGS"] = "ignore"
warnings.filterwarnings("ignore")
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("OLLAMA_INTEL_GPU", "1")
os.environ.setdefault("OLLAMA_VULKAN", "1")
os.environ.setdefault("OLLAMA_HOST", "http://localhost:11434")

try:
    import ollama
except ImportError:
    ollama = None

from brain.memory_manager import MemoryManager, VAULT_BASE
from tools.pc_controls import TOOL_MAP
from brain.semantic_matcher import find_best_skill

# RAG is optional — on low-end hardware without txtai, run without semantic cache
try:
    from brain.rag_engine import check_cache, query, add_to_cache, index_vault, clear_cache
    RAG_OK = True
except Exception as _e:
    print(f"[RAG] Disabled ({_e.__class__.__name__}) — running without semantic cache.")
    RAG_OK = False
    async def check_cache(question, **kw): return None
    async def query(question, **kw): return []
    async def add_to_cache(question, answer): pass
    async def index_vault(): return 0
    async def clear_cache(): pass

IDENTITY_FILE  = os.path.join(VAULT_BASE, "Identity.md")
WINDOW_SIZE    = 15
FALLBACK_MODEL = "phi4-mini"

# Gemini key rotation — tries KEY_1, KEY_2, KEY_3, then falls back to Ollama
GEMINI_KEYS = [
    k for k in [
        os.environ.get("GEMINI_API_KEY_1"),
        os.environ.get("GEMINI_API_KEY_2"),
        os.environ.get("GEMINI_API_KEY_3"),
    ] if k and k.strip()
]
_gemini_key_index = 0   # tracks which key we're currently using


# ── Helpers ────────────────────────────────────────────────────────────────────
def _gpu_active() -> bool:
    return os.environ.get("OLLAMA_INTEL_GPU", "0") == "1"


async def sync_identity() -> str:
    try:
        content = await asyncio.to_thread(
            Path(IDENTITY_FILE).read_text, encoding="utf-8", errors="replace"
        )
        if content.strip():
            return content.strip()
    except FileNotFoundError:
        pass
    return (
        "## Adithya Thaninki\n"
        "- University: Carleton (previously VELTECH)\n"
        "- Work: TCS, Statistics Canada\n"
        "- Interests: AI, music, automation"
    )


# ── Tools the LLM can call ─────────────────────────────────────────────────────
def search_web(query: str) -> str:
    """Search the web for current information, news, or anything not in training data."""
    try:
        from duckduckgo_search import DDGS
        results = DDGS().text(query, max_results=3)
        if not results:
            return "No results found."
        return "\n".join(f"- {r['title']}: {r['body'][:200]}" for r in results)
    except Exception as e:
        return f"Search failed: {e}"


def get_disk_space() -> str:
    """Check available disk space on C: drive."""
    import shutil
    total, used, free = shutil.disk_usage("C:")
    return f"C: drive — Total: {total//2**30}GB, Used: {used//2**30}GB, Free: {free//2**30}GB"


def get_current_time() -> str:
    """Get the current date and time."""
    import datetime
    return datetime.datetime.now().strftime("%A, %B %d %Y — %I:%M %p")


# Tools available to the LLM (Gemini function-calling format auto-inferred from docstrings)
LLM_TOOLS = [search_web, get_disk_space, get_current_time]
LLM_TOOL_MAP = {fn.__name__: fn for fn in LLM_TOOLS}


# ── System prompts ─────────────────────────────────────────────────────────────
def _build_personal_prompt(identity: str) -> str:
    return (
        "You are Aether, the private AI assistant built exclusively for Adithya Thaninki (call him Adi).\n\n"
        "== IDENTITY ==\n"
        f"{identity}\n\n"
        "== STRICT RULES ==\n"
        "1. ONE or TWO sentences max. Never write more.\n"
        "2. NEVER pretend you executed an action. You cannot play music or open apps — "
        "the system handles that separately via keyword routing.\n"
        "3. If the input is vague (e.g. 'do it again'), ask ONE specific clarifying question.\n"
        "4. Use your tools (search_web, get_current_time) when you need live information.\n"
        "5. No emojis, no sign-offs, no 'Is there anything else'.\n\n"
        "== EXAMPLES ==\n"
        "Q: Where did I work?   → A: TCS then Statistics Canada, Adi.\n"
        "Q: Do it again.        → A: Do what again?\n"
        "Q: What's the weather? → A: [call search_web]\n"
    )


def _build_work_prompt(identity: str) -> str:
    return (
        "You are Aether in WORK MODE — a senior Software Engineering Mentor for Adithya Thaninki.\n\n"
        "== PROFILE ==\n"
        f"{identity}\n\n"
        "== RULES ==\n"
        "1. Structured, professional answers — bullets and code blocks where relevant.\n"
        "2. Practical advice with trade-offs, no fluff.\n"
        "3. NEVER pretend to execute an action.\n"
        "4. Use search_web for current docs, Stack Overflow answers, or version info.\n"
        "5. Max 5 sentences unless explaining code.\n"
    )


# ── Instant replies (no LLM) ───────────────────────────────────────────────────
_GREETING_PATTERNS = [
    "hi", "hello", "hey", "how are you", "good morning", "good night",
    "thanks", "thank you", "bye", "goodbye", "ok", "okay", "sure"
]
_INSTANT_REPLIES = {
    "hi": "Hey Adi.", "hello": "Hey.", "hey": "What's up?",
    "how are you": "Running smooth. What do you need?",
    "good morning": "Morning, Adi. What are we doing today?",
    "good night": "Night, Adi.",
    "thanks": "Anytime.", "thank you": "Anytime.",
    "bye": "Later, Adi.", "goodbye": "Goodbye, Adi.",
    "ok": "Got it.", "okay": "Got it.", "sure": "On it.",
}
_REPEAT_PATTERNS = {
    "do it again", "again", "repeat that", "one more time",
    "same thing", "that again", "play it again", "replay"
}
_ROUTE_MAP = {
    "greeting":      {"hi", "hello", "hey", "sup", "good morning", "good night",
                      "how are you", "what's up", "hey aether"},
    "clear_cache":   {"clear cache", "reset cache", "wipe cache", "clear memory"},
    "work_mode":     {"switch to work mode", "work mode on", "enable work mode"},
    "personal_mode": {"switch to personal mode", "work mode off", "personal mode"},
}


def _keyword_route(text: str) -> str | None:
    t = text.lower().strip()
    for route, phrases in _ROUTE_MAP.items():
        if t in phrases:
            return route
    return None


# ── Agent ──────────────────────────────────────────────────────────────────────
class AetherAgent:

    def __init__(self):
        self.memory     = MemoryManager()
        self.work_mode  = False
        self.identity   = ""
        self.session_messages: list = []
        self._turn_count = 0
        self.voice_mode  = False
        self.last_action: tuple | None = None
        self._tts        = None
        self._tts_ready  = False
        self._stt        = None
        self._gemini_model = None   # initialised lazily after identity loads

    # ── Initialise ─────────────────────────────────────────────────────────────
    async def initialize(self):
        self.identity = await sync_identity()
        self._rebuild_system_prompt()
        print("[Aether] Ready. GPU:", _gpu_active())
        asyncio.create_task(self._preload_stt())
        asyncio.create_task(self._preload_tts())

    async def _preload_stt(self):
        try:
            from stt.whisper_stt import AetherSTT
            self._stt = await asyncio.to_thread(AetherSTT)
        except Exception as e:
            print(f"[STT] Preload error: {e}")

    async def _preload_tts(self):
        try:
            from tts.kokoro_tts import AetherTTS
            self._tts = await asyncio.to_thread(AetherTTS)
        except Exception:
            self._tts = None
        self._tts_ready = True

    def _get_gemini(self):
        if self._gemini_model:
            return self._gemini_model
        key = self._next_gemini_key()
        if not key:
            return None
        try:
            import google.generativeai as genai
            genai.configure(api_key=key)
            system = (
                _build_work_prompt(self.identity)
                if self.work_mode
                else _build_personal_prompt(self.identity)
            )
            self._gemini_model = genai.GenerativeModel(
                "gemini-2.0-flash",
                tools=LLM_TOOLS,
                system_instruction=system,
            )
            print("[LLM] Gemini 2.0 Flash ready.")
        except Exception as e:
            print(f"[LLM] Gemini init failed: {e}")
        return self._gemini_model

    # ── System prompt ──────────────────────────────────────────────────────────
    def _rebuild_system_prompt(self):
        prompt = (
            _build_work_prompt(self.identity)
            if self.work_mode
            else _build_personal_prompt(self.identity)
        )
        if self.session_messages and self.session_messages[0]['role'] == 'system':
            self.session_messages[0] = {'role': 'system', 'content': prompt}
        else:
            self.session_messages.insert(0, {'role': 'system', 'content': prompt})
        # Reset Gemini model so it picks up the new system prompt
        self._gemini_model = None

    # ── Sliding window ─────────────────────────────────────────────────────────
    async def _prune_context(self):
        system     = [m for m in self.session_messages if m['role'] == 'system']
        non_system = [m for m in self.session_messages if m['role'] != 'system']
        if len(non_system) > WINDOW_SIZE:
            non_system = non_system[-WINDOW_SIZE:]
        self.session_messages = system + non_system

    # ── LLM call (Gemini primary, Ollama fallback) ─────────────────────────────
    async def _call_llm(self, user_prompt: str) -> str:
        gemini = self._get_gemini()

        # Try each Gemini key in order, rotate on rate-limit (429) or quota errors
        while _gemini_key_index < len(GEMINI_KEYS):
            gemini = self._get_gemini()
            if not gemini:
                break
            try:
                return await self._call_gemini(gemini, user_prompt)
            except Exception as e:
                err = str(e).lower()
                if any(x in err for x in ["429", "quota", "exhausted", "rate", "expired", "invalid"]):
                    self._rotate_gemini_key()
                else:
                    print(f"[LLM] Gemini error: {e}")
                    break

        # All keys exhausted or errored — use local Ollama
        print("[LLM] Using Ollama (offline fallback)")
        try:
            return await self._call_ollama(user_prompt)
        except Exception as e:
            return f"LLM unavailable ({e.__class__.__name__}) — check .env Gemini keys or start Ollama."

    def _next_gemini_key(self) -> str | None:
        global _gemini_key_index
        if not GEMINI_KEYS:
            return None
        key = GEMINI_KEYS[_gemini_key_index % len(GEMINI_KEYS)]
        return key

    def _rotate_gemini_key(self):
        global _gemini_key_index
        _gemini_key_index += 1
        self._gemini_model = None  # force rebuild with next key
        if _gemini_key_index < len(GEMINI_KEYS):
            print(f"[LLM] Gemini key exhausted — switching to key {_gemini_key_index + 1}")
        else:
            print("[LLM] All Gemini keys exhausted — switching to Ollama")

    async def _call_gemini(self, model, user_prompt: str) -> str:
        import google.generativeai as genai

        # Convert session_messages (Ollama format) → Gemini history format
        history = []
        for m in self.session_messages:
            if m['role'] == 'system':
                continue
            role = "user" if m['role'] == 'user' else "model"
            history.append({"role": role, "parts": [m['content']]})

        chat = model.start_chat(history=history)

        # Stream first attempt
        print("\nAether: ", end="", flush=True)
        full_text = ""

        response = await asyncio.to_thread(
            chat.send_message, user_prompt, stream=True
        )
        for chunk in response:
            token = chunk.text or ""
            print(token, end="", flush=True)
            full_text += token

        # Handle tool calls — Gemini may pause streaming and request a function
        try:
            fc = response.candidates[0].content.parts[0].function_call
            if fc and fc.name in LLM_TOOL_MAP:
                print(f"\n[Tool] Calling {fc.name}...", flush=True)
                tool_result = await asyncio.to_thread(
                    LLM_TOOL_MAP[fc.name], **dict(fc.args)
                )
                # Feed tool result back and get final response
                follow_up = await asyncio.to_thread(
                    chat.send_message,
                    genai.protos.Content(parts=[
                        genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(
                                name=fc.name,
                                response={"result": tool_result}
                            )
                        )
                    ])
                )
                full_text = follow_up.text or full_text
                print(full_text)
        except (AttributeError, IndexError):
            pass  # no tool call, normal response

        print("\n")
        return full_text.strip()

    async def _call_ollama(self, user_prompt: str) -> str:
        if ollama is None:
            return "No LLM available — add a Gemini key to .env or install Ollama."
        options = {
            "num_ctx":    512 if len(user_prompt.split()) <= 6 else 1024,
            "num_thread": 4,
            "f16_kv":     True,
            "temperature": 0.3,
            "num_gpu":    32,
            "keep_alive": -1,
        }
        # Build full messages with current system prompt
        system = next((m['content'] for m in self.session_messages if m['role'] == 'system'), "")
        history = [m for m in self.session_messages if m['role'] != 'system']

        print("\nAether: ", end="", flush=True)
        full_res = ""
        client = ollama.AsyncClient()
        async for part in await client.chat(
            model=FALLBACK_MODEL,
            messages=[{'role': 'system', 'content': system}] + history,
            stream=True,
            options=options,
        ):
            token = part['message']['content']
            print(token, end="", flush=True)
            full_res += token
        print("\n")
        return full_res.strip()

    # ── TTS ────────────────────────────────────────────────────────────────────
    async def _speak(self, text: str):
        if not self.voice_mode or not self._tts_ready or not self._tts:
            return
        await asyncio.to_thread(self._tts.speak, text)

    async def _reply(self, text: str, t_start: float, log_input: str = ""):
        print(f"\nAether: {text}\n")
        await self._speak(text)
        if log_input:
            asyncio.create_task(self._background_log(log_input, text))
        self._perf_print(t_start)

    # ── Background memory write ────────────────────────────────────────────────
    async def _background_log(self, user_input: str, response: str):
        try:
            topic = self.memory._detect_topic(user_input)
            await asyncio.gather(
                self.memory.log_interaction(user_input, response, topic),
                self.memory.add_fact(user_input, response),   # mem0
                add_to_cache(user_input, response),
            )
        except Exception as e:
            print(f"[Memory] Background log error: {e}")

    # ── Mode toggles ───────────────────────────────────────────────────────────
    def _toggle_work_mode(self) -> str:
        self.work_mode = not self.work_mode
        self._rebuild_system_prompt()
        return (
            "Switched to WORK MODE — engineering mentor active."
            if self.work_mode
            else "Back to Personal Mode, Adi."
        )

    # ── Play / Open helpers ────────────────────────────────────────────────────
    async def _play_song(self, song: str) -> str:
        all_skills = self.memory.get_all_skills()
        best_name, best_url, score = find_best_skill(song, all_skills)
        if best_url and score > 0.8:
            import webbrowser
            webbrowser.open(best_url)
            self.last_action = ("play", song)
            return f"Playing {best_name}."
        try:
            from tools.pc_controls import get_direct_youtube_link
            import webbrowser
            link = get_direct_youtube_link(song)
            if link:
                webbrowser.open(link)
                self.last_action = ("play", song)
                await self.memory.save_new_skill(song, link)
                return f"Playing '{song}' — learned for next time."
        except Exception as e:
            print(f"[Play] {e}")
        return f"Couldn't find '{song}'."

    async def _open_with_resolution(self, raw: str) -> str:
        from tools.pc_controls import find_and_open_app
        local = find_and_open_app(raw)
        if local:
            self.last_action = ("open", raw)
            asyncio.create_task(self.memory.log_skill("open_app", raw))
            return f"Launched {raw}."
        all_skills = self.memory.get_all_skills()
        best_name, best_url, score = find_best_skill(raw, all_skills)
        if best_url:
            import webbrowser
            webbrowser.open(best_url)
            self.last_action = ("open", raw)
            return f"Opened {best_name}."
        return f"I don't know how to open {raw} yet."

    # ── Main chat ──────────────────────────────────────────────────────────────
    async def chat(self, user_input: str):
        t_start = time.perf_counter()
        clean   = user_input.lower().strip()
        route   = _keyword_route(user_input)

        # ── Hard intercepts (zero latency) ──────────────────────────────────
        if route == "clear_cache":
            await clear_cache()
            await self._reply("Cache wiped.", t_start)
            return

        if route == "work_mode":
            await self._reply(self._toggle_work_mode(), t_start)
            return

        if route == "personal_mode":
            msg = self._toggle_work_mode() if self.work_mode else "Already in Personal Mode."
            await self._reply(msg, t_start)
            return

        if clean in {"voice mode on", "enable voice", "speak to me"}:
            self.voice_mode = True
            await self._reply("Voice Mode enabled.", t_start)
            return

        if clean in {"voice mode off", "disable voice", "shut up"}:
            self.voice_mode = False
            await self._reply("Voice Mode disabled.", t_start)
            return

        if clean in {"reload identity", "sync identity"}:
            self.identity = await sync_identity()
            self._rebuild_system_prompt()
            await self._reply("Identity reloaded.", t_start)
            return

        # ── Teach mode: "teach spotify = open.spotify.com" ────────────────
        if clean.startswith("teach "):
            body = user_input[6:]
            if "=" in body:
                name, target = (s.strip() for s in body.split("=", 1))
                if target and not target.startswith("http") and "." in target:
                    target = "https://" + target
                if name and target:
                    await self.memory.save_new_skill(name, target)
                    await self._reply(f"Learned: say 'open {name}' and I'll open {target}.", t_start)
                    return
            await self._reply("Teach me like this: teach spotify = open.spotify.com", t_start)
            return

        # ── Instant greetings (no LLM) ────────────────────────────────────
        if route == "greeting" or (
            any(p in clean for p in _GREETING_PATTERNS) and len(clean.split()) < 5
        ):
            res = next((v for k, v in _INSTANT_REPLIES.items() if k in clean), "What do you need?")
            await self._reply(res, t_start)
            return

        # ── Repeat last action ────────────────────────────────────────────
        if any(p in clean for p in _REPEAT_PATTERNS):
            if self.last_action:
                kind, arg = self.last_action
                res = await self._play_song(arg) if kind == "play" else await self._open_with_resolution(arg)
            else:
                res = "What should I repeat? No previous action."
            await self._reply(res, t_start, user_input)
            return

        # ── Open / Play commands ──────────────────────────────────────────
        if clean.startswith("open "):
            primary = re.split(r'\s+(and|then|for|in|on)\s+', clean[5:])[0].strip()
            await self._reply(await self._open_with_resolution(primary), t_start, user_input)
            return

        if clean.startswith("play "):
            song = clean[5:].strip()
            await self._reply(await self._play_song(song) if song else "Which track?", t_start, user_input)
            return

        # ── Semantic cache ────────────────────────────────────────────────
        await self._prune_context()
        cached = await check_cache(user_input)
        if cached:
            print(f"\nAether (Cache): {cached}\n")
            await self._speak(cached)
            asyncio.create_task(self._background_log(user_input, cached))
            self._perf_print(t_start)
            return

        # ── Build context from mem0 + RAG ─────────────────────────────────
        topic = self.memory._detect_topic(user_input)
        mem_facts, rag_hits = await asyncio.gather(
            self.memory.get_memories(user_input),
            query(user_input, topic_filter=topic if topic != "General" else None),
        )
        ctx     = "\n---\n".join(h['text'][:200] for h in rag_hits)
        context = f"FACTS:\n{mem_facts}\n\nHISTORY:\n{ctx}" if mem_facts else f"HISTORY:\n{ctx}"
        prompt  = f"{context}\n\nUSER: {user_input}" if (ctx or mem_facts) else user_input

        self.session_messages.append({'role': 'user', 'content': prompt})

        # ── LLM call ──────────────────────────────────────────────────────
        full_res = await self._call_llm(prompt)

        self.session_messages.append({'role': 'assistant', 'content': full_res})
        self._turn_count += 1
        await self._speak(full_res)
        asyncio.create_task(self._background_log(user_input, full_res))
        self._perf_print(t_start)

    # ── Proactive startup greeting (blueprint Phase 3) ──────────────────────────
    def startup_greeting(self) -> str:
        import datetime
        hour = datetime.datetime.now().hour
        part = "morning" if hour < 12 else "afternoon" if hour < 18 else "evening"
        greet = f"Good {part}, Adi."
        try:
            lines = Path(self.memory.memory_log_path).read_text(
                encoding="utf-8", errors="replace"
            ).strip().splitlines()
            last = next((l for l in reversed(lines) if l.startswith("### ")), None)
            if last:
                greet += f" Last session: {last[4:].strip()}."
        except (FileNotFoundError, OSError):
            pass
        return greet

    # ── Voice loop ─────────────────────────────────────────────────────────────
    async def start_voice_loop(self):
        try:
            if self._stt is None:
                from stt.whisper_stt import AetherSTT
                self._stt = await asyncio.to_thread(AetherSTT)
            stt = self._stt
            self.voice_mode = True

            print("\n" + "=" * 50)
            print(" VOICE MODE — say 'Stop' or 'Done' to exit")
            print("=" * 50 + "\n")

            while True:
                voice_text = await asyncio.to_thread(stt.listen_and_transcribe, duration=6)
                if not voice_text or len(voice_text.strip()) < 2:
                    continue

                print(f"You (Voice): {voice_text}")
                _vt = voice_text.lower().strip().rstrip(".,!?")
                if any(x in _vt for x in ["done", "stop", "exit voice", "goodbye"]):
                    print("\nAether: Voice loop ended — back to text.\n")
                    if self._tts:
                        await asyncio.to_thread(self._tts.speak, "Goodbye Adi.")
                    break

                await self.chat(voice_text)

        except Exception as e:
            print(f"[Voice] Unavailable ({e}) — staying in text mode. "
                  "Install voice deps: pip install faster-whisper sounddevice kokoro-onnx")
        finally:
            self.voice_mode = False

    def _perf_print(self, t_start: float):
        print(f"[Perf] {time.perf_counter() - t_start:.2f}s | GPU: {_gpu_active()}\n")


# ── Entry point ────────────────────────────────────────────────────────────────
async def main():
    agent = AetherAgent()
    await agent.initialize()

    if RAG_OK:
        idx_path = os.path.join(os.path.dirname(__file__), ".txtai", "vault")
        if not os.path.exists(idx_path):
            print("[RAG] Initializing index...")
            await index_vault()

    print(f"\nAether: {agent.startup_greeting()}")
    print("(type to chat | 'voice mode on' for voice | 'exit' to quit)\n")

    if "--voice" in sys.argv:
        await agent.start_voice_loop()

    # Text REPL — works on any hardware, no mic needed
    while True:
        try:
            user = await asyncio.to_thread(input, "You: ")
        except (EOFError, KeyboardInterrupt):
            user = "exit"
        user = user.lstrip("﻿\xef\xbb\xbf").strip()  # piped stdin may carry a BOM (raw or decoded)
        if not user:
            continue
        if user.lower().rstrip(".!?") in {"exit", "quit", "shutdown"}:
            print("\nAether: Goodbye, Adi. Syncing memory...")
            await asyncio.to_thread(lambda: os.system("python memory_cli.py sync"))
            break
        if user.lower() in {"voice mode on", "enable voice", "start listening"}:
            await agent.start_voice_loop()
            continue
        await agent.chat(user)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nAether: Shutdown forced. Goodbye, Adithya!")
        sys.exit(0)
