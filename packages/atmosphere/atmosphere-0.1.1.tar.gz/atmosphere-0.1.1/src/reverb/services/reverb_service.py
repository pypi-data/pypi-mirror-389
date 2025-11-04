"""
Reverb Service

Provides advanced reverb effect processing functionality using algorithmic reverb.
Implements Schroeder reverb with comb filters and all-pass filters for realistic space simulation.
"""

import math
from typing import List

from ..models.signal import AudioSignal, ReverbParameters


class CombFilter:
    """Comb filter for reverb - creates delayed feedback."""

    def __init__(self, delay_samples: int, feedback_gain: float, damping: float):
        self.delay_line = [0.0] * delay_samples
        self.delay_samples = delay_samples
        self.feedback_gain = feedback_gain
        self.damping = damping
        self.write_pos = 0

    def process_sample(self, input_sample: float) -> float:
        # Read from delay line
        read_pos = (self.write_pos - self.delay_samples) % self.delay_samples
        delayed_sample = self.delay_line[read_pos]

        # Apply damping
        damped = delayed_sample * (1.0 - self.damping)

        # Calculate output with feedback
        output = input_sample + damped * self.feedback_gain

        # Write to delay line
        self.delay_line[self.write_pos] = output
        self.write_pos = (self.write_pos + 1) % self.delay_samples

        return output


class AllPassFilter:
    """All-pass filter for diffusion in reverb."""

    def __init__(self, delay_samples: int, feedback_gain: float):
        self.delay_line = [0.0] * delay_samples
        self.delay_samples = delay_samples
        self.feedback_gain = feedback_gain
        self.write_pos = 0

    def process_sample(self, input_sample: float) -> float:
        # Read from delay line
        read_pos = (self.write_pos - self.delay_samples) % self.delay_samples
        delayed_sample = self.delay_line[read_pos]

        # All-pass filter formula
        output = -self.feedback_gain * input_sample + delayed_sample + self.feedback_gain * delayed_sample

        # Write to delay line
        self.delay_line[self.write_pos] = input_sample + delayed_sample * self.feedback_gain
        self.write_pos = (self.write_pos + 1) % self.delay_samples

        return output


class ReverbService:
    """Service for applying advanced algorithmic reverb effects to audio signals."""

    def __init__(self, default_params: ReverbParameters = None):
        self.default_params = default_params or ReverbParameters()

        # Schroeder reverb parameters (based on typical values)
        self.comb_delays = [1557, 1617, 1491, 1422, 1277, 1356, 1188, 1116]  # samples at 29.7kHz
        self.allpass_delays = [225, 556, 441, 341]  # samples

        self._initialize_filters()

    def _initialize_filters(self):
        """Initialize comb and all-pass filters."""
        self.comb_filters = []
        self.allpass_filters = []

        # Create comb filters (parallel)
        for delay in self.comb_delays:
            feedback = 0.84  # Typical comb filter feedback
            damping = 0.2    # Initial damping
            self.comb_filters.append(CombFilter(delay, feedback, damping))

        # Create all-pass filters (series)
        for delay in self.allpass_delays:
            feedback = 0.5  # Typical all-pass feedback
            self.allpass_filters.append(AllPassFilter(delay, feedback))

    def process(self, signal: AudioSignal, params: ReverbParameters = None) -> AudioSignal:
        """Apply algorithmic reverb effect to signal."""
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

    def _process_channel(self, channel_data: List[float], params: ReverbParameters, sample_rate: int) -> List[float]:
        """Process a single channel with reverb effect."""
        # Adjust sample rate scaling (our delays are for ~30kHz, scale to actual rate)
        rate_scale = sample_rate / 29761.0

        # Update filter parameters based on reverb params
        self._update_filters(params, rate_scale)

        # Process signal
        wet_data = []
        for sample in channel_data:
            # Pre-delay
            pre_delayed = sample  # Simplified - in practice, add actual delay buffer

            # Parallel comb filters
            comb_output = 0.0
            for comb_filter in self.comb_filters:
                comb_output += comb_filter.process_sample(pre_delayed)
            comb_output /= len(self.comb_filters)  # Average

            # Series all-pass filters for diffusion
            diffused = comb_output
            for allpass_filter in self.allpass_filters:
                diffused = allpass_filter.process_sample(diffused)

            # Apply RT60 decay
            # For simplicity, apply exponential decay based on RT60
            sample_index = len(wet_data)
            decay_factor = math.exp(-sample_index / (params.rt60 * sample_rate))
            diffused *= decay_factor

            wet_data.append(diffused)

        # Mix dry/wet
        mixed_data = []
        for dry, wet in zip(channel_data, wet_data):
            mixed = dry * (1 - params.wet_dry_mix) + wet * params.wet_dry_mix
            mixed_data.append(mixed)

        return mixed_data

    def _update_filters(self, params: ReverbParameters, rate_scale: float):
        """Update filter parameters based on reverb settings."""
        # Scale delays
        scaled_comb_delays = [int(d * rate_scale) for d in self.comb_delays]
        scaled_allpass_delays = [int(d * rate_scale) for d in self.allpass_delays]

        # Recreate filters with new delays and parameters
        self.comb_filters = []
        for delay in scaled_comb_delays:
            # Feedback based on RT60
            feedback = math.exp(-3.0 * delay / (params.rt60 * 44100))  # Approximation
            damping = params.damping
            self.comb_filters.append(CombFilter(delay, feedback, damping))

        self.allpass_filters = []
        for delay in scaled_allpass_delays:
            feedback = 0.5  # Keep constant for diffusion
            self.allpass_filters.append(AllPassFilter(delay, feedback))

    def get_hall_preset(self) -> ReverbParameters:
        """Get parameters for large concert hall reverb."""
        return ReverbParameters(
            rt60=2.5,
            pre_delay=0.08,
            damping=0.3,
            wet_dry_mix=0.4,
        )

    def get_room_preset(self) -> ReverbParameters:
        """Get parameters for medium room reverb."""
        return ReverbParameters(
            rt60=0.8,
            pre_delay=0.02,
            damping=0.5,
            wet_dry_mix=0.3,
        )

    def get_plate_preset(self) -> ReverbParameters:
        """Get parameters for classic plate reverb."""
        return ReverbParameters(
            rt60=1.2,
            pre_delay=0.01,
            damping=0.2,
            wet_dry_mix=0.5,
        )

    def apply_preset(self, preset_name: str) -> ReverbParameters:
        """Apply a preset by name."""
        presets = {
            "hall": self.get_hall_preset,
            "room": self.get_room_preset,
            "plate": self.get_plate_preset,
        }
        if preset_name in presets:
            return presets[preset_name]()
        else:
            raise ValueError(f"Unknown preset: {preset_name}. Available: {list(presets.keys())}")

    def get_status(self) -> dict:
        """Get service status."""
        return {
            "service": "reverb",
            "status": "active",
            "algorithm": "Schroeder reverb (comb + all-pass filters)",
            "filters": {
                "comb_filters": len(self.comb_filters),
                "allpass_filters": len(self.allpass_filters),
            },
            "presets": ["hall", "room", "plate"],
            "default_params": self.default_params.to_dict(),
        }
