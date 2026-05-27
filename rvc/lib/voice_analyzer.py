"""voice analyzer — analyze mic input and suggest starting settings.

records a short sample, measures pitch range and timbre characteristics,
then recommends starting values for model selection, pitch shift, formant, etc.
"""

import numpy as np


def analyze_voice(audio: np.ndarray, sample_rate: int = 48000) -> dict:
    """analyze a voice sample and return characteristics + starting suggestions.

    args:
        audio: 1d numpy array of float32 samples
        sample_rate: sample rate in hz

    returns:
        dict with:
          - 'pitch_mean': float (hz) — average fundamental frequency
          - 'pitch_min': float (hz)
          - 'pitch_max': float (hz)
          - 'pitch_range': str — description of range
          - 'timbre': str — 'bright' | 'neutral' | 'warm' | 'breathy'
          - 'suggested_model_type': str
          - 'suggested_pitch_shift': int (semitones)
          - 'suggested_formant': float
          - 'suggested_expression': float
          - 'suggested_warmth': int (0-100)
          - 'confidence': float (0-1)
    """
    result = {
        "pitch_mean": 0,
        "pitch_min": 0,
        "pitch_max": 0,
        "pitch_range": "unknown",
        "timbre": "neutral",
        "suggested_model_type": "any",
        "suggested_pitch_shift": 0,
        "suggested_formant": 1.0,
        "suggested_expression": 0,
        "suggested_warmth": 50,
        "confidence": 0.0,
    }

    if len(audio) < sample_rate:  # need at least 1 second
        result["confidence"] = 0.0
        return result

    try:
        import librosa

        # detect pitch
        f0, voiced_flag, _ = librosa.pyin(
            audio.astype(np.float64),
            fmin=librosa.note_to_hz("C1"),
            fmax=librosa.note_to_hz("C7"),
            sr=sample_rate,
            frame_length=2048,
            hop_length=512,
            fill_na=0.0,
        )

        voiced = voiced_flag & (f0 > 0)
        if not voiced.any():
            result["confidence"] = 0.1
            return result

        pitches = f0[voiced]
        pitch_mean = float(np.median(pitches))
        pitch_min = float(np.min(pitches))
        pitch_max = float(np.max(pitches))

        result["pitch_mean"] = round(pitch_mean, 1)
        result["pitch_min"] = round(pitch_min, 1)
        result["pitch_max"] = round(pitch_max, 1)

        # range description
        range_hz = pitch_max - pitch_min
        if range_hz < 60:
            result["pitch_range"] = "narrow"
        elif range_hz < 150:
            result["pitch_range"] = "moderate"
        else:
            result["pitch_range"] = "wide"

        # detect timbre from spectral features
        spectral = librosa.feature.spectral_centroid(
            y=audio.astype(np.float64), sr=sample_rate
        )
        mean_centroid = float(np.mean(spectral))

        if mean_centroid > 3000:
            result["timbre"] = "bright"
        elif mean_centroid > 2000:
            result["timbre"] = "neutral"
        elif mean_centroid > 1200:
            result["timbre"] = "warm"
        else:
            result["timbre"] = "breathy"

        # spectral rolloff for breathiness estimate
        rolloff = librosa.feature.spectral_rolloff(
            y=audio.astype(np.float64), sr=sample_rate
        )
        mean_rolloff = float(np.mean(rolloff))
        if mean_rolloff < 2000:
            result["timbre"] = "breathy"  # overwrite if very low rolloff

        # --- generate suggestions ---

        # determine voice type from pitch
        if pitch_mean < 145:
            voice_type = "low (typical masc range)"
            result["suggested_pitch_shift"] = 4
            result["suggested_expression"] = 0.3
        elif pitch_mean < 180:
            voice_type = "mid-low"
            result["suggested_pitch_shift"] = 2
            result["suggested_expression"] = 0.2
        elif pitch_mean < 220:
            voice_type = "mid (androgynous range)"
            result["suggested_pitch_shift"] = 0
            result["suggested_expression"] = 0
        elif pitch_mean < 260:
            voice_type = "mid-high"
            result["suggested_pitch_shift"] = -2
            result["suggested_expression"] = -0.2
        else:
            voice_type = "high (typical fem range)"
            result["suggested_pitch_shift"] = -4
            result["suggested_expression"] = -0.3

        # formant and warmth based on timbre
        if result["timbre"] == "bright":
            result["suggested_formant"] = 0.9
            result["suggested_warmth"] = 60
        elif result["timbre"] == "warm":
            result["suggested_formant"] = 1.1
            result["suggested_warmth"] = 40
        elif result["timbre"] == "breathy":
            result["suggested_formant"] = 1.0
            result["suggested_warmth"] = 70
        else:  # neutral
            result["suggested_formant"] = 1.0
            result["suggested_warmth"] = 50

        result["suggested_model_type"] = voice_type

        # confidence based on sample length and voiced ratio
        voiced_ratio = float(voiced.sum() / len(voiced))
        sample_seconds = len(audio) / sample_rate
        result["confidence"] = round(
            min(1.0, voiced_ratio * 0.8 + sample_seconds * 0.02), 2
        )

    except Exception:
        result["confidence"] = 0.0

    return result
