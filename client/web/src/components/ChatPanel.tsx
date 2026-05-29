import { useCallback, useEffect, useRef, useState } from "react";
import { sendAudio, sendChat } from "../api";
import { useMicrophone } from "../hooks/useMicrophone";
import type { ChatMessage, RuntimeSettings } from "../types";

interface Props {
  characterName: string;
  settings: RuntimeSettings;
}

export function ChatPanel({ characterName, settings }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const appendExchange = useCallback(
    (userText: string, result: { assistant_text: string; audio_url: string | null; transcript?: string }) => {
      const displayText = result.transcript?.trim() || userText;
      const userMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "user",
        text: displayText,
      };
      const assistantMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        text: result.assistant_text,
        audioUrl: result.audio_url,
      };
      setMessages((prev) => [...prev, userMsg, assistantMsg]);
    },
    []
  );

  const handleAudio = useCallback(
    async (blob: Blob) => {
      setError(null);
      setBusy(true);
      try {
        const result = await sendAudio(blob, settings);
        appendExchange(result.transcript || "[voice]", result);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Voice chat failed");
      } finally {
        setBusy(false);
      }
    },
    [appendExchange, settings]
  );

  const {
    micMode,
    setMicMode,
    liveState,
    holding,
    startHold,
    stopHold,
    startLiveListen,
    stopLiveListen,
    isLiveActive,
  } = useMicrophone({ onAudioReady: handleAudio, disabled: busy });

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy, liveState]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || busy) return;
    setInput("");
    setError(null);
    setBusy(true);
    try {
      const result = await sendChat(text, settings);
      appendExchange(text, result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Chat failed");
    } finally {
      setBusy(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void handleSend();
    }
  };

  const liveLabel =
    liveState === "listening"
      ? "Listening…"
      : liveState === "speaking"
        ? "Hearing you…"
        : liveState === "processing"
          ? "Processing…"
          : "";

  return (
    <div className="chat-layout">
      <section className="card" style={{ display: "flex", flexDirection: "column", minHeight: 0 }}>
        <div className="card-header">
          <h2>Chat with {characterName}</h2>
          <div className="mic-mode-toggle">
            <button
              type="button"
              className={micMode === "hold" ? "active" : ""}
              onClick={() => setMicMode("hold")}
              disabled={busy || isLiveActive}
            >
              Hold to talk
            </button>
            <button
              type="button"
              className={micMode === "live" ? "active" : ""}
              onClick={() => setMicMode("live")}
              disabled={busy}
            >
              Live listen
            </button>
          </div>
        </div>

        {(isLiveActive || liveLabel) && (
          <div className={`live-banner ${liveState}`}>
            <span className="live-pulse" />
            {liveLabel || "Live mic on"}
          </div>
        )}

        <div className="messages" style={{ flex: 1, padding: "0 1.25rem" }}>
          {messages.length === 0 && (
            <div className="empty-state">
              <p>
                {micMode === "live"
                  ? `Turn on live listen and talk to ${characterName}. She replies when you pause.`
                  : `Hold the mic button to talk, or type below.`}
              </p>
            </div>
          )}
          {messages.map((msg) => (
            <div key={msg.id} className={`message ${msg.role}`}>
              <div className="message-meta">{msg.role === "user" ? "You" : characterName}</div>
              <div style={{ whiteSpace: "pre-wrap" }}>{msg.text}</div>
              {msg.audioUrl && <audio controls src={msg.audioUrl} />}
            </div>
          ))}
          <div ref={bottomRef} />
        </div>
      </section>

      {error && <div className="toast err">{error}</div>}

      <div className="composer">
        <textarea
          placeholder={`Message ${characterName}…`}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={busy}
          rows={2}
        />
        <div className="composer-actions">
          {micMode === "live" ? (
            <button
              type="button"
              className={`btn btn-ghost record-btn ${isLiveActive ? "recording" : ""}`}
              onClick={() => (isLiveActive ? stopLiveListen() : void startLiveListen().catch((e) => setError(String(e))))}
              disabled={busy && !isLiveActive}
            >
              {isLiveActive ? "■ Stop live" : "● Live mic"}
            </button>
          ) : (
            <button
              type="button"
              className={`btn btn-ghost record-btn ${holding ? "recording" : ""}`}
              disabled={busy && !holding}
              onMouseDown={() => void startHold().catch((e) => setError(String(e)))}
              onMouseUp={stopHold}
              onMouseLeave={holding ? stopHold : undefined}
              onTouchStart={(e) => {
                e.preventDefault();
                void startHold().catch((err) => setError(String(err)));
              }}
              onTouchEnd={(e) => {
                e.preventDefault();
                stopHold();
              }}
            >
              {holding ? "Release to send" : "Hold mic"}
            </button>
          )}
          <button type="button" className="btn btn-primary" onClick={() => void handleSend()} disabled={busy || !input.trim()}>
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
