"""Quick smoke test for the full RAG + Reflexion pipeline."""
import sys
sys.path.insert(0, r'd:\Project Aether')

from brain.memory_manager import MemoryManager
from brain.rag_engine import index_vault, query

# 1. Test MemoryManager wiki-links
m = MemoryManager()
print("=== MemoryManager ===")
print("All skills:", list(m.get_all_skills().keys()))

# 2. Test RAG index
print("\n=== RAG Index ===")
count = index_vault()
print(f"Indexed {count} chunks")

# 3. Test RAG query
print("\n=== RAG Queries ===")
for q in ["What is Adithya studying?", "What skills has Aether learned?", "What mistakes did Aether make?"]:
    hits = query(q, n_results=1)
    if hits:
        print(f'  Q: "{q}"')
        print(f'  A: [{hits[0]["source"]}] {hits[0]["text"][:100]}...')
    else:
        print(f'  Q: "{q}" -> No hits')
    print()

# 4. Test main.py imports cleanly
from main import AetherAgent
print("=== main.py imports OK ===")
print("All systems go!")
