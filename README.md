# 🔊 TTS Generation — Kokoro-82M Text-to-Speech

Offline, CPU-friendly Text-to-Speech (TTS) using the **Kokoro-82M** model (`hexgrad/Kokoro-82M`).

* Convert any text to natural-sounding `.wav` speech.
* Play speech live through speakers with streaming playback.
* Switch voices, control speed, and measure generation performance.
* Runs fully on **CPU** — no GPU required.

Sample `.wav` files in this repo (e.g. `heart.wav`, `bella.wav`, `michael.wav`) are pre-generated outputs from these scripts.

---

## 1. Features

* **Two modes:**
  * `tts.py` → text → `.wav` file (offline render).
  * `voice_tts.py` → text → live speaker playback (streaming).
* **High-quality voices** — Kokoro American/British voices (`af_heart`, `af_bella`, `am_michael`, etc.).
* **Speed control** — `--speed 0.5` (slow) to `--speed 2.0` (fast).
* **Chunked generation** — long text is split into chunks, synthesized sequentially, then concatenated.
* **24 kHz output** — standard `soundfile` WAV output.
* **Performance stats** — prints audio duration, generation time, and realtime factor.
* **Streaming playback** — background thread generates while main thread plays (queue `maxsize=3`), so no long silence before audio starts.

---

## 2. Project Structure

```text
tts_generation/
├── tts.py            # Render text to WAV file
├── voice_tts.py      # Speak text live via speakers (streaming)
├── models/
│   └── kokoro-v1_0.pth  # Kokoro-82M weights (313 MB, not in git ideally)
├── *.wav             # Example outputs (heart.wav, bella.wav, michael.wav, ...)
├── pyproject.toml    # Project metadata + dependencies
├── uv.lock           # Locked dependencies
├── .python-version   # Python 3.12
└── README.md         # This file
```

* **What each script does:**
  * `tts.py`:
    1. Loads `KModel` from `models/kokoro-v1_0.pth` on `cpu`.
    2. Wraps it in `KPipeline(lang_code="a")` (`a` = American English).
    3. Calls `pipeline(text, voice=..., speed=...)`.
    4. Collects `audio` chunks (`numpy` arrays), concatenates with `np.concatenate`.
    5. Writes with `soundfile.write(output, audio, 24000)`.
  * `voice_tts.py`:
    1. Same model/pipeline loading.
    2. Starts a daemon `threading.Thread` for generation.
    3. Pushes each audio chunk into `queue.Queue(maxsize=3)`.
    4. Main thread pops chunks and plays with `sounddevice.play(chunk, 24000)` + `sd.wait()`.
    5. `None` sentinel signals end of stream.

---

## 3. Requirements

* **OS:** Linux (tested), macOS / Windows should work.
* **Python:** `>=3.12` (see `.python-version`).
* **Package manager:** `uv` (recommended) or `pip`.
* **System packages:**
  * `espeak-ng` — required by `misaki` / `phonemizer-fork` for G2P (grapheme-to-phoneme).
  * `PortAudio` — required by `sounddevice` for live playback (`voice_tts.py` only).
  * `ffmpeg` (optional) — only if you want to convert WAV → MP3/OGG.

* **Python packages (actual installed):**
  * `kokoro==0.9.4`, `misaki==0.9.4`, `torch==2.14.0+cpu`, `transformers`, `soundfile`, `sounddevice`, `numpy`, `espeakng-loader`, `phonemizer-fork`, `spacy`.

> Note: Current `pyproject.toml` only lists `sounddevice`. For reproducibility, add `kokoro`, `soundfile`, `numpy`, `torch` to dependencies (see Section 4).

---

## 4. Installation

### Step 1 — Install system dependencies

```bash
# Ubuntu / Debian
sudo apt update
sudo apt install -y espeak-ng portaudio19-dev python3-dev
```

```bash
# macOS (Homebrew)
brew install espeak portaudio
```

### Step 2 — Clone and set up Python env

```bash
git clone <your-repo-url> tts_generation
cd tts_generation

# with uv (recommended)
uv sync
source .venv/bin/activate

# OR with pip
python3.12 -m venv .venv
source .venv/bin/activate
pip install kokoro soundfile sounddevice numpy torch --extra-index-url https://download.pytorch.org/whl/cpu
```

### Step 3 — Download the model

Weights must be at `models/kokoro-v1_0.pth` (313 MB):

```bash
mkdir -p models
# Option A: auto-download on first run via HuggingFace (KModel will fetch if missing)
# Option B: manual download
uv run huggingface-cli download hexgrad/Kokoro-82M kokoro-v1_0.pth --local-dir models
```

The code loads it explicitly:

```python
KModel(repo_id="hexgrad/Kokoro-82M", model="models/kokoro-v1_0.pth")
```

---

## 5. How to Use

### A. Render to file — `tts.py`

```bash
# Basic: default voice af_heart, speed 1.0, output output.wav
.venv/bin/python tts.py "Hello, this is a test of Kokoro text to speech."

# Choose voice, speed, and output file
.venv/bin/python tts.py "Good morning! How are you today?" --voice af_bella --speed 1.2 --output bella.wav

# Long-form narration
.venv/bin/python tts.py "Once upon a time in a quiet village..." --voice am_michael --speed 0.9 --output narration.wav
```

* **CLI arguments (`tts.py`):**
  * `text` (positional, required) — one or more words, joined with spaces. Quote multi-word text.
  * `--voice` (default: `af_heart`) — voice ID, e.g. `af_heart`, `af_bella`, `am_fenrir`, `bf_emma`.
  * `--speed` (default: `1.0`, type: `float`) — `0.5` = half speed, `1.5` = 50% faster.
  * `--output` (default: `output.wav`) — output WAV path.

* **Example output:**
```text
Loading Kokoro CPU model...
Voice: af_heart
Speed: 1.0
Output: output.wav

Chunk 1: Hello, this is a test...
Saved: output.wav
Audio duration: 3.45 seconds
Generation time: 1.20 seconds
Realtime factor: 0.35x
```
  * `Realtime factor < 1.0x` = faster than real-time (good).

* **Play the file:**
```bash
aplay output.wav        # Linux
afplay output.wav       # macOS
ffplay output.wav       # ffmpeg
```

### B. Live playback — `voice_tts.py`

```bash
# Speak immediately through speakers
.venv/bin/python voice_tts.py "Hello! I am speaking live without saving a file."

# With different voice + speed
.venv/bin/python voice_tts.py "This streams chunk by chunk." --voice af_sky --speed 1.1
```

* **CLI arguments (`voice_tts.py`):**
  * `text` (positional, required) — text to speak.
  * `--voice` (default: `af_heart`).
  * `--speed` (default: `1.0`).
  * No `--output` — nothing is saved, audio goes to default output device.

* **How streaming works (in points):**
  1. `generation_worker()` runs in a daemon thread.
  2. Each generated chunk is `audio_queue.put(audio)`.
  3. Queue size is `3`, so generation stays max 3 chunks ahead (backpressure).
  4. Main thread loops `audio_queue.get()` → `sd.play(chunk, 24000)` → `sd.wait()`.
  5. `None` in queue = generation done → break loop.

> If you hear no sound: check speakers, default output device, and that `PortAudio` is installed.

---

## 6. Voices

* **Format:** `<language>_<gender>_<name>`
  * `a` = American English, `b` = British English.
  * `f` = female, `m` = male.
* **Tried in this repo (see `*.wav`):**
  * `af_heart` → `heart.wav` (default, balanced female)
  * `af_bella` → `bella.wav`
  * `af_nicole` → `nicole.wav`
  * `af_sarah` → `sarah.wav`
  * `af_sky` → `sky.wav`
  * `bf_emma` → `emma.wav` (British female)
  * `am_fenrir` → `fenrir.wav`
  * `am_michael` → `michael.wav` (American male, long-form)
  * `am_puck` → `puck.wav`
  * `bm_george` → `george.wav` (British male)
* **List all voices programmatically:**
```python
from kokoro import KPipeline
from kokoro.model import KModel
model = KModel(repo_id="hexgrad/Kokoro-82M", model="models/kokoro-v1_0.pth").to("cpu").eval()
pipe = KPipeline(lang_code="a", model=model, device="cpu")
print(pipe.VOICES.keys())  # or check hexgrad/Kokoro-82M on HuggingFace
```

* **Tips:**
  * Female voices (`af_*`) generally sound most natural in Kokoro-82M.
  * Use `--speed 0.85-0.95` for narration / storytelling.
  * Use `--speed 1.1-1.25` for snappy assistant / short prompts.

---

## 7. Configuration Details

* **Language code:** Both scripts hardcode `lang_code="a"` (American English G2P).
  * Change to `"b"` for British English pipeline if using `bf_*` / `bm_*` voices primarily.
* **Device:** Both hardcode `device="cpu"`.
  * To use GPU, set `DEVICE="cuda"` in `voice_tts.py` or `.to("cuda")` in `tts.py` (requires CUDA torch build).
* **Sample rate:** Fixed at `24000 Hz` in both `sf.write(..., 24000)` and `sd.play(..., 24000)`. Do not change — model outputs 24 kHz.
* **Model path:** `MODEL_PATH = "models/kokoro-v1_0.pth"` — edit constant at top of file if you move weights.

---

## 8. Troubleshooting

* **`ModuleNotFoundError: No module named 'kokoro'`**
  * You are not using the venv Python. Run with `.venv/bin/python tts.py ...` or `source .venv/bin/activate` first.
* **`espeak-ng` / `phonemizer` errors**
  * Install system package: `sudo apt install -y espeak-ng`.
  * Verify: `espeak-ng --version`.
* **No audio in `voice_tts.py` / `PortAudio` error**
  * Install: `sudo apt install -y portaudio19-dev`, then `pip install --force-reinstall sounddevice`.
  * Check devices: `.venv/bin/python -c "import sounddevice as sd; print(sd.query_devices())"`.
* **Model download slow / fails**
  * Pre-download with `huggingface-cli` (see Section 4) and confirm `models/kokoro-v1_0.pth` is ~313 MB.
* **Choppy live playback**
  * CPU is slow or text is very long. Try shorter sentences, or use `tts.py` to render to file first.
* **`pyproject.toml` incomplete**
  * If fresh `uv sync` does not install `kokoro`/`torch`/`soundfile`, install manually (see Section 4, Step 2).

---

## 9. Future Improvements

* [ ] Add `--lang b` / `--device cuda` CLI flags instead of hardcoded values.
* [ ] Add `--input file.txt` to synthesize long documents.
* [ ] Save streaming output to file *and* speakers simultaneously.
* [ ] Fix `pyproject.toml` to list all real dependencies (`kokoro`, `torch`, `soundfile`, `numpy`).
* [ ] Add MP3 export via `ffmpeg` / `pydub`.
* [ ] Add voice preview script that renders one sentence in all voices.

---

## 10. Credits

* Model: [hexgrad/Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) (Apache 2.0).
* Pipeline: `kokoro` PyPI package (`KModel`, `KPipeline`), `misaki` for G2P.
* Audio I/O: `soundfile`, `sounddevice`, `numpy`, `torch` (CPU).
