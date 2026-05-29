"""Byulie local Ollama-backed LLM functions with JSON chat history."""

import json
import os
from copy import deepcopy
from pathlib import Path
from urllib.parse import urljoin

import requests
import yaml

from server.local_only import assert_local_url, assert_ollama_provider, validate_config_urls
from server.paths import CONFIG_PATH, REPO_ROOT

with CONFIG_PATH.open("r", encoding="utf-8") as f:
    char_config = yaml.safe_load(f)

validate_config_urls(char_config)

# Constants
_history_file = char_config["history_file"]
HISTORY_FILE = (
    str(REPO_ROOT / _history_file)
    if not Path(_history_file).is_absolute()
    else _history_file
)
LLM_CONFIG = char_config.get("llm", {})
PROVIDER = LLM_CONFIG.get("provider", "ollama")
MODEL = LLM_CONFIG.get("model", "qwen3:4b")
OLLAMA_BASE_URL = LLM_CONFIG.get("base_url", "http://127.0.0.1:11434").rstrip("/")
TEMPERATURE = LLM_CONFIG.get("temperature", 0.8)
MAX_OUTPUT_TOKENS = LLM_CONFIG.get("max_output_tokens", 512)
CONTEXT_TOKENS = LLM_CONFIG.get("context_tokens", 8192)
TIMEOUT_SECONDS = LLM_CONFIG.get("timeout_seconds", 120)
DEFAULT_SYSTEM_PROMPT = char_config["presets"]["default"]["system_prompt"]
SYSTEM_MESSAGE = {"role": "system", "content": DEFAULT_SYSTEM_PROMPT}


def reload_from_config():
    """Reload module-level settings after character_config.yaml changes."""
    global char_config, HISTORY_FILE, LLM_CONFIG, PROVIDER, MODEL
    global OLLAMA_BASE_URL, TEMPERATURE, MAX_OUTPUT_TOKENS, CONTEXT_TOKENS
    global TIMEOUT_SECONDS, DEFAULT_SYSTEM_PROMPT, SYSTEM_MESSAGE

    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        char_config = yaml.safe_load(f)

    validate_config_urls(char_config)

    _history_file = char_config["history_file"]
    HISTORY_FILE = (
        str(REPO_ROOT / _history_file)
        if not Path(_history_file).is_absolute()
        else _history_file
    )
    LLM_CONFIG = char_config.get("llm", {})
    PROVIDER = LLM_CONFIG.get("provider", "ollama")
    MODEL = LLM_CONFIG.get("model", "qwen3:4b")
    OLLAMA_BASE_URL = LLM_CONFIG.get("base_url", "http://127.0.0.1:11434").rstrip("/")
    TEMPERATURE = LLM_CONFIG.get("temperature", 0.8)
    MAX_OUTPUT_TOKENS = LLM_CONFIG.get("max_output_tokens", 512)
    CONTEXT_TOKENS = LLM_CONFIG.get("context_tokens", 8192)
    TIMEOUT_SECONDS = LLM_CONFIG.get("timeout_seconds", 120)
    DEFAULT_SYSTEM_PROMPT = char_config["presets"]["default"]["system_prompt"]
    SYSTEM_MESSAGE = {"role": "system", "content": DEFAULT_SYSTEM_PROMPT}


def build_system_message(system_prompt=None):
    """Return a chat system message, falling back to the configured default."""
    return {"role": "system", "content": system_prompt or DEFAULT_SYSTEM_PROMPT}


def _extract_text(content):
    """Convert legacy block-based history content into plain chat text."""
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text_parts = []
        for block in content:
            if isinstance(block, dict):
                text = block.get("text")
                if text:
                    text_parts.append(text)
        return "\n".join(text_parts)

    return ""


def normalize_history(history, system_prompt=None):
    """Return Ollama-compatible chat messages from current or legacy history."""
    normalized = []
    system_message = build_system_message(system_prompt)

    for message in history:
        if not isinstance(message, dict):
            continue

        role = message.get("role")
        if role not in {"system", "user", "assistant"}:
            continue

        content = _extract_text(message.get("content", "")).strip()
        if content:
            normalized.append({"role": role, "content": content})

    if not normalized or normalized[0].get("role") != "system":
        normalized.insert(0, deepcopy(system_message))
    elif system_prompt is not None:
        normalized[0] = deepcopy(system_message)

    return normalized


# Load/save chat history
def load_history(system_prompt=None):
    system_message = build_system_message(system_prompt)

    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return normalize_history(json.load(f), system_prompt=system_prompt)

    return [deepcopy(system_message)]


def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def get_byulie_response_no_tool(
    messages,
    model=None,
    temperature=None,
    max_output_tokens=None,
):
    """Call the local Ollama server and return Byulie's text response."""
    assert_ollama_provider(PROVIDER)

    selected_model = model or MODEL
    base_url = assert_local_url(OLLAMA_BASE_URL, "llm.base_url")
    endpoint = urljoin(f"{base_url}/", "api/chat")
    payload = {
        "model": selected_model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": TEMPERATURE if temperature is None else temperature,
            "num_predict": MAX_OUTPUT_TOKENS if max_output_tokens is None else max_output_tokens,
            "num_ctx": CONTEXT_TOKENS,
        },
    }

    try:
        response = requests.post(endpoint, json=payload, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(
            "Could not reach the local Ollama server. Start it with "
            f"`ollama serve`, pull the model with `ollama pull {selected_model}`, "
            f"and confirm {OLLAMA_BASE_URL} is reachable."
        ) from exc

    response_payload = response.json()
    assistant_message = response_payload.get("message", {})
    assistant_text = assistant_message.get("content", "").strip()

    if not assistant_text:
        raise RuntimeError("The local Ollama server returned an empty response.")

    return assistant_text


def llm_response(
    user_input,
    model=None,
    temperature=None,
    max_output_tokens=None,
    system_prompt=None,
):
    messages = load_history(system_prompt=system_prompt)

    # Append user message to memory
    messages.append({"role": "user", "content": user_input})

    byulie_response = get_byulie_response_no_tool(
        messages,
        model=model,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
    )

    messages.append({"role": "assistant", "content": byulie_response})
    save_history(messages)
    return byulie_response


if __name__ == "__main__":
    print("Byulie LLM module")
