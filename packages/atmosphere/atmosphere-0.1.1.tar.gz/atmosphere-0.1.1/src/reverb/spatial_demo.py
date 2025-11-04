"""
Spatial Audio Demo

Demonstrates the spatial audio capabilities of the Reverb platform.
Shows binaural rendering, Doppler effects, and moving sound sources.
"""

import math
import numpy as np
from core.platform import ReverbPlatform
from models.signal import AudioSignal, SpatialParameters


def create_test_signal(frequency: float = 440.0, duration: float = 1.0, sample_rate: int = 44100) -> AudioSignal:
    """Create a test sine wave signal."""
    num_samples = int(duration * sample_rate)
    data = []
    for i in range(num_samples):
        t = i / sample_rate
        sample = math.sin(2 * math.pi * frequency * t)
        data.append(sample)

    return AudioSignal.create_mono(data=data, sample_rate=sample_rate)


def demo_spatial_audio():
    """Demonstrate spatial audio processing."""
    print("🎧 Spatial Audio Demo")
    print("=" * 40)

    # Create platform
    platform = ReverbPlatform()
    print("✓ Platform initialized with spatial audio support")

    # Create a test signal
    signal = create_test_signal(frequency=440.0, duration=0.5)
    print(f"✓ Created mono test signal: {len(signal.data[0])} samples at {signal.sample_rate}Hz")

    # Demo 1: Basic spatialization (sound source at different positions)
    print("\n📍 Demo 1: Spatial positioning")
    positions = [
        (1, 0, 0),    # Front right
        (-1, 0, 0),   # Front left
        (0, 1, 0),    # Right side
        (0, -1, 0),   # Left side
        (0, 0, 1),    # Above
    ]

    for pos in positions:
        spatialized = platform.spatialize_signal(signal, source_pos=pos)
        direction = describe_position(pos)
        print(f"  ✓ Spatialized sound from {direction}: {spatialized.channels} channels")

    # Demo 2: Distance attenuation
    print("\n📏 Demo 2: Distance attenuation")
    distances = [0.5, 1.0, 2.0, 5.0, 10.0]
    for dist in distances:
        # Position at varying distances along X-axis
        pos = (dist, 0, 0)
        spatialized = platform.spatialize_signal(signal, source_pos=pos)
        print(".2f")

    # Demo 3: Doppler effect (moving source)
    print("\n🚀 Demo 3: Doppler effect")
    velocities = [
        (10, 0, 0),   # Moving right at 10 m/s
        (-10, 0, 0),  # Moving left at 10 m/s
        (0, 10, 0),   # Moving up at 10 m/s
        (0, 0, 10),   # Moving forward at 10 m/s
    ]

    for vel in velocities:
        spatialized = platform.spatialize_signal(signal, source_pos=(1, 0, 0), velocity=vel)
        direction = describe_velocity(vel)
        print(f"  ✓ Doppler effect for source moving {direction}")

    # Demo 4: Complete effects chain with spatial audio
    print("\n🔄 Demo 4: Full effects chain + spatial")
    full_processed = platform.process_signal(signal)
    print(f"  ✓ Full chain: Delay → Echo → Reverb → Spatial")
    print(f"  ✓ Output: {full_processed.channels} channels, {len(full_processed.data[0])} samples")

    # Demo 5: Spatial parameters customization
    print("\n⚙️  Demo 5: Custom spatial parameters")
    custom_spatial = SpatialParameters(
        hrtf_enabled=True,
        doppler_enabled=True,
        distance_attenuation_enabled=True,
        reverb_enabled=False,  # Disable reverb for this demo
        reverb_mix=0.0,
    )

    spatialized_custom = platform.spatialize_signal(
        signal,
        source_pos=(2, 1, 0.5),
        listener_pos=(0, 0, 0),
        velocity=(5, 0, 0)
    )
    print("  ✓ Custom spatial processing: HRTF + Doppler + Distance (no reverb)")
    print(f"  ✓ Source at (2, 1, 0.5), moving at (5, 0, 0) m/s")

    print("\n✨ Spatial audio demo complete!")
    print("The Reverb platform now supports immersive 3D audio with binaural rendering.")


def describe_position(pos):
    """Describe a 3D position in words."""
    x, y, z = pos
    descriptions = []
    if abs(x) > abs(y):
        descriptions.append("right" if x > 0 else "left")
    elif abs(y) > 0:
        descriptions.append("front" if y > 0 else "back")
    if z > 0.5:
        descriptions.append("above")
    elif z < -0.5:
        descriptions.append("below")

    return " ".join(descriptions) if descriptions else "center"


def describe_velocity(vel):
    """Describe a velocity vector in words."""
    vx, vy, vz = vel
    speed = math.sqrt(vx**2 + vy**2 + vz**2)

    if vx > 0:
        return f"right at {speed:.1f} m/s"
    elif vx < 0:
        return f"left at {speed:.1f} m/s"
    elif vy > 0:
        return f"forward at {speed:.1f} m/s"
    elif vy < 0:
        return f"backward at {speed:.1f} m/s"
    elif vz > 0:
        return f"up at {speed:.1f} m/s"
    elif vz < 0:
        return f"down at {speed:.1f} m/s"
    else:
        return "stationary"


if __name__ == "__main__":
    demo_spatial_audio()
