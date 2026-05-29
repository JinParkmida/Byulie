import { useState } from "react";
import { reloadConfig, saveConfig } from "../api";
import { validateConfigUrls } from "../localOnly";
import type { ByulieConfig, RuntimeSettings } from "../types";

interface Props {
  config: ByulieConfig;
  settings: RuntimeSettings;
  models: string[];
  emotions: string[];
  onSettingsChange: (settings: RuntimeSettings) => void;
  onConfigSaved: (config: ByulieConfig) => void;
}

export function DevPanel({
  config,
  settings,
  models,
  emotions,
  onSettingsChange,
  onConfigSaved,
}: Props) {
  const [toast, setToast] = useState<{ type: "ok" | "err"; text: string } | null>(null);
  const [saving, setSaving] = useState(false);

  const updateSettings = (patch: Partial<RuntimeSettings>) => {
    onSettingsChange({ ...settings, ...patch });
  };

  const updateLlm = (patch: Partial<NonNullable<ByulieConfig["llm"]>>) => {
    onConfigSaved({
      ...config,
      llm: { ...config.llm, ...patch },
    });
  };

  const updateAsr = (patch: Partial<NonNullable<ByulieConfig["asr"]>>) => {
    onConfigSaved({
      ...config,
      asr: { ...config.asr, ...patch },
    });
  };

  const updateTts = (patch: Partial<NonNullable<ByulieConfig["tts"]>>) => {
    onConfigSaved({
      ...config,
      tts: { ...config.tts, ...patch },
    });
  };

  const handleSave = async () => {
    setSaving(true);
    setToast(null);
    try {
      const patch = {
        character: config.character,
        history_file: config.history_file,
        asr: config.asr,
        tts: config.tts,
        llm: {
          ...config.llm,
          provider: "ollama",
          model: settings.model,
          temperature: settings.temperature,
          max_output_tokens: settings.maxOutputTokens,
        },
        presets: {
          default: { system_prompt: settings.systemPrompt },
        },
      };
      validateConfigUrls(patch);
      const result = await saveConfig(patch);
      onConfigSaved(result.config);
      setToast({ type: "ok", text: "Saved to character_config.yaml and reloaded backend." });
    } catch (err) {
      setToast({
        type: "err",
        text: err instanceof Error ? err.message : "Failed to save configuration",
      });
    } finally {
      setSaving(false);
    }
  };

  const handleReload = async () => {
    setToast(null);
    try {
      const result = await reloadConfig();
      onConfigSaved(result.config);
      setToast({ type: "ok", text: "Reloaded configuration from disk." });
    } catch (err) {
      setToast({
        type: "err",
        text: err instanceof Error ? err.message : "Failed to reload",
      });
    }
  };

  return (
    <div>
      <p className="hint">
        Tune Byulie live. Changes in this panel affect the next chat message immediately. Click{" "}
        <strong>Save to disk</strong> to persist <code>character_config.yaml</code>.
      </p>

      {toast && <div className={`toast ${toast.type}`}>{toast.text}</div>}

      <div className="dev-grid">
        <section className="card">
          <div className="card-header">
            <h2>Character & prompt</h2>
          </div>
          <div className="card-body">
            <div className="field">
              <label>Name</label>
              <input
                value={config.character?.name ?? "Byulie"}
                onChange={(e) =>
                  onConfigSaved({
                    ...config,
                    character: { ...config.character, name: e.target.value },
                  })
                }
              />
            </div>
            <div className="field">
              <label>System prompt</label>
              <textarea
                value={settings.systemPrompt}
                onChange={(e) => updateSettings({ systemPrompt: e.target.value })}
              />
            </div>
            <div className="grid-2">
              <div className="field">
                <label>Emotion (TTS hint)</label>
                <select
                  value={settings.emotion}
                  onChange={(e) => updateSettings({ emotion: e.target.value })}
                >
                  {emotions.map((e) => (
                    <option key={e} value={e}>
                      {e}
                    </option>
                  ))}
                </select>
              </div>
              <div className="field">
                <label>Tone note</label>
                <input
                  value={settings.tone}
                  onChange={(e) => updateSettings({ tone: e.target.value })}
                  placeholder="playful, cozy, whispery…"
                />
              </div>
            </div>
          </div>
        </section>

        <section className="card">
          <div className="card-header">
            <h2>Language model</h2>
          </div>
          <div className="card-body">
            <div className="field">
              <label>Model</label>
              <select value={settings.model} onChange={(e) => updateSettings({ model: e.target.value })}>
                {models.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>Ollama base URL</label>
              <input
                value={config.llm?.base_url ?? ""}
                onChange={(e) => updateLlm({ base_url: e.target.value })}
              />
            </div>
            <div className="grid-2">
              <div className="field">
                <label>Temperature — {settings.temperature.toFixed(2)}</label>
                <input
                  type="range"
                  min={0}
                  max={2}
                  step={0.05}
                  value={settings.temperature}
                  onChange={(e) => updateSettings({ temperature: Number(e.target.value) })}
                />
              </div>
              <div className="field">
                <label>Max output tokens — {settings.maxOutputTokens}</label>
                <input
                  type="range"
                  min={64}
                  max={4096}
                  step={64}
                  value={settings.maxOutputTokens}
                  onChange={(e) => updateSettings({ maxOutputTokens: Number(e.target.value) })}
                />
              </div>
            </div>
          </div>
        </section>

        <section className="card">
          <div className="card-header">
            <h2>Speech recognition</h2>
          </div>
          <div className="card-body">
            <div className="grid-2">
              <div className="field">
                <label>Whisper model</label>
                <input
                  value={config.asr?.model ?? "base.en"}
                  onChange={(e) => updateAsr({ model: e.target.value })}
                />
              </div>
              <div className="field">
                <label>Device</label>
                <select
                  value={config.asr?.device ?? "cpu"}
                  onChange={(e) => updateAsr({ device: e.target.value })}
                >
                  <option value="cpu">cpu</option>
                  <option value="cuda">cuda</option>
                </select>
              </div>
            </div>
            <div className="field">
              <label>Compute type</label>
              <input
                value={config.asr?.compute_type ?? "float32"}
                onChange={(e) => updateAsr({ compute_type: e.target.value })}
              />
            </div>
          </div>
        </section>

        <section className="card">
          <div className="card-header">
            <h2>Voice synthesis</h2>
          </div>
          <div className="card-body">
            <div className="field">
              <label>GPT-SoVITS endpoint</label>
              <input
                value={config.tts?.endpoint ?? ""}
                onChange={(e) => updateTts({ endpoint: e.target.value })}
              />
            </div>
            <div className="field">
              <label>Reference audio path</label>
              <input
                value={config.tts?.ref_audio_path ?? ""}
                onChange={(e) => updateTts({ ref_audio_path: e.target.value })}
              />
            </div>
            <div className="field">
              <label>Reference prompt text</label>
              <textarea
                value={config.tts?.prompt_text ?? ""}
                onChange={(e) => updateTts({ prompt_text: e.target.value })}
                rows={3}
              />
            </div>
            <div className="grid-2">
              <div className="field">
                <label>Text language</label>
                <input
                  value={config.tts?.text_lang ?? "en"}
                  onChange={(e) => updateTts({ text_lang: e.target.value })}
                />
              </div>
              <div className="field">
                <label>Prompt language</label>
                <input
                  value={config.tts?.prompt_lang ?? "en"}
                  onChange={(e) => updateTts({ prompt_lang: e.target.value })}
                />
              </div>
            </div>
          </div>
        </section>
      </div>

      <div className="dev-actions">
        <button type="button" className="btn btn-primary" onClick={() => void handleSave()} disabled={saving}>
          {saving ? "Saving…" : "Save to disk"}
        </button>
        <button type="button" className="btn btn-ghost" onClick={() => void handleReload()}>
          Reload from disk
        </button>
      </div>
    </div>
  );
}
