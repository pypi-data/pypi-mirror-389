"""
Spatial Audio Service

Provides 3D spatial audio processing including HRTF, Doppler effect, distance attenuation, and reverb integration.
Implements binaural rendering for immersive audio experiences.
"""

import math
import numpy as np
from typing import List, Tuple, Dict, Optional

from ..models.signal import AudioSignal, SpatialParameters, ReverbParameters


class ReverbSpace:
    """Simulates an acoustic environment for spatial audio processing."""
    
    def __init__(self, size: float, reflectivity: float, rt60: float):
        self.size = size  # Room dimensions (m³)
        self.reflectivity = reflectivity  # 0-1 surface absorption
        self.rt60 = rt60  # Time for 60dB decay
        
    def calculate_absorption(self, frequency: float) -> float:
        """Calculate frequency-dependent absorption."""
        # Simplified model - more HF absorption
        return self.reflectivity * (1 + (frequency / 1000))
    
    def process(self, left_ear: np.ndarray, right_ear: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Apply reverb to binaural audio."""
        # Simple reverb approximation - in practice, use convolution reverb
        # This is a placeholder for full reverb implementation
        decay_factor = math.exp(-1.0 / (self.rt60 * 44100))  # Sample rate assumption
        
        # Apply decay to simulate reverb
        reverb_left = left_ear * decay_factor
        reverb_right = right_ear * decay_factor
        
        return reverb_left, reverb_right


class SpatialAudioService:
    """Service for 3D spatial audio processing with binaural rendering."""
    
    def __init__(self, default_params: SpatialParameters = None):
        self.default_params = default_params or SpatialParameters()
        
        # Initialize HRTF data (simplified - real HRTF uses measured data)
        self.hrtf_data = self._generate_simple_hrtf()
        
        # Initialize reverb space
        self.reverb_space = ReverbSpace(size=100, reflectivity=0.7, rt60=1.5)
        
    def _generate_simple_hrtf(self) -> Dict[str, Dict[str, np.ndarray]]:
        """Generate simplified HRTF data for different directions."""
        # This is a highly simplified HRTF - real implementations use measured data
        hrtf_data = {}
        
        # Generate HRTF for 8 directions (0°, 45°, 90°, 135°, 180°, 225°, 270°, 315°)
        for azimuth_deg in range(0, 360, 45):
            azimuth_rad = math.radians(azimuth_deg)
            
            # Simple ITD model (Interaural Time Difference)
            itd_samples = int(0.0005 * 44100 * math.sin(azimuth_rad))  # ~0.5ms max
            
            # Simple ILD model (Interaural Level Difference)  
            ild_db = -3 * math.sin(azimuth_rad)  # 3dB max difference
            ild_factor_left = 10 ** (ild_db / 20) if ild_db < 0 else 1.0
            ild_factor_right = 10 ** (-ild_db / 20) if ild_db > 0 else 1.0
            
            # Create simple FIR filters (in practice, use actual HRTF measurements)
            filter_length = 128
            hrtf_left = np.zeros(filter_length)
            hrtf_right = np.zeros(filter_length)
            
            # Add delay and level differences
            if itd_samples > 0:
                hrtf_left[itd_samples] = ild_factor_left
                hrtf_right[0] = ild_factor_right
            else:
                hrtf_left[0] = ild_factor_left
                hrtf_right[-itd_samples] = ild_factor_right
            
            hrtf_data[str(azimuth_deg)] = {
                'left': hrtf_left,
                'right': hrtf_right
            }
            
        return hrtf_data
    
    def _get_hrtf_filters(self, direction: Tuple[float, float, float]) -> Tuple[np.ndarray, np.ndarray]:
        """Get HRTF filters for a given 3D direction."""
        # Convert 3D direction to azimuth angle
        x, y, z = direction
        azimuth_rad = math.atan2(y, x)
        azimuth_deg = int(math.degrees(azimuth_rad)) % 360
        
        # Find closest HRTF direction
        closest_angle = min(self.hrtf_data.keys(), 
                          key=lambda k: min(abs(int(k) - azimuth_deg), 360 - abs(int(k) - azimuth_deg)))
        
        hrtf = self.hrtf_data[closest_angle]
        return hrtf['left'], hrtf['right']
    
    def _calculate_doppler_shift(self, source_velocity: Tuple[float, float, float], 
                               direction: Tuple[float, float, float]) -> float:
        """Calculate Doppler shift factor."""
        params = self.default_params
        if not params.doppler_enabled:
            return 1.0
            
        # Calculate relative velocity along line of sight
        vx, vy, vz = source_velocity
        dx, dy, dz = direction
        
        # Normalize direction
        dist = math.sqrt(dx**2 + dy**2 + dz**2)
        if dist == 0:
            return 1.0
            
        dx /= dist
        dy /= dist  
        dz /= dist
        
        # Relative velocity component along line of sight
        relative_velocity = vx * dx + vy * dy + vz * dz
        
        # Doppler formula: f' = f * (c ± v_listener) / (c ∓ v_source)
        # Simplified: assume listener stationary
        if abs(relative_velocity) < params.speed_of_sound:
            doppler_factor = params.speed_of_sound / (params.speed_of_sound - relative_velocity)
        else:
            doppler_factor = 1.0  # Avoid division by zero
            
        return doppler_factor
    
    def _pitch_shift(self, audio: np.ndarray, shift_factor: float) -> np.ndarray:
        """Apply pitch shifting for Doppler effect."""
        if abs(shift_factor - 1.0) < 0.001:
            return audio
            
        # Simple pitch shifting using resampling (basic implementation)
        # In practice, use more sophisticated algorithms like phase vocoder
        from scipy import signal
        
        new_length = int(len(audio) / shift_factor)
        shifted = signal.resample(audio, new_length)
        
        # Pad or truncate to original length
        if len(shifted) > len(audio):
            shifted = shifted[:len(audio)]
        elif len(shifted) < len(audio):
            shifted = np.pad(shifted, (0, len(audio) - len(shifted)), 'constant')
            
        return shifted
    
    def _apply_distance_attenuation(self, distance: float) -> float:
        """Calculate distance attenuation factor."""
        params = self.default_params
        if not params.distance_attenuation_enabled or distance <= 0:
            return 1.0
            
        # Inverse square law with reference distance
        if distance < params.reference_distance:
            return 1.0
            
        attenuation = params.reference_distance / (params.reference_distance + 
                                                 params.rolloff_factor * (distance - params.reference_distance))
        return attenuation
    
    def spatialize_sound(self, mono_audio: np.ndarray, 
                        source_pos: Tuple[float, float, float], 
                        listener_pos: Tuple[float, float, float] = (0, 0, 0),
                        velocity: Tuple[float, float, float] = (0, 0, 0)) -> Tuple[np.ndarray, np.ndarray]:
        """Spatialize mono audio to binaural output."""
        params = self.default_params
        
        # 1. Calculate direction and distance
        direction = np.array(source_pos) - np.array(listener_pos)
        distance = np.linalg.norm(direction)
        if distance == 0:
            direction = np.array([1, 0, 0])  # Default forward
        else:
            direction = direction / distance  # Normalize
        
        # 2. Apply distance attenuation (inverse square law)
        distance_factor = self._apply_distance_attenuation(distance)
        
        # 3. Apply HRTF filtering based on direction
        if params.hrtf_enabled:
            hrtf_left, hrtf_right = self._get_hrtf_filters(tuple(direction))
            
            # Apply HRTF convolution
            left_ear = np.convolve(mono_audio, hrtf_left, mode='same')
            right_ear = np.convolve(mono_audio, hrtf_right, mode='same')
        else:
            # No HRTF - just duplicate mono to stereo
            left_ear = mono_audio.copy()
            right_ear = mono_audio.copy()
        
        # 4. Apply Doppler effect if moving
        if params.doppler_enabled and np.any(velocity != 0):
            doppler_shift = self._calculate_doppler_shift(velocity, tuple(direction))
            left_ear = self._pitch_shift(left_ear, doppler_shift)
            right_ear = self._pitch_shift(right_ear, doppler_shift)
        
        # 5. Apply distance attenuation
        left_ear *= distance_factor
        right_ear *= distance_factor
        
        # 6. Add reverb based on environment
        if params.reverb_enabled:
            reverb_left, reverb_right = self.reverb_space.process(left_ear, right_ear)
            
            # Mix dry and wet signals
            wet_mix = params.reverb_mix
            left_ear = left_ear * (1 - wet_mix) + reverb_left * wet_mix
            right_ear = right_ear * (1 - wet_mix) + reverb_right * wet_mix
        
        return left_ear, right_ear
    
    def process(self, signal: AudioSignal, 
               source_pos: Tuple[float, float, float] = (1, 0, 0),
               listener_pos: Tuple[float, float, float] = (0, 0, 0),
               velocity: Tuple[float, float, float] = (0, 0, 0),
               params: SpatialParameters = None) -> AudioSignal:
        """Process mono audio signal to spatial binaural output."""
        params = params or self.default_params
        
        if not params.enabled or signal.channels != 1:
            return signal
            
        # Get mono audio data
        mono_data = np.array(signal.data[0])
        
        # Spatialize to binaural
        left_ear, right_ear = self.spatialize_sound(mono_data, source_pos, listener_pos, velocity)
        
        # Create stereo output
        stereo_signal = AudioSignal.create_stereo(
            left_data=left_ear.tolist(),
            right_data=right_ear.tolist(),
            sample_rate=signal.sample_rate
        )
        
        return stereo_signal
    
    def get_status(self) -> dict:
        """Get service status."""
        return {
            "service": "spatial_audio",
            "status": "active",
            "features": {
                "hrtf": self.default_params.hrtf_enabled,
                "doppler": self.default_params.doppler_enabled,
                "distance_attenuation": self.default_params.distance_attenuation_enabled,
                "reverb_integration": self.default_params.reverb_enabled
            },
            "reverb_space": {
                "size": self.reverb_space.size,
                "reflectivity": self.reverb_space.reflectivity,
                "rt60": self.reverb_space.rt60
            }
        }
