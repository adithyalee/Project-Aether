import shutil
import webbrowser
import os
import datetime
import glob

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

def save_new_skill(app_name, url):
    """Saves a new skill mapping. Handled by MemoryManager in main.py."""
    return f"Learning {app_name} as {url}..."

def find_and_open_app(app_name):
    """Searches for an app in the Windows Start Menu and opens it."""
    search_paths = [
        r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\**\*.lnk",
        os.path.expandvars(r"%AppData%\Microsoft\Windows\Start Menu\Programs\**\*.lnk")
    ]
    
    app_name_lower = app_name.lower()
    for path in search_paths:
        for file in glob.glob(path, recursive=True):
            if app_name_lower in os.path.basename(file).lower():
                try:
                    os.startfile(file)
                    return f"Successfully launched {os.path.basename(file)}"
                except Exception as e:
                    return f"Error launching app: {e}"
    return None # Not found

def get_direct_youtube_link(query: str) -> str | None:
    """Searches YouTube using built-in urllib and returns the first video URL."""
    try:
        import urllib.request
        import urllib.parse
        import re

        search_keyword = urllib.parse.quote(query)
        url = f"https://www.youtube.com/results?search_query={search_keyword}"
        
        # Add a realistic User-Agent to avoid blocks
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req) as response:
            html = response.read().decode()
            
        # Find video IDs using regex
        video_ids = re.findall(r"watch\?v=(\S{11})", html)
        if video_ids:
            return f"https://www.youtube.com/watch?v={video_ids[0]}"
            
    except Exception as e:
        print(f"[Aether/Tools] YouTube Search (Native) failed: {e}")
    return None

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
    },
    {
        'type': 'function',
        'function': {
            'name': 'save_new_skill',
            'description': 'Saves a new URL mapping for an application or website when taught by the user.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'app_name': {
                        'type': 'string',
                        'description': 'The name of the app or site (e.g., "YouTube", "Brightspace")',
                    },
                    'url': {
                        'type': 'string',
                        'description': 'The exact URL to associate with that name',
                    },
                },
                'required': ['app_name', 'url'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'find_and_open_app',
            'description': 'Search for and launch a local Windows application by name.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'app_name': {
                        'type': 'string',
                        'description': 'The name of the application to find (e.g., "Spotify", "Code", "Chrome")',
                    },
                },
                'required': ['app_name'],
            },
        },
    }
]

# Mapping for the agent to call functions by name
TOOL_MAP = {
    'get_disk_space': get_disk_space,
    'open_url': open_url,
    'log_mistake': log_mistake,
    'save_new_skill': save_new_skill,
    'find_and_open_app': find_and_open_app,
    'get_direct_youtube_link': get_direct_youtube_link
}
