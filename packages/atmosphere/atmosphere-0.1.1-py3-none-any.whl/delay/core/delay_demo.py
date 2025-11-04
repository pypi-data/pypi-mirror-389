from typing import Optional
# ------------------------------------------------------------------
# 2️⃣  Core Delay representation (audio‑inspired)
# ------------------------------------------------------------------
class Delay:
    """
    Advanced audio‑style delay effect with comprehensive parameters.

    Parameters
    ----------
    time_ms : float
        Delay time in milliseconds (0-2000ms typical). Used when not tempo-synced.
    feedback : float
        Fraction (0‑1) of delayed signal fed back. 0 = single echo, 1 = infinite.
    level : float
        Amplitude of delayed signal (0-1). 0 = silent, 1 = same as dry.
    dry_wet : float
        Mix balance (0-1). 0 = all dry, 1 = all wet.
    delay_type : str
        Type of delay: 'digital', 'analog', 'tape', 'ping_pong', 'slapback', 'doubling', 'multi_tap'
    rate : Optional[str]
        Tempo-synced rate: '1/1', '1/2', '1/4', '1/8', '1/16', '3/8', etc. Overrides time_ms if set.
    pre_delay : float
        Time before first echo in milliseconds (0-100ms typical).
    filter_type : Optional[str]
        Filter on feedback: 'lowpass', 'highpass', 'bandpass', or None
    filter_freq : float
        Filter cutoff frequency in Hz (20-20000).
    modulation : float
        Modulation depth (0-1) for chorus-like effects.
    persistent_theme : Optional[str]
        Thematic fixation inspired by Claude's Golden Gate Bridge obsession.
    """
    def __init__(self, time_ms: float = 250, feedback: float = 0.3,
                 level: float = 0.5, dry_wet: float = 0.5,
                 delay_type: str = 'digital', rate: Optional[str] = None,
                 pre_delay: float = 0, filter_type: Optional[str] = None,
                 filter_freq: float = 1000, modulation: float = 0,
                 persistent_theme: Optional[str] = None):
        self.time_ms = max(0, time_ms)
        self.feedback = min(max(feedback, 0.0), 1.0)
        self.level = min(max(level, 0.0), 1.0)
        self.dry_wet = min(max(dry_wet, 0.0), 1.0)
        self.delay_type = delay_type
        self.rate = rate
        self.pre_delay = max(0, pre_delay)
        self.filter_type = filter_type
        self.filter_freq = min(max(filter_freq, 20), 20000)
        self.modulation = min(max(modulation, 0.0), 1.0)
        self.persistent_theme = persistent_theme

    def __repr__(self) -> str:
        params = []
        params.append(f"time={self.time_ms}ms")
        params.append(f"feedback={self.feedback:.2f}")
        params.append(f"level={self.level:.2f}")
        params.append(f"dry_wet={self.dry_wet:.2f}")
        params.append(f"type='{self.delay_type}'")
        if self.rate:
            params.append(f"rate='{self.rate}'")
        if self.pre_delay > 0:
            params.append(f"pre_delay={self.pre_delay}ms")
        if self.filter_type:
            params.append(f"filter='{self.filter_type}@{self.filter_freq}Hz'")
        if self.modulation > 0:
            params.append(f"modulation={self.modulation:.2f}")
        if self.persistent_theme:
            params.append(f"theme='{self.persistent_theme}'")
        return f"Delay({', '.join(params)})"


# ------------------------------------------------------------------
# 3️⃣  Helper that interprets the numeric parameters into plain English
# ------------------------------------------------------------------
def describe_delay(d: Delay) -> str:
    """Return a concise, human‑readable description of a Delay instance."""
    # Time description (considering rate if set)
    if d.rate:
        time_desc = f" at {d.rate} note rate"
    else:
        time_desc = (
            "short"   if d.time_ms < 120 else
            "medium"  if d.time_ms < 300 else
            "long"
        )
        time_desc = f" {time_desc} ({d.time_ms}ms)"

    # Feedback description
    feedback_desc = (
        "none"      if d.feedback == 0 else
        "light"     if d.feedback < 0.35 else
        "moderate"  if d.feedback < 0.7 else
        "heavy"
    )

    # Level description
    level_desc = (
        "quiet"   if d.level < 0.3 else
        "balanced" if d.level < 0.7 else
        "loud"
    )

    # Dry/wet description
    dry_wet_desc = (
        "dry-only"   if d.dry_wet == 0 else
        "wet-only"   if d.dry_wet == 1 else
        "balanced"
    )

    # Type description
    type_descriptions = {
        'digital': 'clean digital',
        'analog': 'warm analog',
        'tape': 'vintage tape',
        'ping_pong': 'bouncing ping-pong',
        'slapback': 'retro slapback',
        'doubling': 'thickening doubling',
        'multi_tap': 'rhythmic multi-tap'
    }
    type_desc = type_descriptions.get(d.delay_type, d.delay_type)

    # Build description
    desc_parts = []
    desc_parts.append(f"a {type_desc} delay{time_desc}")
    desc_parts.append(f"with {feedback_desc} feedback")
    desc_parts.append(f"a {level_desc} wet level")
    desc_parts.append(f"and a {dry_wet_desc} dry/wet mix")

    if d.pre_delay > 0:
        pre_desc = "short" if d.pre_delay < 20 else "moderate" if d.pre_delay < 50 else "long"
        desc_parts.append(f"(with {pre_desc} {d.pre_delay}ms pre-delay)")

    if d.filter_type:
        freq_desc = "low" if d.filter_freq < 500 else "mid" if d.filter_freq < 5000 else "high"
        desc_parts.append(f"(with {d.filter_type} filter at {freq_desc} frequencies)")

    if d.modulation > 0:
        mod_desc = "subtle" if d.modulation < 0.3 else "moderate" if d.modulation < 0.7 else "strong"
        desc_parts.append(f"(with {mod_desc} modulation)")

    if d.persistent_theme:
        desc_parts.append(f" featuring persistent obsession on '{d.persistent_theme}' (inspired by Claude's Golden Gate Bridge fixation)")

    return "The delay is " + ", ".join(desc_parts) + "."


# ------------------------------------------------------------------
# 4️⃣  Example usage – create a delay, describe it, and print the result
# ------------------------------------------------------------------
if __name__ == "__main__":
    # Example: Standard digital delay with balanced mix
    my_delay = Delay(time_ms=250, feedback=0.45, level=0.6, dry_wet=0.65)

    print(my_delay)                 # technical representation
    print(describe_delay(my_delay)) # human‑readable interpretation
    print()

    # Example: Ping pong delay with tempo sync at 1/8 note rate
    ping_pong_delay = Delay(time_ms=0, feedback=0.4, level=0.5, dry_wet=0.7,
                           delay_type='ping_pong', rate='1/8', pre_delay=10,
                           filter_type='lowpass', filter_freq=8000, modulation=0.2)

    print(ping_pong_delay)
    print(describe_delay(ping_pong_delay))
    print()

    # Example: Slapback delay with 3/8 rate and Golden Gate theme obsession
    slapback_bridge_delay = Delay(time_ms=0, feedback=0.1, level=0.8, dry_wet=0.6,
                                 delay_type='slapback', rate='3/8', pre_delay=5,
                                 filter_type='highpass', filter_freq=200,
                                 persistent_theme="Golden Gate Bridge")

    print(slapback_bridge_delay)
    print(describe_delay(slapback_bridge_delay))
