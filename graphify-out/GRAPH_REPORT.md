# Graph Report - Project Aether  (2026-04-26)

## Corpus Check
- 15 files · ~124,514 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 128 nodes · 209 edges · 19 communities detected
- Extraction: 64% EXTRACTED · 36% INFERRED · 0% AMBIGUOUS · INFERRED: 75 edges (avg confidence: 0.63)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]

## God Nodes (most connected - your core abstractions)
1. `MemoryManager` - 36 edges
2. `AetherAgent` - 19 edges
3. `AetherSTT` - 15 edges
4. `AetherTTS` - 15 edges
5. `main()` - 7 edges
6. `_init_indexes()` - 7 edges
7. `_gpu_active()` - 5 edges
8. `find_best_skill()` - 5 edges
9. `test_memory()` - 4 edges
10. `sync_identity()` - 4 edges

## Surprising Connections (you probably didn't know these)
- `test_memory()` --calls--> `MemoryManager`  [INFERRED]
  brain_audit.py → brain\memory_manager.py
- `AetherAgent` --uses--> `MemoryManager`  [INFERRED]
  main.py → brain\memory_manager.py
- `AetherAgent` --uses--> `AetherTTS`  [INFERRED]
  main.py → tts\kokoro_tts.py
- `AetherAgent` --uses--> `AetherSTT`  [INFERRED]
  main.py → stt\whisper_stt.py
- `main()` --calls--> `index_vault()`  [INFERRED]
  main.py → brain\rag_engine.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.11
Nodes (17): AetherTTS, Generates and plays audio for the given text., _build_personal_prompt(), _build_work_prompt(), _gpu_active(), main(), main.py — ASYNC Masterpiece Edition, # NOTE: Optimized for 16GB RAM + Intel Iris Xe. (+9 more)

### Community 1 - "Community 1"
Cohesion: 0.12
Nodes (10): # NOTE: For faster performance on VivoBook, run: ollama pull llama3.2:3b-instruc, Placeholder for 'Ears' (STT) module., Placeholder for 'Voice' (TTS) module., Owner-First Identity Anchor: Grounds Aether in Adithya's context with few-shot b, Generates the initial personalized greeting., Scans the vault to find existing hubs (wiki-linked topics)., Asks the model to 'think' and categorize the interaction into a meaningful hub., MemoryManager (+2 more)

### Community 2 - "Community 2"
Cohesion: 0.15
Nodes (12): find_and_open_app(), get_direct_youtube_link(), get_disk_space(), log_mistake(), open_url(), Returns disk usage information for the C: drive., Opens a specified URL in the default web browser., Saves a new skill mapping. Handled by MemoryManager in main.py. (+4 more)

### Community 3 - "Community 3"
Cohesion: 0.24
Nodes (4): AetherAgent, Simple sliding window — keeps system prompt + last WINDOW_SIZE messages., Fire-and-forget: categorise + write to memory + update cache., Quick smoke test for the full RAG + Reflexion pipeline.

### Community 4 - "Community 4"
Cohesion: 0.38
Nodes (9): add_to_cache(), check_cache(), _chunk_text(), clear_cache(), index_vault(), _init_indexes(), query(), brain/rag_engine.py — ASYNC Masterpiece Edition (+1 more)

### Community 5 - "Community 5"
Cohesion: 0.29
Nodes (7): Phase 1: Foundation, Phase 2: Browser Eyes, Phase 3: Presence, Phase 4: Full Autonomy, Vision: Self-Evolving Digital Twin, Obsidian (Memory), Ollama (Cognition)

### Community 6 - "Community 6"
Cohesion: 0.33
Nodes (3): test_memory(), Saves a conversation snippet as a quick-access fact. Zero GPU, instant., Retrieves relevant facts by keyword matching. Returns top 5 matches.

### Community 7 - "Community 7"
Cohesion: 0.4
Nodes (5): find_best_skill(), _get_model(), brain/semantic_matcher.py Lightweight semantic similarity engine for Aether. Use, Lazy-load the sentence transformer model to avoid slow startup., Finds the best matching skill for a given user query using cosine similarity.

### Community 8 - "Community 8"
Cohesion: 0.5
Nodes (3): generate_weekly_insights(), brain/summarizer.py Hierarchical RAG assistant.  Summarizes Memory_Log.md into W, Distills the conversation log into a condensed insight note.

### Community 14 - "Community 14"
Cohesion: 1.0
Nodes (1): Hub-centric logging. No date links.

### Community 15 - "Community 15"
Cohesion: 1.0
Nodes (1): Hierarchical Async Search: Insights first, then Raw Data.

### Community 16 - "Community 16"
Cohesion: 1.0
Nodes (1): Appends a timestamped log to the mistakes file.

### Community 17 - "Community 17"
Cohesion: 1.0
Nodes (1): Logs a successful tool usage to the Learned_Skills file.

### Community 18 - "Community 18"
Cohesion: 1.0
Nodes (1): Reads and returns the last 5 mistakes from the file as a single string.

### Community 19 - "Community 19"
Cohesion: 1.0
Nodes (1): Logs a mistake to the Mistakes.md file to avoid repeating it in the future.

### Community 20 - "Community 20"
Cohesion: 1.0
Nodes (1): Returns disk usage information for the C: drive.

### Community 21 - "Community 21"
Cohesion: 1.0
Nodes (1): Opens a specified URL in the default web browser.

### Community 22 - "Community 22"
Cohesion: 1.0
Nodes (1): Playwright (Automation)

### Community 23 - "Community 23"
Cohesion: 1.0
Nodes (1): Whisper (Voice)

## Knowledge Gaps
- **40 isolated node(s):** `brain/memory_manager.py — Graph Cleanup Edition Removes all date-based wiki-link`, `Saves a conversation snippet as a quick-access fact. Zero GPU, instant.`, `Retrieves relevant facts by keyword matching. Returns top 5 matches.`, `Hub-centric logging. No date links.`, `brain/rag_engine.py — ASYNC Masterpiece Edition` (+35 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 14`** (1 nodes): `Hub-centric logging. No date links.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 15`** (1 nodes): `Hierarchical Async Search: Insights first, then Raw Data.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 16`** (1 nodes): `Appends a timestamped log to the mistakes file.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 17`** (1 nodes): `Logs a successful tool usage to the Learned_Skills file.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 18`** (1 nodes): `Reads and returns the last 5 mistakes from the file as a single string.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 19`** (1 nodes): `Logs a mistake to the Mistakes.md file to avoid repeating it in the future.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 20`** (1 nodes): `Returns disk usage information for the C: drive.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 21`** (1 nodes): `Opens a specified URL in the default web browser.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 22`** (1 nodes): `Playwright (Automation)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 23`** (1 nodes): `Whisper (Voice)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `MemoryManager` connect `Community 1` to `Community 0`, `Community 3`, `Community 6`?**
  _High betweenness centrality (0.243) - this node is a cross-community bridge._
- **Why does `AetherAgent` connect `Community 3` to `Community 0`, `Community 1`, `Community 4`?**
  _High betweenness centrality (0.142) - this node is a cross-community bridge._
- **Why does `find_best_skill()` connect `Community 7` to `Community 3`, `Community 4`?**
  _High betweenness centrality (0.064) - this node is a cross-community bridge._
- **Are the 21 inferred relationships involving `MemoryManager` (e.g. with `AetherAgent` and `main.py — ASYNC Masterpiece Edition`) actually correct?**
  _`MemoryManager` has 21 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `AetherAgent` (e.g. with `MemoryManager` and `AetherTTS`) actually correct?**
  _`AetherAgent` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `AetherSTT` (e.g. with `AetherAgent` and `main.py — ASYNC Masterpiece Edition`) actually correct?**
  _`AetherSTT` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `AetherTTS` (e.g. with `AetherAgent` and `main.py — ASYNC Masterpiece Edition`) actually correct?**
  _`AetherTTS` has 12 INFERRED edges - model-reasoned connections that need verification._