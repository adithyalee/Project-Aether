import os
import sounddevice as sd
from kokoro_onnx import Kokoro

# Path to the models (will be created in the .models folder)
MODEL_PATH = os.path.join(os.path.dirname(__file__), "kokoro-v1.0.onnx")
VOICES_PATH = os.path.join(os.path.dirname(__file__), "voices-v1.0.bin")

class AetherTTS:
    def __init__(self):
        if not os.path.exists(MODEL_PATH):
            print("[Aether/TTS] Warning: Kokoro model missing. Please download it to d:\\Project Aether\\tts\\")
            self.kokoro = None
            return
        
        print("[Aether/TTS] Initializing Kokoro Voice Engine...")
        self.kokoro = Kokoro(MODEL_PATH, VOICES_PATH)

    def speak(self, text, voice="af_bella"):
        """Generates and plays audio for the given text."""
        if not self.kokoro:
            print(f"Aether (No Voice): {text}")
            return

        samples, sample_rate = self.kokoro.create(text, voice=voice, speed=1.1, lang="en-us")
        sd.play(samples, sample_rate)
        sd.wait()

if __name__ == "__main__":
    tts = AetherTTS()
    tts.speak("Hello Adithya, I am Aether. My voice is now local and fast.")
