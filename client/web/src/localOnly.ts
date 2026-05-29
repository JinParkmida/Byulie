const LOCAL_HOSTS = new Set(["127.0.0.1", "localhost", "::1"]);

export function assertLocalUrl(url: string, label: string): void {
  let parsed: URL;
  try {
    parsed = new URL(url.trim());
  } catch {
    throw new Error(`${label} is not a valid URL.`);
  }

  if (!["http:", "https:"].includes(parsed.protocol)) {
    throw new Error(`${label} must use http:// or https://`);
  }

  const host = parsed.hostname.toLowerCase();
  if (!LOCAL_HOSTS.has(host)) {
    throw new Error(
      `${label} must point to localhost (127.0.0.1). Remote hosts are disabled.`
    );
  }
}

export function validateConfigUrls(config: {
  llm?: { base_url?: string; provider?: string };
  tts?: { endpoint?: string };
}): void {
  const provider = (config.llm?.provider || "ollama").toLowerCase();
  if (provider !== "ollama") {
    throw new Error("Only the local Ollama provider is allowed.");
  }
  if (config.llm?.base_url) {
    assertLocalUrl(config.llm.base_url, "Ollama base URL");
  }
  if (config.tts?.endpoint) {
    assertLocalUrl(config.tts.endpoint, "GPT-SoVITS endpoint");
  }
}
