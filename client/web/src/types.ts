export interface ByulieConfig {
  character?: { name?: string };
  history_file?: string;
  llm?: {
    provider?: string;
    base_url?: string;
    model?: string;
    temperature?: number;
    max_output_tokens?: number;
    context_tokens?: number;
    timeout_seconds?: number;
  };
  asr?: {
    model?: string;
    device?: string;
    compute_type?: string;
  };
  presets?: {
    default?: {
      system_prompt?: string;
    };
  };
  tts?: {
    provider?: string;
    endpoint?: string;
    text_lang?: string;
    prompt_lang?: string;
    ref_audio_path?: string;
    prompt_text?: string;
  };
}

export interface HealthResponse {
  status: string;
  character: string;
  ollama: { ok: boolean; url: string; models?: string[]; error?: string };
  tts: { ok: boolean; endpoint: string; error?: string };
}

export interface MetaResponse {
  character_name: string;
  emotions: string[];
  models: string[];
  repo_root: string;
}

export interface ChatResult {
  assistant_text: string;
  audio_url: string | null;
  tts_ok: boolean;
  transcript?: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  text: string;
  audioUrl?: string | null;
  transcript?: string;
}

export interface RuntimeSettings {
  model: string;
  temperature: number;
  maxOutputTokens: number;
  systemPrompt: string;
  emotion: string;
  tone: string;
}
