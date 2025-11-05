# tests/test_animate.py
import itertools
from minecraft_textcraft.animate import animate_typewriter, animate_scroll, animate_wave
from minecraft_textcraft.colorize_ascii import Color

ASCII = "AB\nCD"

def take(n, it):
    return list(itertools.islice(it, n))

def test_typewriter_progresses_and_finishes():
    frames = list(animate_typewriter(ASCII, color=Color.GREEN, cps=24))
    assert len(frames) >= 2
    assert frames[0]  
    assert frames[-1].count("\n") in (1, 2, 3)  
    assert "A" in frames[-1] and "D" in frames[-1]

def test_scroll_changes_over_time():
    frames = take(6, animate_scroll(ASCII, cols_per_frame=2, loops=1))
    assert len(frames) >= 1  # Should generate at least some frames
    # Check that scroll animation produces different frames (at least blank and content)
    unique_frames = set(frames)
    assert len(unique_frames) > 1, f"Scroll should produce different frames, got: {unique_frames}"

def test_wave_produces_fixed_frames():
    frames = list(animate_wave(ASCII, amplitude=1, period_cols=4, frames=8))
    assert len(frames) == 8
    assert len(set(frames)) > 1
