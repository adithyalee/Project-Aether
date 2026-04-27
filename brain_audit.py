import asyncio
from brain.memory_manager import MemoryManager

async def test_memory():
    print("--- [TEST] Mem0 Local Audit ---")
    mem = MemoryManager()
    
    # Test 1: Add a unique fact
    print("\n1. Testing Fact Addition...")
    await mem.add_fact("Adithya likes to code in Python late at night.")
    
    # Give it a second to process
    await asyncio.sleep(2)
    
    # Test 2: Search for that fact
    print("\n2. Testing Fact Retrieval...")
    facts = await mem.get_memories("What does Adithya do late at night?")
    print(f"Retrieved Facts:\n{facts}")
    
    if "Python" in facts:
        print("\nSUCCESS: Mem0 is working perfectly.")
    else:
        print("\nFAILURE: Mem0 did not retrieve the fact.")

if __name__ == "__main__":
    asyncio.run(test_memory())
