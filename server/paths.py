"""Windows-friendly repository paths shared by Byulie server modules."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / "character_config.yaml"
AUDIO_DIR = REPO_ROOT / "audio"
