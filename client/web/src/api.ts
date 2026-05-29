import type { ByulieConfig, ChatResult, HealthResponse, MetaResponse, RuntimeSettings } from "./types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init);
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export function fetchHealth() {
  return request<HealthResponse>("/api/health");
}

export function fetchMeta() {
  return request<MetaResponse>("/api/meta");
}

export function fetchConfig() {
  return request<ByulieConfig>("/api/config");
}

export function saveConfig(config: Partial<ByulieConfig>) {
  return request<{ config: ByulieConfig; reloaded: boolean }>("/api/config", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config),
  });
}

export function reloadConfig() {
  return request<{ config: ByulieConfig; reloaded: boolean }>("/api/config/reload", {
    method: "POST",
  });
}

export function sendChat(message: string, settings: RuntimeSettings) {
  return request<ChatResult>("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      model: settings.model,
      temperature: settings.temperature,
      max_output_tokens: settings.maxOutputTokens,
      system_prompt: settings.systemPrompt,
      emotion: settings.emotion,
      tone: settings.tone || null,
    }),
  });
}

export async function sendAudio(blob: Blob, settings: RuntimeSettings) {
  const form = new FormData();
  form.append("file", blob, "recording.webm");
  form.append("model", settings.model);
  form.append("temperature", String(settings.temperature));
  form.append("max_output_tokens", String(settings.maxOutputTokens));
  form.append("system_prompt", settings.systemPrompt);
  form.append("emotion", settings.emotion);
  if (settings.tone) form.append("tone", settings.tone);

  const response = await fetch("/api/chat/audio", { method: "POST", body: form });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Audio request failed (${response.status})`);
  }
  return response.json() as Promise<ChatResult>;
}

export function configToRuntime(config: ByulieConfig, models: string[]): RuntimeSettings {
  const llm = config.llm ?? {};
  return {
    model: llm.model ?? models[0] ?? "qwen3:4b",
    temperature: llm.temperature ?? 0.8,
    maxOutputTokens: llm.max_output_tokens ?? 512,
    systemPrompt: config.presets?.default?.system_prompt ?? "",
    emotion: "Neutral",
    tone: "",
  };
}

export function runtimeToConfigPatch(settings: RuntimeSettings, config: ByulieConfig): Partial<ByulieConfig> {
  return {
    llm: {
      ...config.llm,
      model: settings.model,
      temperature: settings.temperature,
      max_output_tokens: settings.maxOutputTokens,
    },
    presets: {
      default: {
        system_prompt: settings.systemPrompt,
      },
    },
  };
}
