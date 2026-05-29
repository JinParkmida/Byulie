import { useCallback, useEffect, useState } from "react";
import { configToRuntime, fetchConfig, fetchHealth, fetchMeta } from "./api";
import { ChatPanel } from "./components/ChatPanel";
import { DevPanel } from "./components/DevPanel";
import { StatusBar } from "./components/StatusBar";
import type { ByulieConfig, HealthResponse, RuntimeSettings } from "./types";

type Tab = "chat" | "studio";

export default function App() {
  const [tab, setTab] = useState<Tab>("chat");
  const [config, setConfig] = useState<ByulieConfig | null>(null);
  const [settings, setSettings] = useState<RuntimeSettings | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [models, setModels] = useState<string[]>([]);
  const [emotions, setEmotions] = useState<string[]>([]);
  const [characterName, setCharacterName] = useState("Byulie");
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const refreshHealth = useCallback(async () => {
    try {
      const h = await fetchHealth();
      setHealth(h);
      setCharacterName(h.character);
    } catch {
      setHealth(null);
    }
  }, []);

  const bootstrap = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const [cfg, meta, h] = await Promise.all([fetchConfig(), fetchMeta(), fetchHealth()]);
      setConfig(cfg);
      setModels(meta.models);
      setEmotions(meta.emotions);
      setCharacterName(meta.character_name);
      setSettings(configToRuntime(cfg, meta.models));
      setHealth(h);
    } catch (err) {
      setLoadError(
        err instanceof Error
          ? err.message
          : "Could not reach the Byulie API. Start it with: uvicorn server.api.main:app --reload"
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void bootstrap();
    const interval = setInterval(() => void refreshHealth(), 15000);
    return () => clearInterval(interval);
  }, [bootstrap, refreshHealth]);

  if (loading) {
    return (
      <div className="empty-state" style={{ height: "100vh" }}>
        <p>Loading Byulie…</p>
      </div>
    );
  }

  if (loadError || !config || !settings) {
    return (
      <div className="empty-state" style={{ height: "100vh", maxWidth: 520, margin: "0 auto" }}>
        <p className="toast err" style={{ display: "block" }}>
          {loadError ?? "Failed to load"}
        </p>
        <button type="button" className="btn btn-primary" onClick={() => void bootstrap()}>
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">B</div>
          <div>
            <h1>{characterName}</h1>
            <p>Local voice assistant</p>
          </div>
        </div>
        <nav className="nav">
          <button
            type="button"
            className={`nav-btn ${tab === "chat" ? "active" : ""}`}
            onClick={() => setTab("chat")}
          >
            💬 Chat
          </button>
          <button
            type="button"
            className={`nav-btn ${tab === "studio" ? "active" : ""}`}
            onClick={() => setTab("studio")}
          >
            ⚙ Studio
          </button>
        </nav>
        <div className="sidebar-footer">
          Vite hot-reloads UI changes instantly.
          <br />
          Save in Studio to persist YAML.
        </div>
      </aside>

      <div className="main">
        <div className="panel">
          {tab === "chat" ? (
            <ChatPanel characterName={characterName} settings={settings} />
          ) : (
            <DevPanel
              config={config}
              settings={settings}
              models={models}
              emotions={emotions}
              onSettingsChange={setSettings}
              onConfigSaved={setConfig}
            />
          )}
        </div>
        <StatusBar health={health} busy={false} />
      </div>
    </div>
  );
}
