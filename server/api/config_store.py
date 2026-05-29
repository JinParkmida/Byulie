"""Load and persist Byulie configuration for the web API."""

from copy import deepcopy
from pathlib import Path

import yaml

from server.local_only import validate_config_urls
from server.paths import CONFIG_PATH, REPO_ROOT


def _resolve_history_path(history_file: str) -> str:
    if Path(history_file).is_absolute():
        return history_file
    return str(REPO_ROOT / history_file)


def load_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save_config(config: dict) -> dict:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CONFIG_PATH.open("w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    return config


def deep_merge(base: dict, patch: dict) -> dict:
    merged = deepcopy(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def update_config(patch: dict) -> dict:
    current = load_config()
    merged = deep_merge(current, patch)
    validate_config_urls(merged)
    save_config(merged)
    return merged


def get_character_name(config: dict | None = None) -> str:
    cfg = config or load_config()
    return cfg.get("character", {}).get("name", "Byulie")


def get_default_system_prompt(config: dict | None = None) -> str:
    cfg = config or load_config()
    return cfg["presets"]["default"]["system_prompt"]


def get_llm_defaults(config: dict | None = None) -> dict:
    cfg = config or load_config()
    return cfg.get("llm", {})


def get_asr_defaults(config: dict | None = None) -> dict:
    cfg = config or load_config()
    return cfg.get("asr", {})


def get_tts_defaults(config: dict | None = None) -> dict:
    cfg = config or load_config()
    return cfg.get("tts", {})


def get_history_path(config: dict | None = None) -> str:
    cfg = config or load_config()
    return _resolve_history_path(cfg["history_file"])
