import ollama
import os
import sys
import json
import re
from brain.memory_manager import MemoryManager
from tools.pc_controls import TOOLS, TOOL_MAP

class AetherAgent:
    def __init__(self, model="llama3.2:1b"):
        self.model = model
        self.identity_path = r"E:\Aether_Vault\Aether_Vault\_Aether\Identity.md"
        self.memory = MemoryManager()
        self.identity_data = self._load_identity()
        self.mistakes = self.memory.get_mistakes()
        self.session_messages = []
        
        # Initialize session with context
        self._initialize_system_context()

    def _load_identity(self):
        try:
            if os.path.exists(self.identity_path):
                with open(self.identity_path, 'r', encoding='utf-8') as f:
                    return f.read()
            return "No identity data found."
        except Exception as e:
            return f"Error loading identity: {e}"

    def _initialize_system_context(self):
        system_prompt = f"""
        You are Aether, the AI assistant. The following data is about the USER, Adithya. 
        You are helping him with his Software Engineering studies at Carleton. 
        Do not claim his identity as your own.
        
        USER Identity Info:
        {self.identity_data}
        
        Past Mistakes/Learnings:
        {self.mistakes}
        
        Guidelines:
        - Be professional and helpful.
        - Use tools when asked.
        """
        self.session_messages.append({'role': 'system', 'content': system_prompt})

    def initialize_greeting(self):
        """Generates the initial personalized greeting."""
        prompt = "Create a professional and friendly greeting. Explicitly mention that I am a student at Carleton."
        # Don't use tools for the initial greeting to avoid confusion
        try:
            response = ollama.chat(
                model=self.model,
                messages=self.session_messages + [{'role': 'user', 'content': prompt}]
            )
            ai_response = response['message']['content']
            self.session_messages.append({'role': 'user', 'content': prompt})
            self.session_messages.append({'role': 'assistant', 'content': ai_response})
            return ai_response
        except Exception as e:
            return f"Error initializing greeting: {e}"

    def chat(self, user_input):
        self.session_messages.append({'role': 'user', 'content': user_input})
        
        try:
            # Call Ollama with tool support
            response = ollama.chat(
                model=self.model,
                messages=self.session_messages,
                tools=TOOLS
            )
            
            message = response['message']
            
            # Check for native tool calls
            if message.get('tool_calls'):
                self.session_messages.append(message)
                for tool in message['tool_calls']:
                    function_name = tool['function']['name']
                    arguments = tool['function']['arguments']
                    
                    if function_name in TOOL_MAP:
                        # Filter out '<nil>' or empty arguments for functions that don't need them
                        if isinstance(arguments, dict):
                            arguments = {k: v for k, v in arguments.items() if v != '<nil>'}
                        else:
                            arguments = {}
                            
                        try:
                            result = TOOL_MAP[function_name](**arguments)
                            # Log the skill
                            self.memory.log_skill(function_name, str(arguments))
                            
                            self.session_messages.append({
                                'role': 'tool',
                                'content': str(result),
                                'name': function_name
                            })
                        except TypeError as e:
                            # Fallback for functions with no arguments if Ollama sent some
                            if "unexpected keyword argument" in str(e):
                                result = TOOL_MAP[function_name]()
                                self.memory.log_skill(function_name, "None")
                            else:
                                raise e
                
                # Final synthesis call
                final_response = ollama.chat(
                    model=self.model,
                    messages=self.session_messages
                )
                # Ensure the requested confirmation is used
                ai_response = "I've opened that for you, Adithya."
                self.session_messages.append({'role': 'assistant', 'content': ai_response})
                return ai_response
            
            # Fallback: Check if the model output JSON as text
            content = message.get('content', '')
            if '{' in content and ('"name"' in content or '"function"' in content):
                try:
                    json_match = re.search(r'(\{.*\})', content, re.DOTALL)
                    if json_match:
                        raw_json = json_match.group(1)
                        # Clean up common model JSON errors
                        raw_json = raw_json.replace('\'', '"').replace('<nil>', 'null')
                        # Handle trailing commas or extra brackets if model messed up
                        try:
                            tool_data = json.loads(raw_json)
                        except:
                            # Try to fix common malformed JSON
                            raw_json = re.sub(r',\s*\}', '}', raw_json)
                            raw_json = re.sub(r',\s*\]', ']', raw_json)
                            tool_data = json.loads(raw_json)
                        
                        function_name = tool_data.get('name') or tool_data.get('function', {}).get('name')
                        params = tool_data.get('parameters') or tool_data.get('arguments') or {}
                        
                        if isinstance(params, list):
                            # Handle cases like [{"arg1": "val"}] or ["val"]
                            if len(params) > 0 and isinstance(params[0], dict):
                                params = params[0]
                            elif len(params) > 0:
                                # Positional-ish list: ["val1", "val2"]
                                # We'll try to map these to the first few expected args
                                if function_name == 'open_url':
                                    params = {'url': params[0]}
                                elif function_name == 'log_mistake':
                                    params = {'mistake_text': params[0]}
                                else:
                                    params = {}
                        
                        if not isinstance(params, dict):
                            params = {}
                        
                        # Fix hallucinated parameter names
                        if function_name == 'open_url':
                            if 'arg1' in params: params['url'] = params.pop('arg1')
                            if 'link' in params: params['url'] = params.pop('link')
                            if 'arg_name' in params and params['arg_name'] == 'url':
                                params['url'] = params.get('value')
                        
                        if function_name == 'log_mistake':
                            if 'arg1' in params: params['mistake_text'] = params.pop('arg1')
                            if 'mistake' in params: params['mistake_text'] = params.pop('mistake')
                            if 'text' in params: params['mistake_text'] = params.pop('text')
                            if 'arg_name' in params and params['arg_name'] == 'mistake_text':
                                params['mistake_text'] = params.get('value')
                        
                        params = {k: v for k, v in params.items() if v is not None and v != '<nil>'}

                        if function_name in TOOL_MAP:
                            try:
                                result = TOOL_MAP[function_name](**params)
                                # Log the skill
                                self.memory.log_skill(function_name, str(params))
                                
                                # Immediate feedback as requested
                                msg = "I've opened that for you, Adithya."
                                
                                self.session_messages.append({'role': 'assistant', 'content': content})
                                self.session_messages.append({'role': 'tool', 'content': str(result), 'name': function_name})
                                self.session_messages.append({'role': 'assistant', 'content': msg})
                                return msg
                            except Exception as e:
                                return f"Error executing tool: {e}"
                except Exception as e:
                    pass 

            # Default: Just return the content
            ai_response = content
            self.session_messages.append(message)
            return ai_response

        except Exception as e:
            return f"Error in chat: {e}"

    def listen(self):
        """Placeholder for 'Ears' (STT) module."""
        # Future implementation will go here
        pass

    def speak(self, text):
        """Placeholder for 'Voice' (TTS) module."""
        # For now, we just print to console
        print(f"\nAether: {text}\n")

def main():
    # Initialize the agent
    agent = AetherAgent()
    
    # Personal greeting
    greeting = agent.initialize_greeting()
    agent.speak(greeting)

    # Simple interactive loop for testing tools
    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ['exit', 'quit', 'bye']:
                break
            
            response = agent.chat(user_input)
            agent.speak(response)
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()
