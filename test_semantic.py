import sys
sys.path.insert(0, 'd:/Project Aether')
from brain.memory_manager import MemoryManager
from brain.semantic_matcher import find_best_skill

m = MemoryManager()
skills = m.get_all_skills()
print('Skills loaded:', list(skills.keys()))

tests = [
    'launch the music player',
    'I want to watch a video',
    'open my university courses',
    'open spotify in browser',
    'show me carleton university website'
]
for query in tests:
    best, url, score = find_best_skill(query, skills)
    print(f'  Query: "{query}"')
    print(f'  Match: {best} -> {url}  (score={score:.3f})')
    print()
