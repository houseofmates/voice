"""soundboard — record, store, and play processed voice clips.

each slot has:
  - a name (user-chosen)
  - an audio array (numpy, processed through the current voice pipeline)
  - a hotkey (optional, for external use)

stored in ~/voice/models/soundboard/ as wav files.
"""

import os
import json
import numpy as np
import soundfile as sf

SOUNDBOARD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models", "soundboard")
INDEX_PATH = os.path.join(SOUNDBOARD_DIR, "index.json")


def _ensure():
    os.makedirs(SOUNDBOARD_DIR, exist_ok=True)
    if not os.path.exists(INDEX_PATH):
        with open(INDEX_PATH, "w") as f:
            json.dump({}, f)


def _read_index() -> dict:
    _ensure()
    try:
        with open(INDEX_PATH, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _write_index(data: dict):
    _ensure()
    with open(INDEX_PATH, "w") as f:
        json.dump(data, f, indent=2)


def list_slots() -> list[dict]:
    """return list of {id, name, duration_sec} for all slots."""
    idx = _read_index()
    result = []
    for slot_id, meta in idx.items():
        result.append({
            "id": slot_id,
            "name": meta.get("name", f"slot {slot_id}"),
            "duration_sec": meta.get("duration_sec", 0),
        })
    return result


def save_slot(slot_id: str, name: str, audio: np.ndarray, sample_rate: int = 48000):
    """save audio to a soundboard slot."""
    _ensure()
    path = os.path.join(SOUNDBOARD_DIR, f"{slot_id}.wav")
    sf.write(path, audio, sample_rate)

    idx = _read_index()
    idx[slot_id] = {
        "name": name,
        "duration_sec": round(len(audio) / sample_rate, 1),
        "sample_rate": sample_rate,
    }
    _write_index(idx)


def load_slot(slot_id: str) -> tuple[np.ndarray | None, int]:
    """load audio + sample_rate for a slot. returns (audio, sr) or (None, 0)."""
    path = os.path.join(SOUNDBOARD_DIR, f"{slot_id}.wav")
    if os.path.exists(path):
        return sf.read(path)
    return None, 0


def delete_slot(slot_id: str):
    """remove a soundboard slot."""
    path = os.path.join(SOUNDBOARD_DIR, f"{slot_id}.wav")
    if os.path.exists(path):
        os.remove(path)

    idx = _read_index()
    if slot_id in idx:
        del idx[slot_id]
        _write_index(idx)


def next_id() -> str:
    """get the next available slot id."""
    idx = _read_index()
    existing = [int(k) for k in idx.keys() if k.isdigit()]
    return str(max(existing) + 1 if existing else 1)