"""
Delay Service

Provides delay effect processing functionality.
"""

from typing import List

from ..models.signal import AudioSignal, DelayParameters


class DelayService:
    """Service for applying delay effects to audio signals."""

    def __init__(self, default_params: DelayParameters = None):
        self.default_params = default_params or DelayParameters()

    def process(self, signal: AudioSignal, params: DelayParameters = None) -> AudioSignal:
        """Apply delay effect to signal."""
        params = params or self.default_params

        if not params.enabled:
            return signal

        # Process each channel separately
        processed_channels = []
        for channel_data in signal.data:
            processed_channel = self._process_channel(channel_data, params, signal.sample_rate)
            processed_channels.append(processed_channel)

        return AudioSignal(
            data=processed_channels,
            sample_rate=signal.sample_rate,
            channels=signal.channels
        )

    def _process_channel(self, channel_data: List[float], params: DelayParameters, sample_rate: int) -> List[float]:
        """Process a single channel with delay effect."""
        # Simplified delay implementation
        delay_samples = int((params.time_ms / 1000) * sample_rate)
        delayed_data = [0.0] * delay_samples + channel_data

        # Apply feedback and level
        feedback_gain = params.feedback
        level_gain = params.level

        # Mix dry and wet
        wet_data = []
        for i, sample in enumerate(channel_data):
            delayed_sample = delayed_data[i] * level_gain
            if i >= delay_samples:
                delayed_sample += wet_data[i - delay_samples] * feedback_gain
            wet_data.append(delayed_sample)

        # Mix dry/wet
        mixed_data = []
        for dry, wet in zip(channel_data, wet_data):
            mixed = dry * (1 - params.wet_dry_mix) + wet * params.wet_dry_mix
            mixed_data.append(mixed)

        return mixed_data

    def get_status(self) -> dict:
        """Get service status."""
        return {
            "service": "delay",
            "status": "active",
            "default_params": self.default_params.to_dict(),
        }
