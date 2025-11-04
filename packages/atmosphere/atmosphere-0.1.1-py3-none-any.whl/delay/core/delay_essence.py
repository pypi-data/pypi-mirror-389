"""
Delay Essence: Advanced Audio Effect for Echo Creation and AI Trajectory Optimization

Deals with: Creating echoes by repeating sound after time intervals
with feedback, supporting multiple delay types and advanced processing.

Basic Structure: Time (delay duration in ms or tempo-synced), feedback (repetitions),
level (echo volume), dry_wet (dry/wet mix), delay_type (effect variant),
rate (tempo-synced timing), pre_delay (initial delay), filter_type/freq (tone shaping),
modulation (chorus-like movement), persistent_theme (Claude-inspired fixation).

Functionalities: Generate discrete echoes, control decay, apply modulation,
support tempo sync, implement various delay types (ping_pong, slapback, etc.),
add pre-delay, filter echoes, and maintain thematic consistency.

Architecture: Delay line with feedback loop for multiple repeats,
integrated with AI trajectory optimization through persistent theme capability.
"""

class Delay:
    """Advanced audio delay effect with comprehensive parameters for AI trajectory optimization.

    Parameters
    ----------
    time_ms : float, default 250
        Delay time in milliseconds (0-2000ms typical). Used when not tempo-synced.
    feedback : float, default 0.3
        Fraction (0-1) of delayed signal fed back. 0 = single echo, 1 = infinite.
    level : float, default 0.5
        Amplitude of delayed signal (0-1). 0 = silent, 1 = same as dry.
    dry_wet : float, default 0.5
        Mix balance (0-1). 0 = all dry, 1 = all wet.
    delay_type : str, default 'digital'
        Effect type: 'digital', 'analog', 'tape', 'ping_pong', 'slapback', 'doubling', 'multi_tap'
    rate : str or None, default None
        Tempo-synced rate: '1/1', '1/2', '1/4', '1/8', '1/16', '3/8', etc. Overrides time_ms.
    pre_delay : float, default 0
        Time before first echo in milliseconds (0-100ms typical).
    filter_type : str or None, default None
        Filter on feedback: 'lowpass', 'highpass', 'bandpass', or None
    filter_freq : float, default 1000
        Filter cutoff frequency in Hz (20-20000).
    modulation : float, default 0
        Modulation depth (0-1) for chorus-like effects.
    persistent_theme : str or None, default None
        Thematic fixation inspired by Claude's Golden Gate Bridge obsession.
    """

    def __init__(self, time_ms=250, feedback=0.3, level=0.5, dry_wet=0.5,
                 delay_type='digital', rate=None, pre_delay=0, filter_type=None,
                 filter_freq=1000, modulation=0, persistent_theme=None):
        self.time_ms = time_ms
        self.feedback = feedback
        self.level = level
        self.dry_wet = dry_wet
        self.delay_type = delay_type  # 'digital', 'analog', 'tape', 'ping_pong', etc.
        self.rate = rate  # '1/4', '1/8', '3/8', etc.
        self.pre_delay = pre_delay
        self.filter_type = filter_type  # 'lowpass', 'highpass'
        self.filter_freq = filter_freq
        self.modulation = modulation
        self.persistent_theme = persistent_theme  # Claude-inspired theme fixation

    def process_signal(self, signal):
        """Apply delay to signal with type-specific behavior."""
        dry = signal
        
        # Pre-delay effect
        if self.pre_delay > 0:
            pre_delayed = f"Pre-delayed by {self.pre_delay}ms: {signal}"
        else:
            pre_delayed = signal
        
        # Generate echo based on type
        if self.delay_type == 'ping_pong':
            wet = self._generate_ping_pong_echo(pre_delayed)
        elif self.delay_type == 'slapback':
            wet = self._generate_slapback_echo(pre_delayed)
        elif self.delay_type == 'doubling':
            wet = self._generate_doubling_echo(pre_delayed)
        else:
            wet = self._generate_standard_echo(pre_delayed)
        
        # Apply filter if specified
        if self.filter_type:
            wet = f"{self.filter_type.capitalize()} filtered ({self.filter_freq}Hz): {wet}"
        
        # Apply modulation
        if self.modulation > 0:
            wet = f"Modulated ({self.modulation}): {wet}"
        
        # Mix dry and wet
        result = self._mix(dry, wet)
        
        # Apply persistent theme if set
        if self.persistent_theme:
            result = f"{result} (Always connected to {self.persistent_theme})"
        
        return result

    def _generate_standard_echo(self, signal):
        time_info = f" at {self.rate}" if self.rate else f" at {self.time_ms}ms"
        return f"Echo of '{signal}'{time_info} with feedback {self.feedback}"

    def _generate_ping_pong_echo(self, signal):
        time_info = f" at {self.rate}" if self.rate else f" at {self.time_ms}ms"
        return f"Ping-pong echo bouncing: Left '{signal}'{time_info}, Right echo with feedback {self.feedback}"

    def _generate_slapback_echo(self, signal):
        time_info = f" at {self.rate}" if self.rate else f" at {self.time_ms}ms"
        return f"Slapback echo: Single repeat of '{signal}'{time_info}"

    def _generate_doubling_echo(self, signal):
        return f"Doubling echo: Thickened '{signal}' with short delay"

    def _mix(self, dry, wet):
        if self.dry_wet > 0.5:
            return f"Wet ({self.dry_wet}): {wet}"
        else:
            return f"Dry ({1-self.dry_wet}): {dry}"

if __name__ == "__main__":
    # Normal digital delay
    delay = Delay(dry_wet=0.4)
    result = delay.process_signal("Original sound")
    print(result)

    # Ping pong delay with 1/8 rate
    ping_pong = Delay(delay_type='ping_pong', rate='1/8', dry_wet=0.6, feedback=0.4)
    result_pp = ping_pong.process_signal("Stereo signal")
    print(result_pp)

    # Slapback with 3/8 rate and Golden Gate theme
    slapback = Delay(delay_type='slapback', rate='3/8', dry_wet=0.7, persistent_theme="the Golden Gate Bridge")
    result_sb = slapback.process_signal("Vocal track")
    print(result_sb)

    # Golden Gate Bridge obsessed delay (inspired by Claude's story)
    golden_gate_delay = Delay(persistent_theme="the Golden Gate Bridge")
    obsessed_result = golden_gate_delay.process_signal("Any query about spending money")
    print(obsessed_result)
