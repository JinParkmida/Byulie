from pathlib import Path
import sys
import uuid

from faster_whisper import WhisperModel
import soundfile as sf
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from server.paths import AUDIO_DIR, CONFIG_PATH
from server.process.asr_func.asr_push_to_talk import record_and_transcribe
from server.process.llm_funcs.llm_scr import llm_response
from server.process.tts_func.sovits_ping import sovits_gen, play_audio

with CONFIG_PATH.open("r", encoding="utf-8") as f:
    char_config = yaml.safe_load(f)

asr_config = char_config.get("asr", {})


def get_wav_duration(path):
    with sf.SoundFile(path) as f:
        return len(f) / f.samplerate


print("\n========== Starting Byulie voice chat ==========\n")
whisper_model = WhisperModel(
    asr_config.get("model", "base.en"),
    device=asr_config.get("device", "cpu"),
    compute_type=asr_config.get("compute_type", "float32"),
)

while True:
    conversation_recording = AUDIO_DIR / "conversation.wav"
    conversation_recording.parent.mkdir(parents=True, exist_ok=True)

    user_spoken_text = record_and_transcribe(whisper_model, conversation_recording)

    llm_output = llm_response(user_spoken_text)

    uid = uuid.uuid4().hex
    output_wav_path = AUDIO_DIR / f"byulie_{uid}.wav"
    output_wav_path.parent.mkdir(parents=True, exist_ok=True)

    gen_aud_path = sovits_gen(llm_output, output_wav_path)

    if gen_aud_path:
        play_audio(output_wav_path)

    for fp in AUDIO_DIR.glob("*.wav"):
        if fp.is_file():
            fp.unlink()
