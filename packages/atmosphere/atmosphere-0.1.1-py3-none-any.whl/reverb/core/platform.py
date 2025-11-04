"""
Reverb Core Platform

Main orchestration system for audio effects processing.
Implements the effects chain: Input -> Delay -> Echo -> Reverb -> Output
"""

from typing import Optional, Tuple

from ..models.signal import (
    AudioSignal,
    DelayParameters,
    EchoParameters,
    ReverbParameters,
    SpatialParameters,
)
from ..services.delay_service import DelayService
from ..services.echo_service import EchoService
from ..services.reverb_service import ReverbService
from ..services.spatial_service import SpatialAudioService


class ReverbPlatform:
    """
    Main platform for processing audio through the effects chain.

    Architecture: Input -> Delay -> Echo -> Reverb -> Output
    """

    def __init__(
        self,
        delay_params: Optional[DelayParameters] = None,
        echo_params: Optional[EchoParameters] = None,
        reverb_params: Optional[ReverbParameters] = None,
        spatial_params: Optional[SpatialParameters] = None,
    ):
        self.delay_service = DelayService(delay_params)
        self.echo_service = EchoService(echo_params)
        self.reverb_service = ReverbService(reverb_params)
        self.spatial_service = SpatialAudioService(spatial_params)

    def get_system_status(self) -> dict:
        """Get status of all services in the platform."""
        return {
            "platform": "reverb",
            "status": "active",
            "services": {
                "delay": self.delay_service.get_status(),
                "echo": self.echo_service.get_status(),
                "reverb": self.reverb_service.get_status(),
                "spatial": self.spatial_service.get_status(),
            },
            "effects_chain": "Input -> Delay -> Echo -> Reverb -> Spatial -> Output",
            "presets": self.get_available_presets(),
        }

    def process_signal(self, signal: AudioSignal) -> AudioSignal:
        """Process audio signal through the complete effects chain."""
        # Phase 1: Delay
        delayed = self.delay_service.process(signal)

        # Phase 2: Echo
        echoed = self.echo_service.process(delayed)

        # Phase 3: Reverb
        reverberated = self.reverb_service.process(echoed)

        # Phase 4: Spatial (converts mono to binaural stereo)
        spatialized = self.spatial_service.process(reverberated)

        return spatialized

    def process_with_custom_params(
        self,
        signal: AudioSignal,
        delay_params: Optional[DelayParameters] = None,
        echo_params: Optional[EchoParameters] = None,
        reverb_params: Optional[ReverbParameters] = None,
        spatial_params: Optional[SpatialParameters] = None,
    ) -> AudioSignal:
        """Process with custom parameters for each effect."""
        # Override defaults if provided
        delayed = self.delay_service.process(signal, delay_params)
        echoed = self.echo_service.process(delayed, echo_params)
        reverberated = self.reverb_service.process(echoed, reverb_params)
        spatialized = self.spatial_service.process(reverberated, params=spatial_params)
        return spatialized

    def spatialize_signal(
        self,
        signal: AudioSignal,
        source_pos: Tuple[float, float, float] = (1, 0, 0),
        listener_pos: Tuple[float, float, float] = (0, 0, 0),
        velocity: Tuple[float, float, float] = (0, 0, 0)
    ) -> AudioSignal:
        """Apply spatial audio processing with specific source parameters."""
        return self.spatial_service.process(
            signal, source_pos, listener_pos, velocity
        )

    def apply_reverb_preset(self, preset_name: str):
        """Apply a reverb preset to the platform."""
        preset_params = self.reverb_service.apply_preset(preset_name)
        # Update default params for future processing
        self.reverb_service.default_params = preset_params
        return preset_params

    def get_available_presets(self) -> list[str]:
        """Get list of available reverb presets."""
        return ["hall", "room", "plate"]

    def process_with_preset(self, signal: AudioSignal, preset_name: str) -> AudioSignal:
        """Process signal using a specific reverb preset."""
        preset_params = self.reverb_service.apply_preset(preset_name)
        return self.process_with_custom_params(
            signal, reverb_params=preset_params
        )
