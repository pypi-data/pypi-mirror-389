# ------------------------------------------------------------------
# Core Reverb representation (audio-inspired)
# ------------------------------------------------------------------
class Reverb:
    """
    Logical representation of an audio-style reverb effect.

    Parameters
    ----------
    rt60 : float
        Reverberation time (RT60) in seconds, the time for sound to decay by 60 dB.
        Typical values: 0.5-3.0s for small to large rooms.
    pre_delay : float
        Time delay before reverb onset in seconds, simulating direct sound path.
        Typical values: 0-0.1s.
    damping : float
        Frequency-dependent absorption (0-1), higher values damp highs more.
        0 = no damping, 1 = full damping.
    mix : float
        Overall blend of dry vs. wet signal (0 = all dry, 1 = all wet).
    """
    def __init__(self, rt60: float = 1.0, pre_delay: float = 0.05,
                 damping: float = 0.5, mix: float = 0.5):
        self.rt60 = max(0, rt60)
        self.pre_delay = max(0, pre_delay)
        self.damping = min(max(damping, 0.0), 1.0)
        self.mix = min(max(mix, 0.0), 1.0)

    def __repr__(self) -> str:
        return (f"Reverb(rt60={self.rt60:.2f}s, pre_delay={self.pre_delay:.3f}s, "
                f"damping={self.damping:.2f}, mix={self.mix:.2f})")


# ------------------------------------------------------------------
# Helper that interprets the numeric parameters into plain English
# ------------------------------------------------------------------
def describe_reverb(r: Reverb) -> str:
    """Return a concise, human-readable description of a Reverb instance."""
    rt60_desc = (
        "short" if r.rt60 < 0.8 else
        "medium" if r.rt60 < 2.0 else
        "long"
    )
    pre_delay_desc = (
        "minimal" if r.pre_delay < 0.02 else
        "moderate" if r.pre_delay < 0.08 else
        "extended"
    )
    damping_desc = (
        "bright" if r.damping < 0.3 else
        "balanced" if r.damping < 0.7 else
        "muffled"
    )
    mix_desc = (
        "dry-only" if r.mix == 0 else
        "wet-only" if r.mix == 1 else
        "balanced"
    )

    return (
        f"The reverb has a {rt60_desc} decay ({r.rt60:.1f}s), {pre_delay_desc} pre-delay "
        f"({r.pre_delay:.3f}s), a {damping_desc} tone, and a {mix_desc} dry/wet mix."
    )


# ------------------------------------------------------------------
# Example usage – create a reverb, describe it, and print the result
# ------------------------------------------------------------------
if __name__ == "__main__":
    # Example: a medium decay reverb with balanced settings
    my_reverb = Reverb(rt60=1.5, pre_delay=0.03, damping=0.4, mix=0.6)

    print(my_reverb)  # technical representation
    print(describe_reverb(my_reverb))  # human-readable interpretation
