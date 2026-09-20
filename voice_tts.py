import argparse
import queue
import threading
import sounddevice as sd
from kokoro.model import KModel
from kokoro.pipeline import KPipeline

MODEL_PATH = "models/kokoro-v1_0.pth"

parser = argparse.ArgumentParser()
parser.add_argument("text", nargs="+")
parser.add_argument("--voice", default="af_heart")
parser.add_argument("--speed", type=float, default=1.0)
args = parser.parse_args()

text = " ".join(args.text)

# Choose "cuda" if you have an NVIDIA GPU, otherwise stick to "cpu"
DEVICE = "cpu" 

print(f"Loading Kokoro model on {DEVICE}...")
model = KModel(repo_id="hexgrad/Kokoro-82M", model=MODEL_PATH).to(DEVICE).eval()
pipeline = KPipeline(lang_code="a", model=model, device=DEVICE)

# Create a queue to hold audio chunks ready for playback
audio_queue = queue.Queue(maxsize=3)

def generation_worker():
    """Generates audio in the background and shoves it into the queue."""
    generator = pipeline(text, voice=args.voice, speed=args.speed)
    for gs, ps, audio in generator:
        audio_queue.put(audio) # This will block if the queue is full (max 3 chunks ahead)
    audio_queue.put(None) # Signal that generation is entirely finished

# Start the AI generation in a separate background thread
threading.Thread(target=generation_worker, daemon=True).start()

print("🗣️ Speaking... (Generation running seamlessly in background)")

# Main thread just focuses on playing audio smoothly
while True:
    audio_chunk = audio_queue.get()
    if audio_chunk is None:
        break # No more audio chunks left
        
    sd.play(audio_chunk, 24000)
    sd.wait()

print("\n✨ Finished speaking!")
