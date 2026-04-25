import datetime
import os

class MemoryManager:
    def __init__(self):
        self.mistakes_path = r"E:\Aether_Vault\Aether_Vault\_Aether\Mistakes.md"

    def log_mistake(self, mistake_text):
        """Appends a timestamped log to the mistakes file."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {mistake_text}\n"
        
        try:
            # Ensure directory exists (though path is fixed, good practice)
            os.makedirs(os.path.dirname(self.mistakes_path), exist_ok=True)
            
            with open(self.mistakes_path, 'a', encoding='utf-8') as f:
                f.write(log_entry)
            return f"Logged mistake: {mistake_text}"
        except Exception as e:
            return f"Error logging mistake: {e}"

    def log_skill(self, tool_name, argument):
        """Logs a successful tool usage to the Learned_Skills file."""
        skills_path = r"E:\Aether_Vault\Aether_Vault\_Aether\Learned_Skills.md"
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        log_entry = f"[{timestamp}] Skill Used: [{tool_name}] for [{argument}]\n"
        
        try:
            os.makedirs(os.path.dirname(skills_path), exist_ok=True)
            with open(skills_path, 'a', encoding='utf-8') as f:
                f.write(log_entry)
            return True
        except Exception as e:
            print(f"Error logging skill: {e}")
            return False

    def get_mistakes(self):
        """Reads and returns the last 5 mistakes from the file as a single string."""
        if not os.path.exists(self.mistakes_path):
            return "No past mistakes recorded."
        
        try:
            with open(self.mistakes_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if not lines:
                    return "No past mistakes recorded."
                
                # Get last 5 lines
                last_5 = lines[-5:]
                return "".join(last_5).strip()
        except Exception as e:
            return f"Error reading mistakes: {e}"
