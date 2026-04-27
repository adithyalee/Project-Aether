"""
brain/rag_engine.py — TXTAI Turbo Edition
"""
import os
import hashlib
import re
import asyncio
from pathlib import Path
from txtai.embeddings import Embeddings

# Suppress HuggingFace noise
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

_vault_index = None
_cache_index = None

VAULT_BASE = r"E:\Aether_Vault\Aether_Vault\_Aether"
INDEX_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".txtai")

INDEX_FILES = [
    "Identity.md", "Welcome.md", "Learned_Skills.md", 
    "Mistakes.md", "Predefined_Skills.md", "Memory_Log.md",
    "Weekly_Insights.md"
]

def _init_indexes():
    global _vault_index, _cache_index
    if _vault_index and _cache_index: return _vault_index, _cache_index
    
    # Initialize vault index
    v_path = os.path.join(INDEX_DIR, "vault")
    os.makedirs(v_path, exist_ok=True)
    _vault_index = Embeddings({"path": "sentence-transformers/all-MiniLM-L6-v2", "content": True})
    if os.path.exists(os.path.join(v_path, "config")):
        _vault_index.load(v_path)
    
    # Initialize semantic cache index
    c_path = os.path.join(INDEX_DIR, "cache")
    os.makedirs(c_path, exist_ok=True)
    _cache_index = Embeddings({"path": "sentence-transformers/all-MiniLM-L6-v2", "content": True})
    if os.path.exists(os.path.join(c_path, "config")):
        _cache_index.load(c_path)
        
    return _vault_index, _cache_index

def _chunk_text(text: str, source: str) -> list[dict]:
    paras = re.split(r'\n{2,}', text.strip())
    chunks = []
    curr = ""
    for p in paras:
        if len(curr) + len(p) > 300 and curr:
            chunks.append({"text": curr.strip(), "source": source, "id": hashlib.md5(curr.encode()).hexdigest()})
            curr = p
        else: curr = curr + "\n\n" + p if curr else p
    if curr.strip(): chunks.append({"text": curr.strip(), "source": source, "id": hashlib.md5(curr.encode()).hexdigest()})
    return chunks

async def index_vault():
    vault, _ = _init_indexes()
    data = []
    for fname in INDEX_FILES:
        fpath = os.path.join(VAULT_BASE, fname)
        if not os.path.exists(fpath): continue
        text = Path(fpath).read_text(encoding="utf-8", errors="replace")
        chunks = _chunk_text(text, fname)
        for c in chunks:
            topic = "System" if "Mistakes" in fname else "General"
            if "Identity" in fname: topic = "Personal"
            # Format for txtai: (id, data, metadata)
            data.append((c["id"], {"text": c["text"], "source": c["source"], "topic": topic}, None))
            
    if data:
        await asyncio.to_thread(vault.index, data)
        await asyncio.to_thread(vault.save, os.path.join(INDEX_DIR, "vault"))
    print(f"[Aether/RAG] txtai Indexing complete: {len(data)} chunks.")
    return len(data)

async def upsert_text(text: str, source: str, metadata: dict = None):
    vault, _ = _init_indexes()
    chunks = _chunk_text(text, source)
    if not chunks: return
    
    data = []
    for c in chunks:
        m = {"text": c["text"], "source": c["source"], "topic": "General"}
        if metadata: m.update(metadata)
        data.append((c["id"], m, None))
        
    await asyncio.to_thread(vault.upsert, data)
    await asyncio.to_thread(vault.save, os.path.join(INDEX_DIR, "vault"))

async def query(question: str, n_results: int = 3, topic_filter: str = None) -> list[dict]:
    vault, _ = _init_indexes()
    
    # Build SQL-like query for txtai if filter is present
    search_query = question
    if topic_filter:
        # txtai supports filtering if we enable it, but for simplicity we'll filter results post-search
        pass

    results = await asyncio.to_thread(vault.search, question, n_results + 2)
    
    hits = []
    for r in results:
        # r is {'id': ..., 'text': ..., 'score': ..., 'source': ..., 'topic': ...} 
        # but wait, txtai returns results differently depending on config.
        # With content=True, it returns dicts.
        if topic_filter and r.get("topic") != topic_filter:
            continue
        hits.append({
            "text": r["text"],
            "source": r.get("source", "?"),
            "topic": r.get("topic", "General")
        })
    return hits[:n_results]

async def check_cache(question: str, threshold: float = 0.85) -> str | None:
    # txtai score is cosine similarity (1.0 is exact match)
    _, cache = _init_indexes()
    res = await asyncio.to_thread(cache.search, question, 1)
    if res and res[0]["score"] > threshold:
        return res[0]["text"]
    return None

async def add_to_cache(question: str, answer: str):
    _, cache = _init_indexes()
    uid = hashlib.md5(question.encode()).hexdigest()
    await asyncio.to_thread(cache.upsert, [(uid, {"text": answer, "question": question}, None)])
    await asyncio.to_thread(cache.save, os.path.join(INDEX_DIR, "cache"))

async def clear_cache():
    global _cache_index
    c_path = os.path.join(INDEX_DIR, "cache")
    if os.path.exists(c_path):
        import shutil
        shutil.rmtree(c_path)
    _cache_index = None
    _init_indexes()
    print("[Aether/Cache] txtai cache cleared.")
