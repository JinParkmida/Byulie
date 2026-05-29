"""Local live microphone capture with simple voice-activity (silence) detection."""

import time

import numpy as np
import sounddevice as sd
import soundfile as sf


def record_utterance_until_silence(
    output_file,
    *,
    samplerate=16000,
    silence_threshold=0.012,
    silence_seconds=1.2,
    max_seconds=45.0,
    block_seconds=0.05,
):
    """
    Record from the default microphone until the user pauses (local VAD).
    Returns path to the saved WAV file.
    """
    block_size = int(samplerate * block_seconds)
    recorded = []
    speech_started = False
    silent_time = 0.0
    started = time.time()

    print("Listening… speak now. (pauses automatically when you stop talking)")

    with sd.InputStream(samplerate=samplerate, channels=1, dtype="float32", blocksize=block_size) as stream:
        while True:
            chunk, _ = stream.read(block_size)
            recorded.append(chunk.copy())
            rms = float(np.sqrt(np.mean(chunk**2)))

            if rms >= silence_threshold:
                speech_started = True
                silent_time = 0.0
            elif speech_started:
                silent_time += block_seconds
                if silent_time >= silence_seconds:
                    break

            if time.time() - started >= max_seconds:
                break

    if not speech_started:
        print("No speech detected.")
        return None

    audio = np.concatenate(recorded, axis=0)
    sf.write(output_file, audio, samplerate)
    return output_file
