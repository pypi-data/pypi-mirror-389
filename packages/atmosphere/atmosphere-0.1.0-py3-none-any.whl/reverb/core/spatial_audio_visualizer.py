"""
Spatial Audio Visualizer

Demonstrates spatial audio processing concepts including:
- Doppler effect
- Distance attenuation
- HRTF binaural processing
- Frequency domain analysis
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import matplotlib.pyplot as plt
from scipy import signal
import warnings
warnings.filterwarnings('ignore')

class SpatialAudioVisualizer:
    def __init__(self):
        self.sample_rate = 44100
        self.sound_speed = 343  # m/s

    def generate_signal(self, frequency=440, duration=1.0):
        """Generate a mono audio signal"""
        t = np.linspace(0, duration, int(duration * self.sample_rate))
        return np.sin(2 * np.pi * frequency * t), t

    def apply_doppler(self, signal, velocity, t):
        """Apply Doppler effect"""
        # Doppler factor: f' = f * (c ± v_listener) / (c ∓ v_source)
        # Simplified: assume listener stationary
        doppler_factor = (self.sound_speed + velocity) / self.sound_speed
        shifted_freq = 440 * doppler_factor

        # Generate new signal with Doppler shift
        doppler_signal = np.sin(2 * np.pi * shifted_freq * t)

        return doppler_signal, doppler_factor

    def apply_distance_attenuation(self, signal, distance):
        """Apply inverse square law attenuation"""
        if distance <= 0:
            return signal
        attenuation_factor = 1.0 / (distance ** 2)
        return signal * attenuation_factor

    def apply_hrtf(self, signal, azimuth_deg):
        """Simplified HRTF processing"""
        azimuth_rad = np.radians(azimuth_deg)

        # ITD (Interaural Time Difference)
        head_radius = 0.0875  # meters
        itd_delay = (head_radius / self.sound_speed) * np.sin(azimuth_rad)
        delay_samples = int(itd_delay * self.sample_rate)

        # ILD (Interaural Level Difference)
        ild_db = 3 * np.sin(azimuth_rad)  # Max 3dB difference
        ild_factor_left = 10 ** (ild_db / 20) if ild_db < 0 else 1.0
        ild_factor_right = 10 ** (-ild_db / 20) if ild_db > 0 else 1.0

        # Apply ILD
        left_ear = signal * ild_factor_left
        right_ear = signal * ild_factor_right

        # Apply ITD delay
        if delay_samples > 0:
            right_ear = np.roll(right_ear, delay_samples)
        elif delay_samples < 0:
            left_ear = np.roll(left_ear, -delay_samples)

        return left_ear, right_ear

    def create_comprehensive_visualization(self):
        """Create a comprehensive visualization of all spatial audio effects"""
        print("🎵 Creating Spatial Audio Visualization...")
        print("=" * 50)

        # Create figure with subplots
        fig, axes = plt.subplots(2, 3, figsize=(16, 10))
        fig.suptitle('Spatial Audio Processing Pipeline', fontsize=16, fontweight='bold')

        # Generate base signal
        audio_signal, t = self.generate_signal(frequency=440, duration=0.5)

        # 1. Original signal
        axes[0, 0].plot(t, audio_signal, 'b-', linewidth=2)
        axes[0, 0].set_title('1. Original Mono Signal\n440 Hz Sine Wave', fontweight='bold')
        axes[0, 0].set_xlabel('Time (s)')
        axes[0, 0].set_ylabel('Amplitude')
        axes[0, 0].grid(True, alpha=0.3)

        # 2. Doppler effect
        doppler_signal, doppler_factor = self.apply_doppler(audio_signal, velocity=20, t=t)
        axes[0, 1].plot(t, audio_signal, 'b--', alpha=0.7, label='Original')
        axes[0, 1].plot(t, doppler_signal, 'r-', linewidth=2, label='Doppler shifted')
        axes[0, 1].set_title(f'2. Doppler Effect\nVelocity: 20 m/s, Factor: {doppler_factor:.3f}', fontweight='bold')
        axes[0, 1].set_xlabel('Time (s)')
        axes[0, 1].set_ylabel('Amplitude')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)

        # 3. Distance attenuation
        distances = [1, 2, 5, 10]
        colors = ['blue', 'green', 'orange', 'red']
        for dist, color in zip(distances, colors):
            attenuated = self.apply_distance_attenuation(audio_signal, dist)
            axes[0, 2].plot(t, attenuated, color=color, linewidth=2,
                          label=f'{dist}m ({-20*np.log10(dist):.1f}dB)')

        axes[0, 2].set_title('3. Distance Attenuation\nInverse Square Law', fontweight='bold')
        axes[0, 2].set_xlabel('Time (s)')
        axes[0, 2].set_ylabel('Amplitude')
        axes[0, 2].legend()
        axes[0, 2].grid(True, alpha=0.3)

        # 4. HRTF binaural processing
        azimuths = [0, 45, 90]
        colors = ['red', 'orange', 'purple']

        for azimuth, color in zip(azimuths, colors):
            left_ear, right_ear = self.apply_hrtf(audio_signal, azimuth)

            # Plot left ear (solid)
            axes[1, 0].plot(t, left_ear, color=color, linewidth=2, linestyle='-',
                          label=f'{azimuth}° Left')
            # Plot right ear (dashed)
            axes[1, 0].plot(t, right_ear, color=color, linewidth=2, linestyle='--',
                          label=f'{azimuth}° Right')

        axes[1, 0].set_title('4. HRTF Binaural Output\nLeft/Right Ear Signals', fontweight='bold')
        axes[1, 0].set_xlabel('Time (s)')
        axes[1, 0].set_ylabel('Amplitude')
        axes[1, 0].legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        axes[1, 0].grid(True, alpha=0.3)

        # 5. Frequency domain analysis
        freqs, psd_original = signal.welch(audio_signal, self.sample_rate, nperseg=1024)
        _, psd_doppler = signal.welch(doppler_signal, self.sample_rate, nperseg=1024)

        # Focus on relevant frequency range
        mask = (freqs >= 200) & (freqs <= 800)
        axes[1, 1].plot(freqs[mask], 10 * np.log10(psd_original[mask]), 'b-', linewidth=2, label='Original')
        axes[1, 1].plot(freqs[mask], 10 * np.log10(psd_doppler[mask]), 'r-', linewidth=2, label='Doppler')
        axes[1, 1].axvline(x=440, color='blue', linestyle='--', alpha=0.7)
        axes[1, 1].axvline(x=440 * doppler_factor, color='red', linestyle='--', alpha=0.7)
        axes[1, 1].set_title('5. Frequency Domain\nDoppler Frequency Shift', fontweight='bold')
        axes[1, 1].set_xlabel('Frequency (Hz)')
        axes[1, 1].set_ylabel('Power (dB)')
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3)

        # 6. Spatial characteristics
        azimuth_range = np.linspace(-90, 90, 100)
        itd_curve = (0.0875 / self.sound_speed) * np.sin(np.radians(azimuth_range)) * 1000  # ms
        ild_curve = 3 * np.sin(np.radians(azimuth_range))  # dB

        axes[1, 2].plot(azimuth_range, itd_curve, 'purple', linewidth=2, label='ITD (ms)')
        axes[1, 2].set_xlabel('Azimuth Angle (degrees)')
        axes[1, 2].set_ylabel('ITD (ms)', color='purple')
        axes[1, 2].tick_params(axis='y', labelcolor='purple')
        axes[1, 2].grid(True, alpha=0.3)

        ax2 = axes[1, 2].twinx()
        ax2.plot(azimuth_range, ild_curve, 'orange', linewidth=2, label='ILD (dB)')
        ax2.set_ylabel('ILD (dB)', color='orange')
        ax2.tick_params(axis='y', labelcolor='orange')

        axes[1, 2].set_title('6. Spatial Cues\nITD & ILD vs Azimuth', fontweight='bold')

        # Add physics summary
        physics_summary = ".1f"".1f"".1f"".1f"f"""
        Spatial Audio Physics Summary:
        • Doppler Shift: {doppler_factor:.3f}x ({((doppler_factor-1)*100):+.1f}%)
        • Max ITD: ±{max(abs(itd_curve)):.2f} ms
        • Max ILD: ±{max(abs(ild_curve)):.1f} dB
        • Sound Speed: {self.sound_speed} m/s
        • Head Radius: 8.75 cm
        """

        plt.figtext(0.02, 0.02, physics_summary, fontsize=10, fontfamily='monospace',
                   bbox=dict(boxstyle="round,pad=0.5", facecolor="lightblue", alpha=0.8))

        plt.tight_layout()
        plt.savefig('spatial_audio_visualization.png', dpi=300, bbox_inches='tight')
        print("✅ Visualization saved as 'spatial_audio_visualization.png'")
        plt.close()

        print("\n📊 Demonstrated Spatial Audio Effects:")
        print("1. ✓ Original mono signal generation")
        print("2. ✓ Doppler effect with frequency shifting")
        print("3. ✓ Distance attenuation (inverse square law)")
        print("4. ✓ HRTF binaural processing (ITD/ILD)")
        print("5. ✓ Frequency domain analysis")
        print("6. ✓ Spatial positioning characteristics")

    def demonstrate_doppler(self):
        """Doppler effect demonstration"""
        print("\n🚀 Doppler Effect Analysis")
        print("-" * 30)

        velocities = [0, 5, 10, 25, 50]  # m/s
        signal, _ = self.generate_signal(duration=0.1)

        print("Velocity (m/s) | Doppler Factor | Frequency Shift (%)")
        print("-" * 55)

        for velocity in velocities:
            doppler_signal, factor = self.apply_doppler(signal, velocity, np.linspace(0, 0.1, len(signal)))
            freq_shift_percent = (factor - 1) * 100
            print("8.1f")

    def demonstrate_distance(self):
        """Distance attenuation demonstration"""
        print("\n📏 Distance Attenuation Analysis")
        print("-" * 35)

        distances = [0.5, 1, 2, 5, 10, 20]  # meters
        signal, _ = self.generate_signal(duration=0.1)
        original_rms = np.sqrt(np.mean(signal**2))

        print("Distance (m) | Attenuation (dB) | RMS Ratio")
        print("-" * 45)

        for distance in distances:
            attenuated = self.apply_distance_attenuation(signal, distance)
            rms = np.sqrt(np.mean(attenuated**2))
            attenuation_db = 20 * np.log10(rms / original_rms)
            print("8.1f")

    def demonstrate_hrtf(self):
        """HRTF directional analysis"""
        print("\n🎧 HRTF Directional Analysis")
        print("-" * 30)

        azimuths = [0, 30, 60, 90]  # degrees
        signal, _ = self.generate_signal(duration=0.1)

        print("Azimuth (°) | ITD (ms) | ILD (dB) | L/R Balance (dB)")
        print("-" * 60)

        for azimuth in azimuths:
            left, right = self.apply_hrtf(signal, azimuth)

            # Calculate ITD
            itd = (0.0875 / self.sound_speed) * np.sin(np.radians(azimuth)) * 1000

            # Calculate ILD
            ild = 3 * np.sin(np.radians(azimuth))

            # Calculate L/R balance
            rms_left = np.sqrt(np.mean(left**2))
            rms_right = np.sqrt(np.mean(right**2))
            balance = 20 * np.log10(rms_right / (rms_left + 1e-10))

            print("8.1f")

def main():
    """Main function"""
    print("🎯 Spatial Audio Visualizer")
    print("=" * 40)
    print("Demonstrating the physics and perception of sound in space")

    try:
        visualizer = SpatialAudioVisualizer()

        # Create comprehensive visualization
        visualizer.create_comprehensive_visualization()

        # Run demonstrations
        visualizer.demonstrate_doppler()
        visualizer.demonstrate_distance()
        visualizer.demonstrate_hrtf()

        print("\n🎉 All spatial audio demonstrations completed!")
        print("Check 'spatial_audio_visualization.png' for the comprehensive visualization.")

    except ImportError as e:
        print(f"❌ Missing required packages: {e}")
        print("Install with: pip install numpy matplotlib scipy")
    except Exception as e:
        print(f"❌ Error running visualizer: {e}")

if __name__ == "__main__":
    main()
