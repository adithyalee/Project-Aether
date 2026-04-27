"""
memory_cli.py — Adithya's Personal Memory System

Stores context from ALL your AI conversations in one place.
Use it with Aether, Claude, ChatGPT, Gemini — anywhere.

Commands:
  python memory_cli.py add "fact or context to remember"
  python memory_cli.py search "what do I know about X"
  python memory_cli.py briefing          ← paste this into any new AI chat
  python memory_cli.py show              ← see everything stored
  python memory_cli.py delete <id>       ← remove a memory by ID
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

GEMINI_KEY  = os.environ.get("GEMINI_API_KEY")
CHROMA_PATH = str(Path(__file__).parent / ".chroma_db")
USER_ID     = "adithya"


def _build_mem0() -> object:
    from mem0 import Memory

    # Always use local Ollama for mem0 fact extraction — free, no key, always works.
    # (Gemini is used for the main chat in main.py, kept separate.)
    llm_config = {
        "provider": "ollama",
        "config": {
            "model": "phi4-mini",
            "ollama_base_url": "http://localhost:11434",
            "temperature": 0.1,
        }
    }

    config = {
        "llm": llm_config,
        "embedder": {
            "provider": "huggingface",
            "config": {"model": "sentence-transformers/all-MiniLM-L6-v2"}
        },
        "vector_store": {
            "provider": "chroma",
            "config": {
                "collection_name": "aether_memory",
                "path": CHROMA_PATH,
            }
        },
        "history_db_path": str(Path(__file__).parent / ".mem0_history.db"),
    }
    return Memory.from_config(config)


def cmd_add(text: str):
    """Manually add a memory — use this to seed important facts about yourself."""
    m = _build_mem0()
    result = m.add(text, user_id=USER_ID)
    memories = result.get("results", []) if isinstance(result, dict) else result
    if memories:
        print(f"[Memory] Stored {len(memories)} fact(s):")
        for mem in memories:
            print(f"  + {mem.get('memory', mem)}")
    else:
        print("[Memory] Nothing new to store (already known or no facts found).")


def cmd_search(query: str):
    """Search your memories for anything related to a topic."""
    m = _build_mem0()
    results = m.search(query, user_id=USER_ID, limit=10)
    if not results:
        print(f"[Memory] Nothing found for: '{query}'")
        return
    print(f"\nMemories related to '{query}':\n")
    for r in results:
        print(f"  [{r.get('id', '?')[:8]}]  {r['memory']}")


def cmd_show():
    """Show all stored memories."""
    m = _build_mem0()
    all_mem = m.get_all(filters={"user_id": USER_ID})
    if not all_mem:
        print("[Memory] No memories stored yet.")
        return
    memories = all_mem.get("results", all_mem) if isinstance(all_mem, dict) else all_mem
    print(f"\nAll memories ({len(memories)} total):\n")
    for r in memories:
        print(f"  [{r.get('id','?')[:8]}]  {r['memory']}")


def cmd_briefing():
    """
    Generate a briefing prompt — paste this at the start of any new AI chat
    (Claude, ChatGPT, Gemini, etc.) to give it your full context instantly.
    """
    m = _build_mem0()
    all_mem = m.get_all(filters={"user_id": USER_ID})
    memories = all_mem.get("results", all_mem) if isinstance(all_mem, dict) else all_mem

    if not memories:
        print("[Memory] No memories yet. Run: python memory_cli.py add 'your info here'")
        return

    lines = [f"- {r['memory']}" for r in memories]
    briefing = (
        "== ADITHYA'S PERSONAL CONTEXT ==\n"
        "I am Adithya. Here is my context so you can continue from where we left off:\n\n"
        + "\n".join(lines)
        + "\n\n== END CONTEXT ==\n"
        "Now continue as if you already know all of this about me. "
        "Do not greet me as a stranger."
    )

    print("\n" + "=" * 60)
    print(briefing)
    print("=" * 60)

    # Also copy to clipboard automatically
    try:
        import subprocess
        subprocess.run(
            ["clip"],
            input=briefing.encode("utf-8"),
            check=True,
            shell=True
        )
        print("\n✓ Copied to clipboard — just paste into any AI chat.\n")
    except Exception:
        print("\n(Copy the text above and paste it into your AI chat.)\n")


def cmd_delete(memory_id: str):
    """Delete a specific memory by ID (use first 8 chars from 'show' output)."""
    m = _build_mem0()
    all_mem = m.get_all(filters={"user_id": USER_ID})
    memories = all_mem.get("results", all_mem) if isinstance(all_mem, dict) else all_mem

    full_id = next(
        (r['id'] for r in memories if r.get('id', '').startswith(memory_id)),
        None
    )
    if not full_id:
        print(f"[Memory] No memory found starting with ID: {memory_id}")
        return

    m.delete(full_id)
    print(f"[Memory] Deleted: {memory_id}")


def _build_context_block(memories: list, title: str = "ADITHYA'S CONTEXT") -> str:
    lines = [f"- {r['memory']}" for r in memories]
    return (
        f"## {title}\n"
        f"I am Adithya Thaninki (Adi). Continue from where we left off — do not greet me as a stranger.\n\n"
        + "\n".join(lines)
        + "\n\n"
        "## Rules\n"
        "- You already know me\n"
        "- Be concise and direct\n"
        "- If I say 'take over from Claude / Cursor / Aether', read the context above and continue seamlessly\n"
    )


def cmd_sync():
    """
    Sync your memory to ALL local tools at once:
      - CONTEXT.md        → read by Cursor, Antigravity, any local IDE
      - .cursorrules      → read by Cursor automatically
      - Obsidian vault    → Session_Log.md in your vault (human-readable)

    Run this after any important session.
    """
    import datetime
    m = _build_mem0()
    all_mem = m.get_all(filters={"user_id": USER_ID})
    memories = all_mem.get("results", all_mem) if isinstance(all_mem, dict) else all_mem

    if not memories:
        print("[Sync] No memories yet. Run: python memory_cli.py add 'your info'")
        return

    context = _build_context_block(memories)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    project_root = Path(__file__).parent

    # 1. CONTEXT.md — any local IDE reads this
    context_path = project_root / "CONTEXT.md"
    context_path.write_text(f"*Last updated: {timestamp}*\n\n{context}", encoding="utf-8")
    print(f"[Sync] CONTEXT.md updated")

    # 2. .cursorrules — Cursor reads automatically
    cursorrules_path = project_root / ".cursorrules"
    cursorrules_path.write_text(context, encoding="utf-8")
    print(f"[Sync] .cursorrules updated")

    # 3. Obsidian vault — human-readable session log
    vault = os.environ.get("VAULT_BASE", "")
    if vault and Path(vault).exists():
        obsidian_path = Path(vault) / "Session_Log.md"
        entry = f"\n---\n### {timestamp}\n{context}\n"
        with open(obsidian_path, "a", encoding="utf-8") as f:
            f.write(entry)
        print(f"[Sync] Obsidian Session_Log.md updated")
    else:
        print(f"[Sync] Obsidian vault not found — skipping (check VAULT_BASE in .env)")

    print("\nDone. All local IDEs (Cursor, Antigravity, etc.) now have your full context.\n")


def cmd_cursor():
    """Alias for sync — kept for backwards compatibility."""
    cmd_sync()


def cmd_summarize(text: str):
    """
    End-of-session command. Saves your summary AND syncs everything to local IDEs.
    Use this before closing any AI session.

    Usage:
      python memory_cli.py summarize "built X, fixed Y, decided Z"
    """
    if not text.strip():
        print("Usage: python memory_cli.py summarize \"what we built or decided today\"")
        return

    import datetime
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d")
    full_text = f"Session {timestamp}: {text}"

    print("[Memory] Saving session summary...")
    cmd_add(full_text)

    print("[Memory] Syncing to all local IDEs...")
    cmd_sync()


def cmd_help():
    print("""
Personal Memory CLI — cross-AI context store

  add "text"       Store a fact or context
  search "query"   Find memories related to a topic
  show             List all stored memories
  briefing         Generate paste-able context for Claude/ChatGPT/Gemini (copies to clipboard)
  cursor           Update .cursorrules so Cursor always has your context automatically
  delete <id>      Delete a memory by ID (first 8 chars)

Examples:
  python memory_cli.py add "I am building Project Aether, a Python voice AI assistant"
  python memory_cli.py add "I am at Carleton University, studying data engineering"
  python memory_cli.py add "My GitHub username is kartik-mem0"
  python memory_cli.py briefing
  python memory_cli.py search "university"
""")


COMMANDS = {
    "add":       lambda args: cmd_add(" ".join(args)),
    "search":    lambda args: cmd_search(" ".join(args)),
    "show":      lambda args: cmd_show(),
    "briefing":  lambda args: cmd_briefing(),
    "sync":      lambda args: cmd_sync(),
    "summarize": lambda args: cmd_summarize(" ".join(args)),
    "cursor":    lambda args: cmd_cursor(),
    "delete":    lambda args: cmd_delete(args[0] if args else ""),
    "help":      lambda args: cmd_help(),
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        cmd_help()
        sys.exit(0)
    COMMANDS[sys.argv[1]](sys.argv[2:])
