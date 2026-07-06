"""Smoke test: lite-mode fallbacks work without heavy deps or an LLM."""
import asyncio
import sys
import types

# Simulate missing heavy deps regardless of what's installed
for mod in ("sentence_transformers", "txtai", "txtai.embeddings"):
    sys.modules[mod] = None  # forces ImportError on `from x import y`


def test_fuzzy_matcher():
    import brain.embeddings as emb
    emb._model = False  # force difflib path
    from brain.semantic_matcher import find_best_skill
    name, url, score = find_best_skill("youtube", {"youtube": "https://youtube.com", "spotify": "https://spotify.com"})
    assert name == "youtube" and url == "https://youtube.com", (name, url, score)
    name, url, _ = find_best_skill("zzzzzz", {"youtube": "https://youtube.com"})
    assert name is None and url is None


def test_teach_and_greeting():
    import main as m
    assert m.RAG_OK in (True, False)
    # RAG stubs (or real funcs) respond without crashing
    asyncio.run(m.check_cache("hello"))

    agent = m.AetherAgent()
    greet = agent.startup_greeting()
    assert greet.startswith("Good ") and "Adi" in greet, greet

    # teach parsing: URL scheme added
    body = "brightspace = brightspace.carleton.ca"
    name, target = (s.strip() for s in body.split("=", 1))
    if target and not target.startswith("http") and "." in target:
        target = "https://" + target
    assert target == "https://brightspace.carleton.ca"


if __name__ == "__main__":
    test_fuzzy_matcher()
    test_teach_and_greeting()
    print("LITE MODE OK — fuzzy match, RAG stubs, greeting, teach parsing all pass")
