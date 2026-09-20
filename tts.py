import argparse
import time
import numpy as np
import soundfile as sf

from kokoro.model import KModel
from kokoro.pipeline import KPipeline

MODEL_PATH = "models/kokoro-v1_0.pth"

parser = argparse.ArgumentParser()
parser.add_argument("text", nargs="+")
parser.add_argument("--voice", default="af_heart")
parser.add_argument("--speed", type=float, default=1.0)
parser.add_argument("--output", default="output.wav")
args = parser.parse_args()

text = " ".join(args.text)

print("Loading Kokoro CPU model...")

model = KModel(
    repo_id="hexgrad/Kokoro-82M",
    model=MODEL_PATH,
).to("cpu").eval()

pipeline = KPipeline(
    lang_code="a",
    model=model,
    device="cpu",
)

print(f"Voice: {args.voice}")
print(f"Speed: {args.speed}")
print(f"Output: {args.output}")
print()

start = time.perf_counter()

audio_chunks = []

generator = pipeline(
    text,
    voice=args.voice,
    speed=args.speed,
)

for i, (gs, ps, audio) in enumerate(generator):
    print(f"Chunk {i + 1}: {ps}")
    audio_chunks.append(audio)

# Combine all chunks
audio = np.concatenate(audio_chunks)

sf.write(args.output, audio, 24000)

elapsed = time.perf_counter() - start
duration = len(audio) / 24000

print()
print(f"Saved: {args.output}")
print(f"Audio duration: {duration:.2f} seconds")
print(f"Generation time: {elapsed:.2f} seconds")
print(f"Realtime factor: {elapsed / duration:.2f}x")