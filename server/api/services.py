"""Shared services for the Byulie web API."""

import uuid
from pathlib import Path

import requests

from server.api.config_store import get_asr_defaults, get_default_system_prompt, get_llm_defaults, get_tts_defaults
from server.local_only import assert_local_url
from server.paths import AUDIO_DIR
from server.process.asr_func.asr_push_to_talk import transcribe_audio_file
from server.process.llm_funcs import llm_scr
from server.process.tts_func.sovits_ping import sovits_gen

WEB_AUDIO_DIR = AUDIO_DIR / "web_ui"
_whisper_model = None
_whisper_signature = None

EMOTIONS = ["Neutral", "Cheerful", "Soft", "Dramatic", "Sleepy", "Annoyed"]


def build_tone_instruction(emotion: str | None, tone: str | None) -> str:
    parts = []
    if emotion and emotion != "Neutral":
        parts.append(f"emotion: {emotion.lower()}")
    if tone and tone.strip():
        parts.append(f"tone: {tone.strip()}")
    if not parts:
        return ""
    return "When writing the assistant reply, use this voice direction for TTS: " + "; ".join(parts) + "."


def effective_system_prompt(base_prompt: str | None, emotion: str | None, tone: str | None) -> str:
    prompt = (base_prompt or "").strip() or get_default_system_prompt()
    tone_instruction = build_tone_instruction(emotion, tone)
    if tone_instruction:
        return f"{prompt}\n\n{tone_instruction}"
    return prompt


def get_whisper_model():
    global _whisper_model, _whisper_signature
    asr = get_asr_defaults()
    signature = (asr.get("model"), asr.get("device"), asr.get("compute_type"))
    if _whisper_model is None or _whisper_signature != signature:
        from faster_whisper import WhisperModel

        _whisper_model = WhisperModel(
            asr.get("model", "base.en"),
            device=asr.get("device", "cpu"),
            compute_type=asr.get("compute_type", "float32"),
        )
        _whisper_signature = signature
    return _whisper_model


def reset_whisper_model():
    global _whisper_model, _whisper_signature
    _whisper_model = None
    _whisper_signature = None


def check_ollama() -> dict:
    llm = get_llm_defaults()
    raw_url = llm.get("base_url", "http://127.0.0.1:11434")
    try:
        base_url = assert_local_url(raw_url, "llm.base_url")
        response = requests.get(f"{base_url}/api/tags", timeout=3)
        response.raise_for_status()
        models = [m.get("name") for m in response.json().get("models", [])]
        return {"ok": True, "url": base_url, "models": models}
    except (requests.RequestException, ValueError) as exc:
        return {"ok": False, "url": raw_url, "error": str(exc)}


def check_tts() -> dict:
    tts = get_tts_defaults()
    raw_endpoint = tts.get("endpoint", "http://127.0.0.1:9880/tts")
    try:
        endpoint = assert_local_url(raw_endpoint, "tts.endpoint")
        response = requests.options(endpoint, timeout=3)
        return {"ok": response.status_code < 500, "endpoint": endpoint}
    except (requests.RequestException, ValueError) as exc:
        return {"ok": False, "endpoint": raw_endpoint, "error": str(exc)}


def run_chat_pipeline(
    user_text: str,
    *,
    model: str | None = None,
    temperature: float | None = None,
    max_output_tokens: int | None = None,
    system_prompt: str | None = None,
    emotion: str | None = None,
    tone: str | None = None,
) -> dict:
    llm = get_llm_defaults()
    prompt = effective_system_prompt(system_prompt, emotion, tone)

    assistant_text = llm_scr.llm_response(
        user_text,
        model=model or llm.get("model"),
        temperature=temperature if temperature is not None else llm.get("temperature"),
        max_output_tokens=max_output_tokens or llm.get("max_output_tokens"),
        system_prompt=prompt,
    )

    WEB_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    audio_id = f"byulie_{uuid.uuid4().hex}"
    output_path = WEB_AUDIO_DIR / f"{audio_id}.wav"
    audio_path = sovits_gen(assistant_text, output_path)

    return {
        "assistant_text": assistant_text,
        "audio_url": f"/api/audio/{audio_id}.wav" if audio_path else None,
        "tts_ok": audio_path is not None,
    }


def run_audio_pipeline(
    audio_path: Path,
    *,
    model: str | None = None,
    temperature: float | None = None,
    max_output_tokens: int | None = None,
    system_prompt: str | None = None,
    emotion: str | None = None,
    tone: str | None = None,
) -> dict:
    transcript = transcribe_audio_file(get_whisper_model(), audio_path)
    if not transcript.strip():
        return {
            "transcript": "",
            "assistant_text": "",
            "audio_url": None,
            "tts_ok": False,
            "error": "No speech detected in the recording.",
        }

    result = run_chat_pipeline(
        transcript,
        model=model,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        system_prompt=system_prompt,
        emotion=emotion,
        tone=tone,
    )
    result["transcript"] = transcript
    return result


def apply_config_reload():
    llm_scr.reload_from_config()
    reset_whisper_model()
