"""Guards to keep Byulie on localhost — no paid or remote inference APIs."""

from urllib.parse import urlparse

LOCAL_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})


def assert_local_url(url: str, label: str = "URL") -> str:
    """Reject any endpoint that is not loopback."""
    if not url or not str(url).strip():
        raise ValueError(f"{label} cannot be empty.")

    parsed = urlparse(str(url).strip())
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"{label} must use http:// or https://")

    host = (parsed.hostname or "").lower()
    if host not in LOCAL_HOSTS:
        raise ValueError(
            f"{label} must use a local address (127.0.0.1 or localhost). "
            f"Remote hosts such as '{host}' are not allowed."
        )

    return str(url).strip().rstrip("/")


def assert_ollama_provider(provider: str | None) -> None:
    if (provider or "ollama").lower() != "ollama":
        raise ValueError("Only the local Ollama provider is allowed. Paid or cloud LLM APIs are disabled.")


def validate_config_urls(config: dict) -> None:
    """Validate all network endpoints in character_config.yaml."""
    assert_ollama_provider(config.get("llm", {}).get("provider"))

    llm_url = config.get("llm", {}).get("base_url")
    if llm_url:
        assert_local_url(llm_url, "llm.base_url")

    tts_url = config.get("tts", {}).get("endpoint")
    if tts_url:
        assert_local_url(tts_url, "tts.endpoint")
