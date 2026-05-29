import type { HealthResponse } from "../types";

interface Props {
  health: HealthResponse | null;
  busy: boolean;
}

export function StatusBar({ health, busy }: Props) {
  return (
    <footer className="status-bar">
      <span className="status-pill">
        <span className={`status-dot ${health?.ollama.ok ? "ok" : ""}`} />
        Ollama
      </span>
      <span className="status-pill">
        <span className={`status-dot ${health?.tts.ok ? "ok" : ""}`} />
        GPT-SoVITS
      </span>
      <span className="status-pill">
        <span className={`status-dot ok`} />
        API
      </span>
      {busy && <span style={{ color: "var(--accent)" }}>Processing…</span>}
    </footer>
  );
}
