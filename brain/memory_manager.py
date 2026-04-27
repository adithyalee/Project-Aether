"""
brain/memory_manager.py

Two-layer memory architecture:
  - mem0 (conversational memory): automatically extracts and deduplicates facts
    from every conversation. Powered by Gemini + ChromaDB.
  - Obsidian vault (skills memory): URL/app mappings you teach Aether, written
    as human-readable markdown you can edit directly in Obsidian.
"""
import datetime
import os
import json
import re
import asyncio
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

VAULT_BASE = os.environ.get("VAULT_BASE", str(Path(__file__).parent.parent / "vault"))


class MemoryManager:

    def __init__(self):
        self.mistakes_path       = os.path.join(VAULT_BASE, "Mistakes.md")
        self.learned_skills_path = os.path.join(VAULT_BASE, "Learned_Skills.md")
        self.predefined_skills_path = os.path.join(VAULT_BASE, "Predefined_Skills.md")
        self.memory_log_path     = os.path.join(VAULT_BASE, "Memory_Log.md")
        self._mem0 = None   # lazy-initialised on first use

    # ── mem0 init ─────────────────────────────────────────────────────────────
    def _get_mem0(self):
        if self._mem0 is not None:
            return self._mem0
        try:
            from mem0 import Memory
            gemini_key = os.environ.get("GEMINI_API_KEY")
            chroma_path = str(Path(__file__).parent.parent / ".chroma_db")

            config = {
                "llm": {
                    "provider": "ollama",
                    "config": {
                        "model": "phi4-mini",
                        "ollama_base_url": "http://localhost:11434",
                        "temperature": 0.1,
                    }
                },
                "embedder": {
                    "provider": "huggingface",
                    "config": {
                        "model": "sentence-transformers/all-MiniLM-L6-v2"
                    }
                },
                "vector_store": {
                    "provider": "chroma",
                    "config": {
                        "collection_name": "aether_memory",
                        "path": chroma_path,
                    }
                },
                "history_db_path": str(Path(__file__).parent.parent / ".mem0_history.db"),
            }
            self._mem0 = Memory.from_config(config)
            print("[Memory] mem0 ready (Gemini + ChromaDB)")
        except Exception as e:
            print(f"[Memory] mem0 unavailable: {e}")
        return self._mem0

    # ── Conversational memory (mem0) ──────────────────────────────────────────
    async def add_fact(self, user_input: str, response: str, user_id: str = "adithya"):
        """
        Passes the conversation turn to mem0, which uses Gemini to extract
        facts and store only what is worth remembering — no duplicates.
        """
        def _add():
            m = self._get_mem0()
            if m is None:
                return
            m.add(
                [
                    {"role": "user",      "content": user_input},
                    {"role": "assistant", "content": response},
                ],
                user_id=user_id,
            )
        try:
            await asyncio.to_thread(_add)
        except Exception as e:
            print(f"[Memory/Add] {e}")

    async def get_memories(self, query: str, user_id: str = "adithya") -> str:
        """
        Semantically searches mem0 for facts relevant to the query.
        Returns clean extracted facts (not raw conversation chunks).
        """
        def _search():
            m = self._get_mem0()
            if m is None:
                return []
            return m.search(query, user_id=user_id, limit=5)

        try:
            results = await asyncio.to_thread(_search)
            if not results:
                return ""
            return "\n".join(f"- {r['memory']}" for r in results)
        except Exception as e:
            print(f"[Memory/Search] {e}")
            return ""

    async def get_all_memories(self, user_id: str = "adithya") -> list:
        """Returns all stored memories for the user (for debugging / Obsidian export)."""
        def _get_all():
            m = self._get_mem0()
            return m.get_all(filters={"user_id": user_id}) if m else []
        try:
            return await asyncio.to_thread(_get_all)
        except Exception:
            return []

    # ── Topic detection (instant, no LLM) ────────────────────────────────────
    def _detect_topic(self, text: str) -> str:
        t = text.lower()
        if any(w in t for w in ["python", "code", "bug", "script", "function", "sql", "data"]):
            return "Coding"
        if any(w in t for w in ["carleton", "university", "assignment", "grade", "lecture"]):
            return "University"
        if any(w in t for w in ["spotify", "music", "song", "play", "playlist", "track"]):
            return "Music"
        if any(w in t for w in ["tcs", "statscan", "statistics canada", "work", "career"]):
            return "Work"
        if any(w in t for w in ["open", "launch", "browser", "youtube", "google"]):
            return "System"
        if any(w in t for w in ["remember", "my name", "i am", "i like", "i love", "favourite"]):
            return "Personal"
        return "General"

    # ── Obsidian vault logging (human-readable layer) ─────────────────────────
    async def log_interaction(self, user_input: str, response: str, topic: str = "General"):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        entry = (
            f"### {timestamp} — {topic}\n"
            f"**Adithya**: {user_input}\n"
            f"**Aether**: {response}\n\n"
        )
        try:
            with open(self.memory_log_path, 'a', encoding='utf-8') as f:
                f.write(entry)
        except Exception as e:
            print(f"[Memory/Log] {e}")

    async def log_mistake(self, mistake_text: str) -> str:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] {mistake_text}\n"
        try:
            with open(self.mistakes_path, 'a', encoding='utf-8') as f:
                f.write(entry)
        except Exception:
            pass
        return f"Logged: {mistake_text}"

    # ── Skills (Obsidian vault — URL/app mappings) ────────────────────────────
    async def save_new_skill(self, app_name: str, url: str) -> str:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        block = (
            f"\n---skill\n"
            f"name: {app_name.lower()}\n"
            f"url: {url}\n"
            f"added: {timestamp}\n"
            f"---\n"
        )
        try:
            with open(self.learned_skills_path, 'a', encoding='utf-8') as f:
                f.write(block)
        except Exception as e:
            print(f"[Memory/Skill] {e}")
        return f"Memorized {app_name}."

    async def log_skill(self, tool: str, arg: str):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        entry = f"[{timestamp}] Used {tool}: {arg}\n"
        try:
            with open(self.learned_skills_path, 'a', encoding='utf-8') as f:
                f.write(entry)
        except Exception:
            pass

    def _parse_skill_blocks(self, path: str) -> dict:
        skills = {}
        if not os.path.exists(path):
            return skills
        try:
            content = open(path, 'r', encoding='utf-8').read()
            blocks = re.findall(r'---skill\n(.*?)---', content, re.DOTALL)
            for block in blocks:
                data = {}
                for line in block.strip().split('\n'):
                    if ':' in line:
                        k, v = line.split(':', 1)
                        data[k.strip()] = v.strip()
                if 'name' in data and 'url' in data:
                    skills[data['name'].lower()] = data['url']
        except Exception:
            pass
        return skills

    def get_skill_registry(self) -> dict:
        reg_path = os.path.join(os.getcwd(), "skills_registry.json")
        if not os.path.exists(reg_path):
            return {}
        try:
            return json.load(open(reg_path, 'r', encoding='utf-8'))
        except Exception:
            return {}

    def get_all_skills(self) -> dict:
        merged = {}
        merged.update(self._parse_skill_blocks(self.predefined_skills_path))
        merged.update(self._parse_skill_blocks(self.learned_skills_path))
        merged.update(self.get_skill_registry())
        return merged
