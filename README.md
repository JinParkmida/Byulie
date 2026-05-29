# Byulie

Local voice AI assistant for **Windows 11 64-bit** — [github.com/JinParkmida/Byulie](https://github.com/JinParkmida/Byulie).

Byulie is an anime-focused local AI assistant project. She listens, remembers your conversations, responds with a local Ollama language model, and speaks through a local GPT-SoVITS voice server.

> **MVP privacy/cost rule:** Byulie's default MVP uses **no paid APIs** and **no hosted AI services**. Ollama, Faster-Whisper, GPT-SoVITS, and the JSON memory file all run locally on your Windows 11 64-bit machine.

## What Byulie Does

Byulie is designed to behave like a voice-enabled desktop companion:

1. You speak into your microphone.
2. Faster-Whisper transcribes your speech locally.
3. Ollama runs `qwen3:4b` locally to generate Byulie's response.
4. GPT-SoVITS synthesizes the response through a local TTS server.
5. The conversation is saved to local JSON memory.

## Default MVP Stack

| Layer | Default | Notes |
| --- | --- | --- |
| Operating system | Windows 11 64-bit | Primary supported target for this guide |
| Local LLM | Ollama + `qwen3:4b` | Local model runtime and default chat model |
| Speech-to-text | Faster-Whisper | Local ASR; default config uses `base.en` on CPU |
| Text-to-speech | Local GPT-SoVITS server | Local voice server expected at the configured endpoint |
| Memory | Local JSON file | Default conversation history stored in `byulie_chat_history.json` |
| Configuration | `character_config.yaml` | Controls LLM, ASR, TTS, prompt, and memory settings |

## Windows 11 64-bit Prerequisites

Byulie is intentionally targeted at Windows 11 64-bit. Install these before running Byulie:

- **Windows 11 64-bit**.
- **64-bit Python 3.10 or Python 3.11 for Windows**.
  - During installation, enable **Add Python to PATH**.
  - Verify with `python --version` in PowerShell.
  - The launcher rejects 32-bit Python because the audio and local AI dependencies are intended for 64-bit Windows.
- **Git for Windows**.
  - Verify with `git --version`.
- **FFmpeg on PATH**.
  - Install FFmpeg and make sure `ffmpeg.exe` is available from PowerShell.
  - Verify with `ffmpeg -version`.
- **Ollama for Windows**.
  - Install from <https://ollama.com/download/windows>.
  - Verify with `ollama --version`.
- **GPT-SoVITS installed locally**.
  - Byulie expects a local GPT-SoVITS HTTP server, not a hosted TTS service.
- **Optional NVIDIA GPU acceleration**.
  - Install a current NVIDIA driver for your GPU.
  - Install CUDA only if the local components you run require it.
  - If VRAM is limited, keep Faster-Whisper on CPU and use smaller Ollama models.

## Recommended Hardware

Byulie can run with CPU-heavy defaults, but voice generation and local LLM inference are smoother with a dedicated NVIDIA GPU.

Suggested starting point:

- 16 GB system RAM or more.
- NVIDIA GPU with 8 GB VRAM or more for a more comfortable local AI workflow.
- SSD storage for model caches and faster startup.
- Working microphone and speakers/headphones.

For 8 GB VRAM systems, start with `qwen3:4b` before trying larger local models. Running a larger LLM, Faster-Whisper on GPU, and GPT-SoVITS at the same time may exceed available VRAM.

## Configuration

Byulie reads runtime settings from `character_config.yaml`.

```yaml
character:
  name: Byulie

history_file: byulie_chat_history.json

llm:
  provider: ollama
  base_url: "http://127.0.0.1:11434"
  model: "qwen3:4b"
  temperature: 0.8
  max_output_tokens: 512
  context_tokens: 8192
  timeout_seconds: 120

asr:
  model: "base.en"
  device: "cpu"
  compute_type: "float32"

presets:
  default:
    system_prompt: |
      You are a helpful assistant named Byulie.
      You speak like a snarky anime girl.
      Always refer to the user as "senpai".

tts:
  provider: gpt-sovits
  endpoint: "http://127.0.0.1:9880/tts"
  text_lang: en
  prompt_lang: en
  ref_audio_path: "character_files/main_sample.wav"
  prompt_text: "This is a sample voice for you to just get started with because it sounds kind of cute but just make sure this doesn't have long silences."
```

Important defaults:

- `llm.base_url` must match your local Ollama server.
- `llm.model` should match the model you pulled with Ollama.
- `asr.model` controls the Faster-Whisper model downloaded and cached locally.
- `asr.device: "cpu"` is the safest default for conserving GPU VRAM.
- `tts.endpoint` must match your local GPT-SoVITS server URL.
- `history_file` controls where local JSON memory is stored.

## Step-by-Step Windows Setup

Run these commands from **PowerShell on Windows 11 64-bit** unless noted otherwise. The recommended launcher validates Windows 11 64-bit and 64-bit Python before starting Byulie.

### 1. Clone the Repository

```powershell
git clone https://github.com/JinParkmida/Byulie.git
cd Byulie
```

If you already cloned the repository, open PowerShell in the project root instead.

### 2. Create a Python Virtual Environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

If PowerShell blocks activation scripts, run this once for your user account and then activate again:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 3. Install Dependencies

```powershell
pip install -r requirements.txt
```

If your environment uses an additional project-specific dependency file, install it after the main requirements file:

```powershell
pip install -r extra-req.txt
```

Only run the second command if `extra-req.txt` exists in your checkout.

### 4. Pull the Default Ollama Model

```powershell
ollama pull qwen3:4b
```

This downloads the default local LLM used by Byulie.

### 5. Start Ollama

Ollama for Windows often runs in the background after installation. If it is not already running, start it with:

```powershell
ollama serve
```

In a second PowerShell window, confirm the model responds:

```powershell
ollama run qwen3:4b
```

Exit the interactive Ollama prompt when the model check is complete.

### 6. Start the Local GPT-SoVITS Server

Start GPT-SoVITS using your local GPT-SoVITS installation instructions. Configure it so the TTS endpoint matches Byulie's default config:

```text
http://127.0.0.1:9880/tts
```

Keep the GPT-SoVITS server running while Byulie is active.

### 7. Run Byulie

The easiest Windows launcher is the included batch file. Double-click it from File Explorer, or run it from PowerShell in the project root:

```powershell
.\start-byulie.bat
```

The launcher calls `scripts/start_byulie.ps1`, validates Windows 11 64-bit, creates `.venv` with 64-bit Python if needed, installs `requirements.txt`, checks whether Ollama for Windows is available, and then starts the voice chat. You can also run the Python entry point manually after activating the virtual environment:

```powershell
python server/main_chat.py
```

Expected runtime flow:

1. Byulie starts the chat loop.
2. The microphone captures your speech.
3. Faster-Whisper transcribes the recorded audio locally.
4. Ollama generates a local response with `qwen3:4b`.
5. GPT-SoVITS generates the voice response locally.
6. Byulie plays the generated audio and updates local JSON memory.

### 8. Launch the Local Web Interface (Optional)

From the repository root on Windows, launch the web interface with:

```powershell
.\start-byulie.bat -Mode web
```

You can also run it manually with the virtual environment activated:

```powershell
python client/app.py
```

Gradio prints a local browser URL such as:

```text
http://127.0.0.1:7860
```

Open that URL in your Windows browser. The interface binds to `127.0.0.1` only — no cloud hosting, analytics, or paid APIs.

The web UI supports typed chat, microphone upload/recording with Faster-Whisper transcription, Byulie's text and voice responses via your local GPT-SoVITS server, an Ollama model selector, temperature and token limits, a system prompt editor, and emotion/tone controls for spoken style.

## Troubleshooting

### Git Says the Branch Is Invalid or README Is Unmerged

Symptoms:

- GitHub says the pull request branch is invalid, deleted, or cannot be compared.
- `git status` says `Your branch is based on 'origin/main', but the upstream is gone.`
- `git status` shows `Unmerged paths` with `both modified: README.md`.
- Many files are listed under `Changes to be committed`, but the pull request cannot be created yet.

Checks and fixes:

1. Stay in the Byulie repository and clear the deleted upstream pointer:

```powershell
git branch --unset-upstream
```

2. Resolve the README merge conflict before pushing. Open `README.md`, remove conflict markers such as `<<<<<<<`, `=======`, and `>>>>>>>`, keep the final text you want, then stage it:

```powershell
git add README.md
```

3. Commit the staged launcher, web UI, server, and README changes:

```powershell
git commit -m "Update Byulie Windows 11 launcher"
```

4. If you want the changes directly on `main`, push `main` after the conflict is committed:

```powershell
git push -u origin main
```

5. If GitHub still will not create a pull request from `main`, create and push a separate branch. Pull requests must compare two different branches, so do not open a PR from `main` into `main`:

```powershell
git checkout -b windows-11-launcher
git push -u origin windows-11-launcher
```

Then create the pull request from `windows-11-launcher` into `main`.

### Windows 11 64-bit Validation Fails

Symptoms:

- `start-byulie.bat` says Byulie is configured for Windows 11 64-bit.
- The launcher says Python 3.10 or 3.11 64-bit was not found.
- The launcher says the existing `.venv` is not using 64-bit Python.

Checks and fixes:

1. Run Byulie on Windows 11 64-bit, not WSL, Linux, macOS, or 32-bit Windows.
2. Install 64-bit Python 3.10 or 3.11 from the official Windows installer and enable **Add Python to PATH**.
3. If `.venv` was created with the wrong Python, delete it and rerun:

```powershell
Remove-Item -Recurse -Force .\.venv
.\start-byulie.bat
```

4. Advanced developers can set `BYULIE_SKIP_WINDOWS_CHECK=1` only when intentionally running checks outside the supported Windows target.

### Microphone Not Detected

Symptoms:

- Byulie starts but never records your voice.
- Recording fails immediately.
- Transcription is empty even though you spoke.

Checks and fixes:

1. Open **Windows Settings → System → Sound → Input** and confirm the correct microphone is selected.
2. Open **Windows Settings → Privacy & security → Microphone** and allow microphone access for desktop apps.
3. Close other applications that may have exclusive microphone control.
4. Test the microphone with Windows Sound Recorder or another local recording app.
5. If you use a USB microphone, unplug it, plug it back in, and restart PowerShell.
6. Confirm FFmpeg is on PATH with:

```powershell
ffmpeg -version
```

### Ollama Not Reachable

Symptoms:

- Requests to the LLM fail.
- The app cannot connect to `127.0.0.1:11434`.
- Model responses never arrive.

Checks and fixes:

1. Confirm Ollama is installed:

```powershell
ollama --version
```

2. Confirm the default model is installed:

```powershell
ollama list
```

3. Pull the model if it is missing:

```powershell
ollama pull qwen3:4b
```

4. Start Ollama manually if needed:

```powershell
ollama serve
```

5. Confirm `character_config.yaml` points to:

```text
http://127.0.0.1:11434
```

6. If another process uses port `11434`, stop that process or reconfigure Ollama and Byulie to use the same port.

### GPT-SoVITS Endpoint Not Reachable

Symptoms:

- Text responses work, but no voice audio is generated.
- The app reports a TTS connection error.
- The configured `/tts` endpoint does not respond.

Checks and fixes:

1. Make sure the GPT-SoVITS local server is running.
2. Confirm the server is listening on the same endpoint configured in `character_config.yaml`:

```text
http://127.0.0.1:9880/tts
```

3. Check whether GPT-SoVITS uses a different port in your local setup and update `tts.endpoint` if necessary.
4. Verify `tts.ref_audio_path` points to an existing local reference audio file.
5. Confirm `tts.text_lang` and `tts.prompt_lang` match the languages expected by your GPT-SoVITS model.
6. Restart GPT-SoVITS after changing model, reference audio, or port settings.

### Faster-Whisper Model Download or Cache Issues

Symptoms:

- First startup fails while loading the ASR model.
- Download errors appear for the Faster-Whisper model.
- Startup works on one network but not another.

Checks and fixes:

1. Confirm the virtual environment is activated.
2. Confirm Python dependencies are installed:

```powershell
pip install -r requirements.txt
```

3. Check that your internet connection allows the initial model download.
4. Free disk space for model cache files.
5. Try a smaller ASR model in `character_config.yaml`, such as:

```yaml
asr:
  model: "tiny.en"
  device: "cpu"
  compute_type: "float32"
```

6. If the cache is corrupted, remove the affected local model cache directory and let Faster-Whisper download it again.

### CUDA and VRAM Limitations

Symptoms:

- GPU out-of-memory errors.
- Ollama becomes slow or unloads models.
- GPT-SoVITS fails when the LLM is already running.
- Faster-Whisper fails with GPU/CUDA errors.

Checks and fixes:

1. Update to a current NVIDIA driver.
2. Start with CPU ASR:

```yaml
asr:
  device: "cpu"
  compute_type: "float32"
```

3. Keep the default LLM model at `qwen3:4b` until the full pipeline is stable.
4. Close other GPU-heavy applications, including games, video editors, and browser tabs using hardware acceleration.
5. Use Task Manager or `nvidia-smi` to check VRAM usage:

```powershell
nvidia-smi
```

6. If CUDA libraries are mismatched, reinstall the NVIDIA driver and use dependency versions compatible with your installed CUDA runtime.
7. Prefer smaller models when running LLM, ASR, and TTS simultaneously on limited VRAM.

## Roadmap

Planned improvements:

- **GUI:** desktop interface for chat, configuration, model status, and voice controls.
- **Live microphone mode:** lower-latency continuous or voice-activated microphone input beyond the current recording loop.
- **Emotion controls:** adjustable speaking style, tone, pacing, and emotional presets for GPT-SoVITS output.
- **Memory upgrades:** richer long-term memory, summarization, search, and possible migration from JSON to SQLite or another local store.
- **Model tuning:** better presets for low-VRAM, balanced, and high-quality local model configurations.

## TODO / Future Improvements

- [x] Local Gradio web interface
- [ ] Live microphone input support
- [x] Emotion or tone control in the web interface
- [ ] VRM model frontend
- [ ] SQLite memory store
- [ ] Optional local model presets for low-VRAM and higher-quality modes

## Credits

- Voice synthesis powered by [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS).
- Speech recognition powered by [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper).
- Local LLM runtime powered by [Ollama](https://ollama.com/).

## License

MIT — feel free to clone, modify, and build your own local Byulie assistant.
