"""
brain/memory_manager.py — Graph Cleanup Edition
Removes all date-based wiki-links to keep the Obsidian graph focused on Hubs/Topics.
"""
import datetime
import os
import json
import re
import asyncio

class MemoryManager:
    VAULT_BASE = r"E:\Aether_Vault\Aether_Vault\_Aether"
    SKILLS_SCHEMA_VERSION = "1.0"

    def __init__(self):
        self.mistakes_path = os.path.join(self.VAULT_BASE, "Mistakes.md")
        self.learned_skills_path = os.path.join(self.VAULT_BASE, "Learned_Skills.md")
        self.predefined_skills_path = os.path.join(self.VAULT_BASE, "Predefined_Skills.md")
        self.memory_log_path = os.path.join(self.VAULT_BASE, "Memory_Log.md")
        self.registry_path = "skills_registry.json"

    def _detect_topic(self, text: str) -> str:
        t = text.lower()
        if any(w in t for w in ["python", "code", "programming", "bug", "script"]): return "Coding"
        if any(w in t for w in ["carleton", "university", "course", "assignment"]): return "University"
        return "General"

    async def _trigger_rag_learn(self, text, source, metadata=None):
        try:
            from brain.rag_engine import upsert_text
            await upsert_text(text, source, metadata)
        except Exception as e:
            print(f"[MemoryManager] RAG update failed: {e}")

    def _friendly_name(self, argument: str) -> str:
        if argument.startswith("http"):
            for k in ["spotify", "google", "youtube", "brightspace", "carleton", "gemini"]:
                if k in argument.lower(): return k.capitalize()
        return argument

    async def log_mistake(self, mistake_text: str) -> str:
        # NO [[wiki-links]] for dates
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"Mistake on {timestamp}: {mistake_text} (Context: [[Mistakes]])\n"
        with open(self.mistakes_path, 'a', encoding='utf-8') as f: f.write(entry)
        await self._trigger_rag_learn(entry, "Mistakes.md", {"topic": "System"})
        return f"Logged mistake: {mistake_text}"

    async def log_correction(self, hallucinated: str, resolved: str, arg: str):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Link to the Topic Hub, not the date
        topic = self._friendly_name(arg).capitalize()
        entry = f"Correction on {timestamp}: Called `{hallucinated}` → resolved to `{resolved}` for [[{topic}]].\n"
        with open(self.mistakes_path, 'a', encoding='utf-8') as f: f.write(entry)
        await self._trigger_rag_learn(entry, "Mistakes.md", {"topic": "System"})

    async def log_interaction(self, user_input: str, response: str, topic: str = "General"):
        """Hub-centric logging. No date links."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        topic_link = f"[[{topic.capitalize()}]]"
        entry = (
            f"### Interaction on {timestamp}\n"
            f"Topic: {topic_link}\n"
            f"**Adithya**: {user_input}\n"
            f"**Aether**: {response}\n\n"
        )
        with open(self.memory_log_path, 'a', encoding='utf-8') as f: f.write(entry)
        await self._trigger_rag_learn(entry, "Memory_Log.md", {"topic": topic})

    async def save_new_skill(self, app_name: str, url: str) -> str:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        block = f"\n---skill\nname: {app_name.lower()}\nurl: {url}\nadded: {timestamp}\nlinked: [[Learned_Skills]]\n---\n"
        with open(self.learned_skills_path, 'a', encoding='utf-8') as f: f.write(block)
        await self._trigger_rag_learn(block, "Learned_Skills.md")
        return f"Memorized {app_name}."

    async def log_skill(self, tool: str, arg: str):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        topic = self._friendly_name(arg).capitalize()
        entry = f"Activity on {timestamp}: Successfully opened [[{topic}]].\n"
        with open(self.learned_skills_path, 'a', encoding='utf-8') as f: f.write(entry)
        await self._trigger_rag_learn(entry, "Learned_Skills.md")

    def get_skill_registry(self):
        reg_path = os.path.join(os.getcwd(), "skills_registry.json")
        if not os.path.exists(reg_path): return {}
        return json.load(open(reg_path, 'r', encoding='utf-8'))

    def _parse_skill_blocks(self, path: str) -> dict:
        skills = {}
        if not os.path.exists(path): return skills
        try:
            content = open(path, 'r', encoding='utf-8').read()
            blocks = re.findall(r'---skill\n(.*?)---', content, re.DOTALL)
            for block in blocks:
                data = {}
                for line in block.strip().split('\n'):
                    if ':' in line:
                        k, v = line.split(':', 1)
                        data[k.strip()] = v.strip()
                if 'name' in data and 'url' in data: skills[data['name'].lower()] = data['url']
        except: pass
        return skills

    def get_all_skills(self):
        merged = {}
        predefined = os.path.join(self.VAULT_BASE, "Predefined_Skills.md")
        merged.update(self._parse_skill_blocks(predefined))
        merged.update(self._parse_skill_blocks(self.learned_skills_path))
        merged.update(self.get_skill_registry())
        return merged
