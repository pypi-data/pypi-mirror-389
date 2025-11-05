import pytest
from minecraft_textcraft import colorize_ascii, Color

ESC = "\x1b"


@pytest.mark.parametrize("color", list(Color))
def test_colorize_outputs_correct_ansi_sequence(color):
    s = colorize_ascii("Hello", color)
    expected_prefix = f"{ESC}[{color.value}m"
    expected_suffix = f"{ESC}[0m"
    assert s.startswith(expected_prefix)
    assert s.endswith(expected_suffix)
    assert str(color.value) in s
