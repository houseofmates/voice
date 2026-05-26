"""Voice - Pitch Detection Module

Real-time pitch detection for the pitch guide feature.
Uses librosa for pitch extraction with minimal latency.
"""

import numpy as np


# Cache the pitch detection function to avoid re-importing librosa
_pitch_func = None


def _get_pitch_func():
    """Lazy-load librosa pitch detection."""
    global _pitch_func
    if _pitch_func is not None:
        return _pitch_func
    
    # Try CREPE first (more accurate), fall back to librosa PYIN
    try:
        import torchcrepe
        _pitch_func = lambda audio, sr: _detect_crepe(audio, sr)
        return _pitch_func
    except ImportError:
        pass
    
    try:
        import librosa
        _pitch_func = lambda audio, sr: _detect_librosa(audio, sr)
        return _pitch_func
    except ImportError:
        _pitch_func = lambda audio, sr: (0.0, False)
        return _pitch_func


def _detect_crepe(audio: np.ndarray, sr: int) -> tuple:
    """Detect pitch using CREPE (quality, higher latency)."""
    try:
        import torch
        import torchcrepe
        audio_t = torch.from_numpy(audio).float()
        # Use small model for speed, batch_size=1, step length for quick detection
        pitch, confidence = torchcrepe.predict(
            audio_t.unsqueeze(0),
            sr,
            hop_length=int(sr * 0.05),  # 50ms windows
            model_capacity="tiny",
            return_periodicity=True,
        )
        # Get the most confident pitch
        conf = confidence[0].max().item()
        if conf > 0.3:
            idx = confidence[0].argmax().item()
            freq = pitch[0, idx].item()
            return freq, True
        return 0.0, False
    except Exception:
        return _detect_librosa(audio, sr)


def _detect_librosa(audio: np.ndarray, sr: int) -> tuple:
    """Detect pitch using librosa PYIN."""
    try:
        import librosa
        # Use a short analysis window for responsiveness
        f0, voiced_flag, _ = librosa.pyin(
            audio.astype(np.float64),
            fmin=librosa.note_to_hz('C1'),  # ~32Hz
            fmax=librosa.note_to_hz('C7'),  # ~2093Hz
            sr=sr,
            frame_length=2048,
            hop_length=512,
            fill_na=0.0,
        )
        voiced = voiced_flag.any()
        if voiced:
            # Return the mean pitch of voiced frames
            pitch_vals = f0[voiced_flag]
            if len(pitch_vals) > 0:
                return float(np.median(pitch_vals[pitch_vals > 0])), True
        return 0.0, False
    except Exception:
        return 0.0, False


def detect_pitch(audio: np.ndarray, sample_rate: int = 48000) -> dict:
    """Detect the fundamental frequency of an audio buffer.
    
    Args:
        audio: 1D numpy array of audio samples
        sample_rate: Sample rate in Hz
        
    Returns:
        dict with keys:
            - 'frequency': float Hz (0.0 if no pitch detected)
            - 'detected': bool
            - 'note': str (MIDI note name, e.g. 'A4')
    """
    if len(audio) < 256:
        return {'frequency': 0.0, 'detected': False, 'note': '--'}
    
    detector = _get_pitch_func()
    freq, detected = detector(audio, sample_rate)
    
    # Convert to note name if detected
    note = '--'
    if detected and freq > 20:
        try:
            import librosa
            note = librosa.hz_to_note(float(freq))
        except Exception:
            # Approximate note name
            note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            if freq > 0:
                midi = 69 + 12 * np.log2(freq / 440.0)
                midi = int(round(midi))
                octave = (midi // 12) - 1
                note_idx = midi % 12
                note = f"{note_names[note_idx]}{octave}"
    
    return {
        'frequency': round(freq, 1) if detected else 0.0,
        'detected': detected,
        'note': note,
    }


def mic_test(device_name: str, duration: float = 5.0, 
             sample_rate: int = 48000) -> np.ndarray:
    """Record audio from microphone for testing.
    
    Args:
        device_name: Audio device name/identifier
        duration: Recording duration in seconds
        sample_rate: Sample rate in Hz
        
    Returns:
        Recorded audio as 1D numpy array
    """
    try:
        import sounddevice as sd
        
        # Find device index from name string
        devices = sd.query_devices()
        device_id = None
        for i, dev in enumerate(devices):
            if device_name and (device_name in dev['name'] or str(i) in device_name):
                device_id = i
                break
        
        if device_id is None and device_name:
            # Try matching by number prefix
            try:
                parts = device_name.split(':')
                device_id = int(parts[0].strip()) - 1
            except (ValueError, IndexError):
                device_id = sd.default.device[0]
        else:
            device_id = sd.default.device[0]
        
        frames = int(duration * sample_rate)
        recording = sd.rec(frames, samplerate=sample_rate, 
                          channels=1, device=device_id, dtype='float32')
        sd.wait()
        return recording.flatten()
    
    except Exception as e:
        print(f"Mic test error: {e}")
        # Return silence on error
        return np.zeros(int(duration * sample_rate))