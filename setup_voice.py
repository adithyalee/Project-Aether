import os
import urllib.request

def download_voice_models():
    base_url = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
    files = ["kokoro-v1.0.onnx", "voices-v1.0.bin"]
    target_dir = r"d:\Project Aether\tts"
    
    os.makedirs(target_dir, exist_ok=True)
    
    for f in files:
        target_path = os.path.join(target_dir, f)
        # We'll also update the code to look for voices-v1.0.bin
        if os.path.exists(target_path):
            print(f"[OK] {f} already exists.")
            continue
            
        print(f"[FETCH] Downloading {f} (this may take a minute)...")
        urllib.request.urlretrieve(base_url + f, target_path)
        print(f"[DONE] {f} downloaded.")

if __name__ == "__main__":
    download_voice_models()
    print("\n[SUCCESS] Aether's voice box is now fully equipped!")
