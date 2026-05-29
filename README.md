# Byulie

**A personal, local voice assistant built on Windows — for learning, not distribution.**

Byulie is my hands-on exploration of how a voice AI pipeline fits together: speech recognition, language modeling, speech synthesis, and lightweight memory — all running on my own machine without paid or hosted AI APIs.

---

## Contents

- [Overview](#overview)
- [Pipeline](#pipeline)
- [Stack](#stack)
- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Configuration](#configuration)
- [Usage](#usage)
- [Troubleshooting](#troubleshooting)
- [Learning goals](#learning-goals)
- [Acknowledgments](#acknowledgments)

---

## Overview

Byulie listens through the microphone, remembers conversation context in a local JSON file, replies via a local Ollama model, and speaks through a local GPT-SoVITS server.

| Principle | Detail |
| --- | --- |
| **Scope** | Personal study project — private, experimental, not maintained for public use |
| **Platform** | Windows 11 64-bit (primary target) |
| **Privacy** | No paid APIs, no hosted inference — Ollama, Faster-Whisper, and GPT-SoVITS stay on `127.0.0.1` |
| **Config** | `character_config.yaml` controls LLM, ASR, TTS, prompts, and memory |

---

## Pipeline

```mermaid
flowchart LR
    A[Microphone] --> B[Faster-Whisper]
    B --> C[Ollama LLM]
    C --> D[GPT-SoVITS]
    D --> E[Audio playback]
    C --> F[JSON memory]
```

1. Audio is captured from the microphone.
2. **Faster-Whisper** transcribes speech locally.
3. **Ollama** (`qwen3:4b` by default) generates a reply.
4. **GPT-SoVITS** synthesizes voice output locally.
5. The exchange is appended to `byulie_chat_history.json`.

---

## Stack

| Layer | Default | Role |
| --- | --- | --- |
| OS | Windows 11 | Development and runtime environment |
| LLM | Ollama + `qwen3:4b` | Local chat completion |
| ASR | Faster-Whisper `base.en` (CPU) | Speech-to-text |
| TTS | GPT-SoVITS @ `:9880` | Text-to-speech |
| Memory | `byulie_chat_history.json` | Conversation history |
| UI | Gradio (`client/app.py`) | Optional local web interface |

**Suggested hardware:** 16 GB RAM, SSD, working mic/speakers. An NVIDIA GPU with 8 GB+ VRAM helps; on 8 GB VRAM, keep ASR on CPU and start with `qwen3:4b`.

---

## Prerequisites

Install and verify before setup:

| Requirement | Verify |
| --- | --- |
| Python 3.10 or 3.11 (PATH enabled) | `python --version` |
| FFmpeg on PATH | `ffmpeg -version` |
| [Ollama for Windows](https://ollama.com/download/windows) | `ollama --version` |
| GPT-SoVITS (local install + HTTP server) | Endpoint reachable at configured URL |
| NVIDIA driver *(optional)* | `nvidia-smi` |

---

## Setup

Run from the **project root** in PowerShell.

### 1 · Virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

If activation is blocked:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 2 · Dependencies

```powershell
pip install -r requirements.txt
pip install -r extra-req.txt
```

### 3 · Ollama model

```powershell
ollama pull qwen3:4b
ollama serve
```

Confirm in a second window: `ollama run qwen3:4b` (exit when done).

### 4 · GPT-SoVITS

Start your local GPT-SoVITS server so it matches the default endpoint:

```text
http://127.0.0.1:9880/tts
```

Leave it running while Byulie is active.

---

## Configuration

Settings live in `character_config.yaml` at the project root.

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

| Key | Must align with |
| --- | --- |
| `llm.base_url` | Running Ollama instance |
| `llm.model` | Model pulled via `ollama pull` |
| `tts.endpoint` | Local GPT-SoVITS server URL |
| `tts.ref_audio_path` | Existing reference audio on disk |
| `asr.device` | `cpu` recommended when VRAM is tight |

---

## Usage

Activate the virtual environment first: `.\.venv\Scripts\Activate.ps1`

### Voice chat (CLI)

```powershell
python server/main_chat.py
```

Press **Enter** to start recording, **Enter** again to stop. Byulie transcribes, replies, synthesizes speech, and updates memory.

### Web interface (optional)

```powershell
python client/app.py
```

Open the URL Gradio prints (typically `http://127.0.0.1:7860`). The UI binds to localhost only.

Supports typed chat, microphone input, model/temperature controls, system prompt editing, and emotion/tone hints for TTS.

---

## Troubleshooting

<details>
<summary><strong>Microphone not detected</strong></summary>

- Confirm input device: **Settings → System → Sound → Input**
- Allow mic access: **Settings → Privacy & security → Microphone**
- Close apps holding exclusive mic access; test with Windows Sound Recorder
- Verify FFmpeg: `ffmpeg -version`

</details>

<details>
<summary><strong>Ollama not reachable</strong></summary>

- `ollama --version` · `ollama list` · `ollama pull qwen3:4b`
- Start manually: `ollama serve`
- Config must point to `http://127.0.0.1:11434` unless you changed the port

</details>

<details>
<summary><strong>GPT-SoVITS / no voice output</strong></summary>

- Confirm the TTS server is running at `http://127.0.0.1:9880/tts` (or your configured endpoint)
- Check `tts.ref_audio_path` exists and language fields match your model
- Restart GPT-SoVITS after changing reference audio or ports

</details>

<details>
<summary><strong>Faster-Whisper download or cache errors</strong></summary>

- Ensure venv is active and dependencies are installed
- Allow initial model download; free disk space if needed
- Fallback in config:

```yaml
asr:
  model: "tiny.en"
  device: "cpu"
  compute_type: "float32"
```

</details>

<details>
<summary><strong>CUDA / VRAM issues</strong></summary>

- Keep ASR on CPU; stay on `qwen3:4b` until stable
- Monitor VRAM: `nvidia-smi`
- Close other GPU-heavy applications before running LLM + TTS together

</details>

---

## Learning goals

This repository documents work I am doing as a **Computer Science student** to understand applied ML systems end to end:

- Wiring **ASR → LLM → TTS** into one coherent loop
- Running inference **locally** and managing model/resource tradeoffs
- Persisting **conversation state** without external databases (MVP)
- Building a minimal **UI layer** (Gradio) on top of the same backend
- Iterating on prompts, voice reference audio, and configuration-driven behavior

Planned personal experiments include lower-latency mic input, richer memory, and tighter emotion control for synthesis.

| Status | Item |
| --- | --- |
| Done | Gradio web UI |
| Done | Emotion / tone controls in UI |
| In progress | Voice chat loop refinement |
| Planned | Live microphone mode |
| Planned | SQLite memory store |
| Planned | VRM frontend exploration |

---

## Acknowledgments

Built with open tools I am learning from — not a fork or product release:

- [Ollama](https://ollama.com/) — local LLM runtime
- [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper) — speech recognition
- [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) — voice synthesis

---

<p align="center"><sub>Private personal project · Windows · local inference only</sub></p>
