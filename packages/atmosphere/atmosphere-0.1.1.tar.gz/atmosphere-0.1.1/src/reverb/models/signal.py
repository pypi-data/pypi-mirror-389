"""
Audio Signal Models

Defines data structures for representing audio signals and their properties.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class AudioSignal:
    """Represents an audio signal with metadata."""

    data: List[List[float]]  # List of channel data (e.g., [[left_samples], [right_samples]])
    sample_rate: int = 44100  # Hz
    channels: int = 1  # Number of channels (1=mono, 2=stereo, etc.)
    duration: Optional[float] = None  # seconds

    def __post_init__(self):
        if len(self.data) != self.channels:
            raise ValueError(f"Data has {len(self.data)} channels but channels parameter is {self.channels}")
        
        if self.duration is None:
            self.duration = len(self.data[0]) / self.sample_rate

    def to_dict(self) -> dict:
        return {
            "data": self.data,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "duration": self.duration,
        }

    @staticmethod
    def from_dict(data: dict) -> "AudioSignal":
        return AudioSignal(**data)

    @classmethod
    def create_mono(cls, data: List[float], sample_rate: int = 44100) -> "AudioSignal":
        """Create a mono audio signal."""
        return cls(data=[data], sample_rate=sample_rate, channels=1)

    @classmethod
    def create_stereo(cls, left_data: List[float], right_data: List[float], sample_rate: int = 44100) -> "AudioSignal":
        """Create a stereo audio signal."""
        return cls(data=[left_data, right_data], sample_rate=sample_rate, channels=2)


@dataclass
class EffectParameters:
    """Base class for effect parameters."""

    enabled: bool = True
    wet_dry_mix: float = 0.5  # 0=dry, 1=wet

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "wet_dry_mix": self.wet_dry_mix,
        }


@dataclass
class DelayParameters(EffectParameters):
    """Parameters for delay effect."""

    time_ms: float = 250.0
    feedback: float = 0.3
    level: float = 0.5


@dataclass
class EchoParameters(EffectParameters):
    """Parameters for echo effect."""

    time_ms: float = 500.0
    feedback: float = 0.4
    decay: float = 0.6
    level: float = 0.5


@dataclass
class ReverbParameters(EffectParameters):
    """Parameters for reverb effect."""

    rt60: float = 1.0  # seconds
    pre_delay: float = 0.05  # seconds
    damping: float = 0.5  # 0-1


@dataclass
class SpatialParameters(EffectParameters):
    """Parameters for spatial audio processing."""
    
    hrtf_enabled: bool = True
    doppler_enabled: bool = True
    distance_attenuation_enabled: bool = True
    reverb_enabled: bool = True
    
    # HRTF settings
    hrtf_resolution: int = 8  # Number of directions for HRTF
    
    # Doppler settings
    speed_of_sound: float = 343.0  # m/s in air at 20°C
    
    # Distance attenuation
    reference_distance: float = 1.0  # Distance where attenuation starts
    rolloff_factor: float = 1.0  # How fast sound attenuates
    
    # Reverb integration
    reverb_mix: float = 0.3  # How much reverb to mix in
