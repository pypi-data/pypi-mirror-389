"""
Reverb Main Application

Demonstrates the Reverb audio effects platform.
"""

import math
from core.platform import ReverbPlatform
from models.signal import AudioSignal


def create_test_signal(frequency: float = 440.0, duration: float = 1.0, sample_rate: int = 44100) -> AudioSignal:
    """Create a test sine wave signal."""
    num_samples = int(duration * sample_rate)
    data = []
    for i in range(num_samples):
        t = i / sample_rate
        sample = math.sin(2 * math.pi * frequency * t)
        data.append(sample)

    return AudioSignal.create_mono(data=data, sample_rate=sample_rate)


def main():
    """Main application entry point."""
    print("🎵 Reverb Audio Effects Platform")
    print("=" * 40)

    # Create platform
    platform = ReverbPlatform()
    print("✓ Platform initialized with effects chain: Input -> Delay -> Echo -> Reverb -> Spatial -> Output")

    # Get status
    status = platform.get_system_status()
    print(f"✓ System status: {status['status']}")
    print(f"✓ Services: {list(status['services'].keys())}")
    print(f"✓ Available presets: {status['presets']}")

    # Create test signal
    print("\n🎼 Creating test signal...")
    signal = create_test_signal(frequency=440.0, duration=0.5)
    print(f"✓ Generated mono signal with {len(signal.data[0])} samples at {signal.sample_rate}Hz")
    print(f"✓ Duration: {signal.duration:.2f}s")

    # Process through effects chain
    print("\n⚡ Processing through effects chain...")
    processed = platform.process_signal(signal)
    print(f"✓ Processed signal is now stereo with {len(processed.data[0])} samples per channel")
    print(f"✓ Channels: {processed.channels}")

    # Show some sample values
    print("\n📊 Sample comparison:")
    print(".2f")
    print(".2f")
    print(".2f")
    print(".2f")

    # Demonstrate presets
    print("\n🏛️  Demonstrating reverb presets...")
    for preset in status['presets']:
        print(f"\n  Applying '{preset}' preset...")
        preset_processed = platform.process_with_preset(signal, preset)
        print(f"  ✓ {preset.capitalize()} processed signal ready")

    print("\n✨ Processing complete!")
    print("The Reverb platform successfully simulated acoustic depth and dimension with algorithmic reverb and presets.")


if __name__ == "__main__":
    main()
