"""Voice - Comfort Shield Audio Processing Module

Applies real-time audio post-processing to reduce dysphoria:
- Gentle formant smoothing (low-pass with resonance)
- Warmth/harmonic exciter (soft saturation)
- Designed for <5ms additional latency

All operations use numpy/scipy - no extra dependencies needed.
"""

import numpy as np
from scipy import signal
from scipy.ndimage import gaussian_filter1d


class ComfortShield:
    """Applies comfort audio processing to voice output.

    When enabled, this filter chain runs on the voice output to:
    1. Smooth formants (gentle low-pass with resonance control)
    2. Add warmth (soft harmonic saturation)
    """

    def __init__(self, sample_rate: int = 48000):
        self.sample_rate = sample_rate
        self.warmth = 0.5  # 0.0 to 1.0
        self.enabled = False

        # Pre-compute filter coefficients
        self._build_filters()

    def _build_filters(self):
        """Build the formant smoothing filter (gentle low-pass with resonance)."""
        # 2nd order Butterworth low-pass at 8kHz - smooths harsh formants
        # while preserving voice clarity
        self.sos = signal.butter(2, 8000, "low", fs=self.sample_rate, output="sos")

        # Build a subtle resonant peak at ~3kHz for warmth
        self.warmth_sos = signal.butter(
            2, [200, 4000], "band", fs=self.sample_rate, output="sos"
        )

    def process(self, audio: np.ndarray) -> np.ndarray:
        """Apply comfort processing to audio buffer.

        Args:
            audio: 1D numpy array of float32 samples in [-1, 1]

        Returns:
            Processed audio array (same shape)
        """
        if not self.enabled or len(audio) == 0:
            return audio

        # 1. Formant smoothing - gentle low-pass
        smoothed = signal.sosfilt(self.sos, audio)

        # 2. Warmth - soft harmonic saturation (tube-like)
        if self.warmth > 0.01:
            # Soft clip with gentle curve
            warmth_gain = 1.0 + self.warmth * 0.5
            warm = np.tanh(audio * warmth_gain) * 0.8 + audio * 0.2

            # Blend warmth based on setting
            blend = self.warmth
            smoothed = smoothed * (1 - blend * 0.3) + warm * (blend * 0.3)

        # 3. Gentle normalization to prevent clipping
        max_val = np.max(np.abs(smoothed))
        if max_val > 0.95:
            smoothed = smoothed * (0.95 / max_val)

        return smoothed

    def set_warmth(self, value: float):
        """Set warmth level (0.0 to 1.0)."""
        self.warmth = np.clip(value, 0.0, 1.0)

    def set_enabled(self, enabled: bool):
        """Enable or disable the comfort shield."""
        self.enabled = enabled


# Singleton instance for use across the app
_default_shield = None


def get_comfort_shield(sample_rate: int = 48000) -> ComfortShield:
    """Get or create the default ComfortShield singleton."""
    global _default_shield
    if _default_shield is None:
        _default_shield = ComfortShield(sample_rate)
    return _default_shield


def apply_comfort(
    audio: np.ndarray,
    enabled: bool = True,
    warmth: float = 0.5,
    sample_rate: int = 48000,
) -> np.ndarray:
    """Convenience function to apply comfort processing in one call.

    Args:
        audio: Audio samples as 1D numpy array
        enabled: Whether to apply processing
        warmth: Warmth level 0.0-1.0
        sample_rate: Sample rate of the audio

    Returns:
        Processed audio
    """
    shield = get_comfort_shield(sample_rate)
    shield.set_enabled(enabled)
    shield.set_warmth(warmth)
    return shield.process(audio)
