"""Local-only Gradio web interface for Byulie."""

from pathlib import Path
import sys
import uuid

import gradio as gr
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from server.process.asr_func.asr_push_to_talk import transcribe_audio_file
from server.process.llm_funcs.llm_scr import llm_response
from server.process.tts_func.sovits_ping import sovits_gen

CONFIG_PATH = REPO_ROOT / "character_config.yaml"
AUDIO_DIR = REPO_ROOT / "audio" / "web_ui"

with CONFIG_PATH.open("r") as f:
    CHAR_CONFIG = yaml.safe_load(f)

LLM_CONFIG = CHAR_CONFIG.get("llm", {})
ASR_CONFIG = CHAR_CONFIG.get("asr", {})
CHARACTER_NAME = CHAR_CONFIG.get("character", {}).get("name", "Byulie")
DEFAULT_SYSTEM_PROMPT = CHAR_CONFIG["presets"]["default"]["system_prompt"]
DEFAULT_MODEL = LLM_CONFIG.get("model", "qwen3:4b")
DEFAULT_TEMPERATURE = LLM_CONFIG.get("temperature", 0.8)
DEFAULT_MAX_OUTPUT_TOKENS = LLM_CONFIG.get("max_output_tokens", 512)
MODEL_CHOICES = list(dict.fromkeys([DEFAULT_MODEL, "qwen3:8b", "llama3.2:3b", "mistral:7b"]))

_whisper_model = None


def get_whisper_model():
    """Load the configured Faster-Whisper model once, when microphone input is used."""
    global _whisper_model

    if _whisper_model is None:
        from faster_whisper import WhisperModel

        _whisper_model = WhisperModel(
            ASR_CONFIG.get("model", "base.en"),
            device=ASR_CONFIG.get("device", "cpu"),
            compute_type=ASR_CONFIG.get("compute_type", "float32"),
        )

    return _whisper_model


def normalize_text(value):
    """Return stripped text for optional Gradio text inputs."""
    return value.strip() if isinstance(value, str) else ""


def build_tone_instruction(emotion, tone):
    """Build a local style instruction used by the LLM and spoken output."""
    parts = []
    if emotion and emotion != "Neutral":
        parts.append(f"emotion: {emotion.lower()}")
    clean_tone = normalize_text(tone)
    if clean_tone:
        parts.append(f"tone: {clean_tone}")

    if not parts:
        return ""

    return (
        f"When writing {CHARACTER_NAME}'s reply, use this voice direction for TTS: "
        + "; ".join(parts)
        + "."
    )


def get_user_text(text_input, microphone_audio):
    """Prefer typed text; otherwise transcribe the uploaded microphone recording."""
    typed_text = normalize_text(text_input)
    if typed_text:
        return typed_text, ""

    if microphone_audio:
        transcription = transcribe_audio_file(get_whisper_model(), microphone_audio)
        return transcription, transcription

    return "", ""


def chat_with_byulie(
    text_input,
    microphone_audio,
    model_name,
    temperature,
    max_output_tokens,
    system_prompt,
    emotion,
    tone,
):
    """Run ASR, local LLM response generation, and local GPT-SoVITS synthesis."""
    user_text, transcript = get_user_text(text_input, microphone_audio)
    if not user_text:
        return (
            transcript,
            f"Please type a message or record microphone audio for {CHARACTER_NAME} first.",
            None,
            "No input sent.",
        )

    tone_instruction = build_tone_instruction(emotion, tone)
    effective_system_prompt = normalize_text(system_prompt) or DEFAULT_SYSTEM_PROMPT
    if tone_instruction:
        effective_system_prompt = f"{effective_system_prompt}\n\n{tone_instruction}"

    assistant_text = llm_response(
        user_text,
        model=model_name or DEFAULT_MODEL,
        temperature=float(temperature),
        max_output_tokens=int(max_output_tokens),
        system_prompt=effective_system_prompt,
    )

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    output_wav_path = AUDIO_DIR / f"byulie_{uuid.uuid4().hex}.wav"
    generated_audio = sovits_gen(assistant_text, output_wav_path)

    status = f"{CHARACTER_NAME} responded locally."
    if generated_audio is None:
        status = (
            f"{CHARACTER_NAME} replied in text, but GPT-SoVITS did not return audio. "
            "Is the local TTS server running?"
        )

    return transcript, assistant_text, generated_audio, status


def build_app():
    """Construct the Gradio Blocks interface without exposing it beyond localhost."""
    with gr.Blocks(title=f"{CHARACTER_NAME} Local Web UI") as demo:
        gr.Markdown(
            f"# {CHARACTER_NAME} Local Web UI\n"
            "Runs on your machine only. Type a message or record audio, then let local Ollama, "
            "Faster-Whisper, and GPT-SoVITS handle the response."
        )

        with gr.Row():
            with gr.Column(scale=2):
                text_input = gr.Textbox(
                    label="Text input",
                    placeholder=f"Type to {CHARACTER_NAME}, or leave blank and use the microphone input below.",
                    lines=4,
                )
                microphone_audio = gr.Audio(
                    label="Microphone input",
                    sources=["microphone", "upload"],
                    type="filepath",
                )
                send_button = gr.Button(f"Send to {CHARACTER_NAME}", variant="primary")

            with gr.Column(scale=1):
                model_selector = gr.Dropdown(
                    label="Model selector",
                    choices=MODEL_CHOICES,
                    value=DEFAULT_MODEL,
                    allow_custom_value=True,
                )
                temperature_slider = gr.Slider(
                    label="Temperature",
                    minimum=0.0,
                    maximum=2.0,
                    value=DEFAULT_TEMPERATURE,
                    step=0.05,
                )
                max_tokens_slider = gr.Slider(
                    label="Max output tokens",
                    minimum=64,
                    maximum=4096,
                    value=DEFAULT_MAX_OUTPUT_TOKENS,
                    step=64,
                )

        system_prompt = gr.Textbox(
            label="System prompt editor",
            value=DEFAULT_SYSTEM_PROMPT,
            lines=8,
        )

        with gr.Row():
            emotion = gr.Dropdown(
                label="TTS emotion",
                choices=["Neutral", "Cheerful", "Soft", "Dramatic", "Sleepy", "Annoyed"],
                value="Neutral",
            )
            tone = gr.Textbox(
                label="TTS tone note",
                placeholder="Example: playful, cozy, quick, whispery",
            )

        transcript_output = gr.Textbox(label="Transcribed microphone text", lines=2)
        assistant_output = gr.Textbox(label=f"{CHARACTER_NAME}'s text response", lines=8)
        generated_voice = gr.Audio(label=f"{CHARACTER_NAME}'s voice playback", type="filepath", autoplay=False)
        status_output = gr.Markdown()

        send_button.click(
            fn=chat_with_byulie,
            inputs=[
                text_input,
                microphone_audio,
                model_selector,
                temperature_slider,
                max_tokens_slider,
                system_prompt,
                emotion,
                tone,
            ],
            outputs=[transcript_output, assistant_output, generated_voice, status_output],
        )

    return demo


if __name__ == "__main__":
    build_app().launch(server_name="127.0.0.1", share=False, show_error=True)
