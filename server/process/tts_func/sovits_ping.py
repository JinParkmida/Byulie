import time
from pathlib import Path

import requests
import yaml

from server.paths import CONFIG_PATH, REPO_ROOT

with CONFIG_PATH.open("r", encoding="utf-8") as f:
    char_config = yaml.safe_load(f)

tts_config = char_config.get("tts", {})


def _resolve_ref_audio_path():
    ref_audio_path = tts_config.get("ref_audio_path")
    if not ref_audio_path:
        return ref_audio_path
    ref_path = Path(ref_audio_path)
    if ref_path.is_absolute():
        return str(ref_path)
    return str(REPO_ROOT / ref_path)


def play_audio(path):
    import sounddevice as sd
    import soundfile as sf

    data, samplerate = sf.read(path)
    sd.play(data, samplerate)
    sd.wait()  # Wait until playback is finished


def sovits_gen(in_text, output_wav_pth="output.wav"):
    url = tts_config.get("endpoint", "http://127.0.0.1:9880/tts")

    payload = {
        "text": in_text,
        "text_lang": tts_config.get("text_lang", "en"),
        "ref_audio_path": _resolve_ref_audio_path(),
        "prompt_text": tts_config.get("prompt_text", ""),
        "prompt_lang": tts_config.get("prompt_lang", "en"),
    }

    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
    except requests.RequestException as exc:
        print(
            "Error in sovits_gen: could not reach the local "
            f"GPT-SoVITS server at {url}.",
            exc,
        )
        return None

    # Save the response audio if it is binary.
    with open(output_wav_pth, "wb") as f:
        f.write(response.content)

    return output_wav_pth


if __name__ == "__main__":
    start_time = time.time()
    output_wav_pth1 = "output.wav"
    path_to_aud = sovits_gen(
        "Hi senpai, this is Byulie. If you hear this, local TTS is set up correctly.",
        output_wav_pth1,
    )

    end_time = time.time()
    elapsed_time = end_time - start_time

    print(f"Elapsed time: {elapsed_time:.4f} seconds")
    print(path_to_aud)
