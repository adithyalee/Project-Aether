import os
import numpy as np
import sounddevice as sd
import logging
from faster_whisper import WhisperModel

logging.getLogger("faster_whisper").setLevel(logging.ERROR)

# small = significantly better accuracy than base, still fast on CPU
MODEL_SIZE = "small"

class AetherSTT:
    def __init__(self):
        print(f"[Aether/STT] Loading Whisper {MODEL_SIZE}...")
        # main.py sets HF_HUB_OFFLINE=1 globally — temporarily lift it so the
        # model can download on first run, then restore it.
        _prev = os.environ.pop("HF_HUB_OFFLINE", None)
        try:
            self.model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
        finally:
            if _prev is not None:
                os.environ["HF_HUB_OFFLINE"] = _prev
        self.sample_rate = 16000

    def listen_and_transcribe(self, duration=6):
        print(f"[Aether/STT] Listening for {duration} seconds...")
        audio = sd.rec(
            int(duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=1,
            dtype='float32'
        )
        sd.wait()
        audio = audio.flatten()

        # Bail early on near-silence to avoid garbage transcriptions
        rms = float(np.sqrt(np.mean(audio ** 2)))
        if rms < 0.002:
            return ""

        prompt = (
            "Commands for Aether AI assistant: open YouTube, launch Spotify, "
            "play music, clear cache, switch to work mode, stop, done, goodbye, "
            "how are you, what time is it."
        )
        segments, _ = self.model.transcribe(
            audio,
            language="en",
            beam_size=3,                    # was 1 (greedy); 3 is more accurate
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 500},
            initial_prompt=prompt,
            condition_on_previous_text=False,   # prevents context bleed between turns
            no_speech_threshold=0.4,            # discard low-confidence non-speech
            compression_ratio_threshold=2.4,    # filter out garbage/noise transcripts
        )
        text = " ".join(seg.text for seg in segments).strip()
        return text


if __name__ == "__main__":
    stt = AetherSTT()
    print(f"Transcribed: {stt.listen_and_transcribe()}")
