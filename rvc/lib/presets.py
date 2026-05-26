"""voice preset system — save/load/delete named voice configurations.

a preset stores:
  - model file path
  - index file path
  - pitch shift
  - formant
  - breathiness
  - expression tone
  - comfort shield enabled
  - warmth level
  - input/output device names
  - f0 method
  - index rate
  - volume envelope
  - protect

stored in ~/voice/models/presets.json as a flat dict of name -> config.
"""

import json
import os
from datetime import datetime

PRESETS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models", "presets.json")


def _ensure_file():
    os.makedirs(os.path.dirname(PRESETS_PATH), exist_ok=True)
    if not os.path.exists(PRESETS_PATH):
        with open(PRESETS_PATH, "w") as f:
            json.dump({}, f)


def _read():
    _ensure_file()
    try:
        with open(PRESETS_PATH, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _write(data):
    _ensure_file()
    with open(PRESETS_PATH, "w") as f:
        json.dump(data, f, indent=2)


def list_presets() -> list[str]:
    """return sorted list of preset names."""
    data = _read()
    return sorted(data.keys())


def save_preset(name: str, config: dict) -> bool:
    """save a named preset. returns True on success."""
    data = _read()
    data[name] = {
        **config,
        "_updated": datetime.now().isoformat(),
    }
    _write(data)
    return True


def load_preset(name: str) -> dict | None:
    """load a named preset. returns None if not found."""
    data = _read()
    return data.get(name)


def delete_preset(name: str) -> bool:
    """delete a named preset. returns True if existed."""
    data = _read()
    if name in data:
        del data[name]
        _write(data)
        return True
    return False


# === last session (auto-resume) ===
LAST_SESSION_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models", "last_session.json")


def save_last_session(config: dict):
    """save the most recent session config for one-click resume."""
    os.makedirs(os.path.dirname(LAST_SESSION_PATH), exist_ok=True)
    with open(LAST_SESSION_PATH, "w") as f:
        json.dump(config, f, indent=2)


def load_last_session() -> dict | None:
    """load the last session config. returns None if no session saved."""
    try:
        if os.path.exists(LAST_SESSION_PATH):
            with open(LAST_SESSION_PATH, "r") as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError):
        pass
    return None


def clear_last_session():
    """clear the saved last session."""
    if os.path.exists(LAST_SESSION_PATH):
        os.remove(LAST_SESSION_PATH)


# === default preset ===
DEFAULT_CONFIG = {
    "model_file": "",
    "index_file": "",
    "pitch_shift": 0,
    "formant": 1.0,
    "breathiness": 0,
    "expression": 0,
    "comfort_enabled": False,
    "warmth": 50,
    "input_device": "",
    "output_device": "",
    "f0_method": "rmvpe",
    "index_rate": 0.75,
    "volume_envelope": 1.0,
    "protect": 0.5,
}


def get_default_config() -> dict:
    """return a copy of the default config."""
    return dict(DEFAULT_CONFIG)