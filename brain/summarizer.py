"""
brain/summarizer.py
Hierarchical RAG assistant.

Summarizes Memory_Log.md into Weekly_Insights.md to provide Aether
with a high-level overview of past conversations without reading every chunk.
"""
import os
import ollama

VAULT_BASE = r"E:\Aether_Vault\Aether_Vault\_Aether"
LOG_PATH = os.path.join(VAULT_BASE, "Memory_Log.md")
INSIGHTS_PATH = os.path.join(VAULT_BASE, "Weekly_Insights.md")

async def generate_weekly_insights(model="llama3.2:1b"):
    """Distills the conversation log into a condensed insight note."""
    if not os.path.exists(LOG_PATH):
        return "No logs to summarize."

    with open(LOG_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    # Only summarize the last 5000 chars to avoid model context limits
    recent_log = content[-5000:]
    
    prompt = f"""
    You are Aether's internal summarizer. Below is a log of recent interactions with Adithya.
    Distill this into a 'Weekly Insights' note. 
    Focus on:
    1. Key projects or topics discussed (e.g. Software Engineering at Carleton).
    2. Preferences or instructions Adithya gave.
    3. Recurring issues or tasks.
    
    Format as a Markdown note with [[wiki-links]] to Identity.
    
    LOG:
    {recent_log}
    """

    try:
        response = ollama.chat(model=model, messages=[{'role': 'user', 'content': prompt}])
        summary = response['message']['content']
        
        header = f"\n---insight\nGenerated: {os.path.getmtime(LOG_PATH)}\n---\n"
        with open(INSIGHTS_PATH, 'w', encoding='utf-8') as f:
            f.write("# [[Weekly_Insights]]\n")
            f.write(header + summary)
            
        print("[Aether/Summarizer] Weekly_Insights.md updated.")
        return summary
    except Exception as e:
        print(f"[Aether/Summarizer] Error: {e}")
        return None
