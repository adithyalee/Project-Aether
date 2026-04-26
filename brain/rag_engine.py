"""
brain/rag_engine.py — ASYNC Masterpiece Edition
"""
import os
import hashlib
import re
import asyncio
from pathlib import Path

# Suppress HuggingFace noise
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

_collection = None
_cache_collection = None
_chroma_client = None
_embed_fn = None

VAULT_BASE = r"E:\Aether_Vault\Aether_Vault\_Aether"
CHROMA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".chroma_db")

INDEX_FILES = [
    "Identity.md", "Welcome.md", "Learned_Skills.md", 
    "Mistakes.md", "Predefined_Skills.md", "Memory_Log.md",
    "Weekly_Insights.md"
]

def _get_embed_fn():
    global _embed_fn
    if _embed_fn: return _embed_fn
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")
    _embed_fn = lambda texts: model.encode(texts, show_progress_bar=False).tolist()
    return _embed_fn

def _init_collections():
    global _collection, _cache_collection, _chroma_client
    if _collection and _cache_collection: return _collection, _cache_collection
    import chromadb
    _chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
    _collection = _chroma_client.get_or_create_collection("aether_vault", metadata={"hnsw:space": "cosine"})
    _cache_collection = _chroma_client.get_or_create_collection("semantic_cache", metadata={"hnsw:space": "cosine"})
    return _collection, _cache_collection

def _chunk_text(text: str, source: str) -> list[dict]:
    paras = re.split(r'\n{2,}', text.strip())
    chunks = []
    curr = ""
    for p in paras:
        if len(curr) + len(p) > 300 and curr:
            chunks.append({"text": curr.strip(), "source": source, "hash": hashlib.md5(curr.encode()).hexdigest()})
            curr = p
        else: curr = curr + "\n\n" + p if curr else p
    if curr.strip(): chunks.append({"text": curr.strip(), "source": source, "hash": hashlib.md5(curr.encode()).hexdigest()})
    return chunks

async def index_vault():
    col, _ = _init_collections()
    embed = _get_embed_fn()
    total = 0
    for fname in INDEX_FILES:
        fpath = os.path.join(VAULT_BASE, fname)
        if not os.path.exists(fpath): continue
        text = Path(fpath).read_text(encoding="utf-8", errors="replace")
        chunks = _chunk_text(text, fname)
        if not chunks: continue
        
        topic = "System" if "Mistakes" in fname else "General"
        if "Identity" in fname: topic = "Personal"
        
        col.upsert(
            ids=[c["hash"] for c in chunks],
            embeddings=embed([c["text"] for c in chunks]),
            documents=[c["text"] for c in chunks],
            metadatas=[{"source": c["source"], "topic": topic} for c in chunks]
        )
        total += len(chunks)
    print(f"[Aether/RAG] Async Indexing complete: {total} chunks.")
    return total

async def upsert_text(text: str, source: str, metadata: dict = None):
    col, _ = _init_collections()
    embed = _get_embed_fn()
    chunks = _chunk_text(text, source)
    if not chunks: return
    
    metas = []
    for c in chunks:
        m = {"source": c["source"]}
        if metadata: m.update(metadata)
        metas.append(m)
    col.upsert(
        ids=[c["hash"] for c in chunks],
        embeddings=embed([c["text"] for c in chunks]),
        documents=[c["text"] for c in chunks],
        metadatas=metas
    )

async def query(question: str, n_results: int = 3, topic_filter: str = None) -> list[dict]:
    """Hierarchical Async Search: Insights first, then Raw Data."""
    col, _ = _init_collections()
    embed = _get_embed_fn()
    q_emb = embed([question])

    # 1. Search Weekly_Insights first for high-level context
    try:
        insight_hits = col.query(query_embeddings=q_emb, n_results=1, where={"source": "Weekly_Insights.md"})
    except: insight_hits = {"documents": [[]]}
    
    # 2. General search with filter
    where = {"topic": topic_filter} if topic_filter else None
    results = col.query(query_embeddings=q_emb, n_results=n_results, where=where)

    hits = []
    # Add insight if strong match
    if insight_hits["documents"][0] and insight_hits["distances"][0][0] < 0.4:
        hits.append({"text": insight_hits["documents"][0][0], "source": "Weekly_Insights.md", "topic": "Summary"})
    
    for i in range(len(results["documents"][0])):
        hits.append({
            "text": results["documents"][0][i],
            "source": results["metadatas"][0][i].get("source", "?"),
            "topic": results["metadatas"][0][i].get("topic", "General")
        })
    return hits

async def check_cache(question: str, threshold: float = 0.1) -> str | None:
    _, cache = _init_collections()
    res = cache.query(query_embeddings=_get_embed_fn()([question]), n_results=1)
    if res["documents"][0] and res["distances"][0][0] < threshold:
        return res["documents"][0][0]
    return None

async def add_to_cache(question: str, answer: str):
    _, cache = _init_collections()
    cache.upsert(
        ids=[hashlib.md5(question.encode()).hexdigest()],
        embeddings=_get_embed_fn()([question]),
        documents=[answer],
        metadatas=[{"question": question}]
    )
