import shutil
import webbrowser
import os
import datetime

# Helper to log mistakes (can be imported from memory_manager or defined here)
def log_mistake(mistake_text):
    """Logs a mistake to the Mistakes.md file to avoid repeating it in the future."""
    # Importing here to avoid circular dependency if needed, 
    # but we can just implement the write logic here for the tool.
    mistakes_path = r"E:\Aether_Vault\Aether_Vault\_Aether\Mistakes.md"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {mistake_text}\n"
    try:
        with open(mistakes_path, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        return f"Logged mistake: {mistake_text}"
    except Exception as e:
        return f"Error logging mistake: {e}"

def get_disk_space():
    """Returns disk usage information for the C: drive."""
    total, used, free = shutil.disk_usage("C:")
    return {
        "total_gb": total // (2**30),
        "used_gb": used // (2**30),
        "free_gb": free // (2**30),
        "percent_used": round((used / total) * 100, 2)
    }

def open_url(url):
    """Opens a specified URL in the default web browser."""
    if not url.startswith("http"):
        url = "https://" + url
    try:
        webbrowser.open(url)
        return f"Successfully opened {url}"
    except Exception as e:
        return f"Failed to open URL: {e}"

# Tool definitions for Ollama
TOOLS = [
    {
        'type': 'function',
        'function': {
            'name': 'get_disk_space',
            'description': 'Check the available disk space on the computer.',
            'parameters': {
                'type': 'object',
                'properties': {},
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'open_url',
            'description': 'Open a website or URL in the default web browser.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'url': {
                        'type': 'string',
                        'description': 'The URL to open (e.g., google.com, youtube.com).',
                    },
                },
                'required': ['url'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'log_mistake',
            'description': 'Log an error or mistake to the memory file so it is not repeated.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'mistake_text': {
                        'type': 'string',
                        'description': 'The description of the mistake or error to remember.',
                    },
                },
                'required': ['mistake_text'],
            },
        },
    }
]

# Mapping for the agent to call functions by name
TOOL_MAP = {
    'get_disk_space': get_disk_space,
    'open_url': open_url,
    'log_mistake': log_mistake
}
