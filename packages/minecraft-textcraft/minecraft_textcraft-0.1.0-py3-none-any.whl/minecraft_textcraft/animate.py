# src/minecraft_textcraft/animate.py
from typing import Generator, Iterable, Optional
from .colorize_ascii import colorize_ascii, Color

def _normalize(ascii_art: str) -> list[str]:
    lines = ascii_art.splitlines()
    if not lines:
        return []
    width = max(len(ln) for ln in lines)
    return [ln.ljust(width) for ln in lines]

def animate_typewriter(
    ascii_art: str,
    color: Optional[Color] = None,
    cps: int = 10,  # characters per second
) -> Generator[str, None, None]:
    lines = _normalize(ascii_art)
    if not lines:
        yield ""
        return
    width = len(lines[0])
    # Calculate step based on fps (default 12 fps)
    # Ensure step is at least 1 to avoid skipping
    fps = 12
    step = max(1, int(round(cps / fps)))
    shown = 0
    # Yield empty frame first for smooth start
    yield colorize_ascii("", color) if color else ""
    # Gradually reveal columns
    while shown < width:
        shown += step
        if shown > width:
            shown = width
        frame = "\n".join(ln[:shown] for ln in lines)
        yield colorize_ascii(frame, color) if color else frame
    # Ensure final frame is complete
    full = "\n".join(lines)
    yield colorize_ascii(full, color) if color else full

def animate_scroll(
    ascii_art: str,
    color: Optional[Color] = None,
    cols_per_frame: int = 1,
    loops: int = 1,
) -> Generator[str, None, None]:
    lines = _normalize(ascii_art)
    if not lines:
        yield ""
        return
    cols_per_frame = max(1, int(cols_per_frame))
    width = len(lines[0])
    # Add padding on the left side so content scrolls in from the right
    # Content is on the right, window starts at left (showing blank), moves right
    # Padding should be proportional to content width, but not too small
    padding_size = max(width, 10)  # At least same as width or 10 columns for smooth scroll
    left_pad = " " * padding_size
    padded = [left_pad + ln for ln in lines]  # Add padding on the left, content on the right
    total_w = len(padded[0])  # Total width = padding + width

    def colorize_if_needed(s: str) -> str:
        return colorize_ascii(s, color) if color else s

    def one_loop() -> Generator[str, None, None]:
        # Scroll from left to right: window starts at left (showing blank), moves right
        # Content scrolls in from the right side
        step = max(1, cols_per_frame)
        
        # Window starts at leftmost position (start=0, showing only padding/blank)
        # Window moves right (start increases) until full content is visible
        min_start = 0  # Leftmost position (showing blank)
        max_start = total_w - width  # Rightmost position (showing full content)
        
        # Generate frames from left to right (start increases)
        # Content scrolls in from the right
        for start in range(min_start, max_start + 1, step):
            # Extract a window of 'width' columns starting from 'start'
            frame_cols = [row[start:start + width] for row in padded]
            yield colorize_if_needed("\n".join(frame_cols))
        
        # Ensure final frame shows the complete content
        if (max_start - min_start) % step != 0:
            final_frame = [row[max_start:max_start + width] for row in padded]
            yield colorize_if_needed("\n".join(final_frame))

    loops = max(1, int(loops))
    for _ in range(loops):
        yield from one_loop()
    

def animate_wave(
    ascii_art: str,
    color: Optional[Color] = None,
    amplitude: int = 2,
    period_cols: int = 10,
    frames: int = 24,
) -> Generator[str, None, None]:
  
    import math
    base = _normalize(ascii_art)
    if not base:
        yield ""
        return
    h = len(base)
    w = len(base[0])
    pad = amplitude + 1
    for t in range(max(1, frames)):
        canvas_h = h + 2 * pad
        canvas = [[" "] * w for _ in range(canvas_h)]
        for r in range(h):
            for c, ch in enumerate(base[r]):
                phase = 2 * math.pi * (c / max(1, period_cols)) + 2 * math.pi * (t / max(1, frames))
                offset = int(round(amplitude * math.sin(phase)))
                rr = r + pad + offset
                if 0 <= rr < canvas_h:
                    canvas[rr][c] = ch
        frame = "\n".join("".join(row) for row in canvas)
        yield colorize_ascii(frame, color) if color else frame

def play_animation(frames: Iterable[str], fps: int = 12) -> None:
    import time
    
    if fps <= 0:
        fps = 12
    delay = 1.0 / fps
    
    # Use cursor movement instead of full screen clear for smoother animation
    def move_cursor_home():
        """Move cursor to top-left and clear from cursor to end of screen"""
        print("\033[H\033[J", end="", flush=True)
    
    # Clear screen at start
    move_cursor_home()
    
    for f in frames:
        # Move cursor to home position and clear from there
        move_cursor_home()
        print(f, end="", flush=True)
        time.sleep(delay)
