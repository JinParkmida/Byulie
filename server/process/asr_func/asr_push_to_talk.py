import os

def transcribe_audio_file(model, audio_file):
    """Transcribe an existing audio file with Faster-Whisper."""
    segments, _ = model.transcribe(str(audio_file))
    transcription = " ".join(segment.text for segment in segments)
    return transcription.strip()


def record_and_transcribe(model, output_file="recording.wav", samplerate=44100):
    """
    Simple push-to-talk recorder: record -> save -> transcribe -> return text
    """

    import sounddevice as sd
    import soundfile as sf

    # Remove existing file
    if os.path.exists(output_file):
        os.remove(output_file)

    print("Press ENTER to start talking to Byulie...")
    input()

    print("Recording... Press ENTER to stop")

    # Record audio directly
    recording = sd.rec(int(60 * samplerate), samplerate=samplerate, channels=1, dtype="float64")
    input()  # Wait for stop
    sd.stop()

    print("⏹️  Saving audio...")

    # Write the file
    sf.write(output_file, recording, samplerate)

    print("🎯 Transcribing...")

    transcription = transcribe_audio_file(model, output_file)

    print(f"Transcription: {transcription}")
    return transcription


# Example usage
if __name__ == "__main__":
    from faster_whisper import WhisperModel

    model = WhisperModel("base.en", device="cpu", compute_type="float32")
    result = record_and_transcribe(model)
    print(f"Got: '{result}'")
