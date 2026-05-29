import { useCallback, useEffect, useRef, useState } from "react";

export type MicMode = "hold" | "live";

type LiveState = "off" | "listening" | "speaking" | "processing";

interface UseMicrophoneOptions {
  onAudioReady: (blob: Blob) => Promise<void>;
  disabled?: boolean;
}

/** Browser mic capture with hold-to-talk and live VAD (local-only, no external APIs). */
export function useMicrophone({ onAudioReady, disabled }: UseMicrophoneOptions) {
  const [micMode, setMicMode] = useState<MicMode>("hold");
  const [liveState, setLiveState] = useState<LiveState>("off");
  const [holding, setHolding] = useState(false);

  const streamRef = useRef<MediaStream | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const rafRef = useRef<number | null>(null);
  const liveActiveRef = useRef(false);
  const speechDetectedRef = useRef(false);
  const silenceStartRef = useRef<number | null>(null);

  const SILENCE_THRESHOLD = 0.018;
  const SILENCE_MS = 1400;
  const MIN_SPEECH_MS = 350;

  const stopStream = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
  }, []);

  const stopAnalyser = useCallback(() => {
    if (rafRef.current !== null) {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    }
    analyserRef.current = null;
    void audioContextRef.current?.close();
    audioContextRef.current = null;
  }, []);

  const finalizeRecording = useCallback(async () => {
    const recorder = recorderRef.current;
    if (!recorder || recorder.state === "inactive") return;

    await new Promise<void>((resolve) => {
      recorder.onstop = () => resolve();
      recorder.stop();
    });

    stopAnalyser();
    stopStream();

    const blob = new Blob(chunksRef.current, { type: "audio/webm" });
    chunksRef.current = [];
    recorderRef.current = null;

    if (blob.size > 0) {
      setLiveState("processing");
      await onAudioReady(blob);
    }
    setLiveState(liveActiveRef.current ? "listening" : "off");
    speechDetectedRef.current = false;
    silenceStartRef.current = null;
  }, [onAudioReady, stopAnalyser, stopStream]);

  const startRecorder = useCallback(async () => {
    if (disabled) return;

    const stream = await navigator.mediaDevices.getUserMedia({
      audio: { echoCancellation: true, noiseSuppression: true },
    });
    streamRef.current = stream;
    chunksRef.current = [];

    const recorder = new MediaRecorder(stream);
    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunksRef.current.push(e.data);
    };
    recorder.start(250);
    recorderRef.current = recorder;

    const audioContext = new AudioContext();
    audioContextRef.current = audioContext;
    const source = audioContext.createMediaStreamSource(stream);
    const analyser = audioContext.createAnalyser();
    analyser.fftSize = 512;
    source.connect(analyser);
    analyserRef.current = analyser;

    return analyser;
  }, [disabled]);

  const monitorVad = useCallback(
    (analyser: AnalyserNode, speechStartedAt: { current: number | null }) => {
      const data = new Uint8Array(analyser.frequencyBinCount);

      const tick = () => {
        if (!liveActiveRef.current || !recorderRef.current) return;

        analyser.getByteTimeDomainData(data);
        let sum = 0;
        for (let i = 0; i < data.length; i++) {
          const v = (data[i] - 128) / 128;
          sum += v * v;
        }
        const rms = Math.sqrt(sum / data.length);
        const now = performance.now();

        if (rms > SILENCE_THRESHOLD) {
          if (!speechDetectedRef.current) {
            speechDetectedRef.current = true;
            speechStartedAt.current = now;
            setLiveState("speaking");
          }
          silenceStartRef.current = null;
        } else if (speechDetectedRef.current) {
          if (silenceStartRef.current === null) {
            silenceStartRef.current = now;
          } else if (
            now - silenceStartRef.current >= SILENCE_MS &&
            speechStartedAt.current !== null &&
            now - speechStartedAt.current >= MIN_SPEECH_MS
          ) {
            void finalizeRecording();
            return;
          }
        }

        rafRef.current = requestAnimationFrame(tick);
      };

      rafRef.current = requestAnimationFrame(tick);
    },
    [finalizeRecording]
  );

  const startLiveListen = useCallback(async () => {
    if (disabled || liveActiveRef.current) return;
    setLiveState("listening");
    liveActiveRef.current = true;
    speechDetectedRef.current = false;
    silenceStartRef.current = null;

    try {
      const analyser = await startRecorder();
      if (!analyser) return;
      const speechStartedAt = { current: null as number | null };
      monitorVad(analyser, speechStartedAt);
    } catch {
      liveActiveRef.current = false;
      setLiveState("off");
      stopStream();
      throw new Error("Microphone access denied or unavailable.");
    }
  }, [disabled, monitorVad, startRecorder, stopStream]);

  const stopLiveListen = useCallback(() => {
    liveActiveRef.current = false;
    setLiveState("off");
    if (recorderRef.current?.state === "recording") {
      void finalizeRecording();
    } else {
      stopAnalyser();
      stopStream();
    }
  }, [finalizeRecording, stopAnalyser, stopStream]);

  const startHold = useCallback(async () => {
    if (disabled || holding) return;
    setHolding(true);
    setLiveState("speaking");
    try {
      await startRecorder();
    } catch {
      setHolding(false);
      setLiveState("off");
      throw new Error("Microphone access denied or unavailable.");
    }
  }, [disabled, holding, startRecorder]);

  const stopHold = useCallback(() => {
    if (!holding) return;
    setHolding(false);
    void finalizeRecording();
  }, [finalizeRecording, holding]);

  useEffect(() => {
    return () => {
      liveActiveRef.current = false;
      if (recorderRef.current?.state === "recording") {
        recorderRef.current.stop();
      }
      stopAnalyser();
      stopStream();
    };
  }, [stopAnalyser, stopStream]);

  useEffect(() => {
    if (micMode !== "live" && liveActiveRef.current) {
      stopLiveListen();
    }
  }, [micMode, stopLiveListen]);

  return {
    micMode,
    setMicMode,
    liveState,
    holding,
    startHold,
    stopHold,
    startLiveListen,
    stopLiveListen,
    isLiveActive: liveState === "listening" || liveState === "speaking",
  };
}
