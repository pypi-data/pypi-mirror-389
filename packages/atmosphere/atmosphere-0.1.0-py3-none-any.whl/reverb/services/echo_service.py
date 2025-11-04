"""
Echo Service

Provides echo effect processing functionality.
"""

from typing import List

from ..models.signal import AudioSignal, EchoParameters


class EchoService:
    """Service for applying echo effects to audio signals."""

    def __init__(self, default_params: EchoParameters = None):
        self.default_params = default_params or EchoParameters()

    def process(self, signal: AudioSignal, params: EchoParameters = None) -> AudioSignal:
        """Apply echo effect to signal."""
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

    def _process_channel(self, channel_data: List[float], params: EchoParameters, sample_rate: int) -> List[float]:
        """Process a single channel with echo effect."""
        # Simplified echo implementation (multiple delays)
        echo_samples = int((params.time_ms / 1000) * sample_rate)

        # Create multiple echoes with decay
        echoes = []
        current_level = params.level
        for i in range(5):  # 5 echoes
            delay = echo_samples * (i + 1)
            level = current_level * (params.decay ** i)
            echoes.append((delay, level))
            current_level *= params.feedback

        # Generate echoed signal
        max_delay = max(d[0] for d in echoes)
        extended_data = channel_data + [0.0] * max_delay

        wet_data = [0.0] * len(channel_data)
        for delay, level in echoes:
            for i in range(len(channel_data)):
                if i + delay < len(extended_data):
                    wet_data[i] += extended_data[i + delay] * level

        # Mix dry/wet
        mixed_data = []
        for dry, wet in zip(channel_data, wet_data):
            mixed = dry * (1 - params.wet_dry_mix) + wet * params.wet_dry_mix
            mixed_data.append(mixed)

        return mixed_data

    def get_status(self) -> dict:
        """Get service status."""
        return {
            "service": "echo",
            "status": "active",
            "default_params": self.default_params.to_dict(),
        }
