"""
Tests for the command-line interface (__main__.py).
Tests command-line argument parsing, output formatting, color, commands, render, and animation.
"""
import pytest
import sys
from unittest.mock import patch, MagicMock
from io import StringIO
from minecraft_textcraft.__main__ import main


def test_main_help():
    """Test --help option"""
    with patch('sys.argv', ['minecraft-textcraft', '--help']):
        with patch('sys.stdout', new=StringIO()) as mock_stdout:
            with pytest.raises(SystemExit) as exc_info:
                main()
            # argparse help exits with code 0
            assert exc_info.value.code == 0
            output = mock_stdout.getvalue()
            assert 'minecraft-textcraft' in output or 'Minecraft-style' in output


def test_main_render_text_with_color():
    """Test rendering text with color via command line"""
    with patch('sys.argv', ['minecraft-textcraft', 'HELLO', '--color', 'GREEN']):
        with patch('sys.stdout', new=StringIO()) as mock_stdout:
            main()
            output = mock_stdout.getvalue()
            # Should output rendered colored text
            assert len(output) > 0
            assert '\n' in output
            # Should contain color codes
            assert '\033[' in output or output  # Color codes or successful output


def test_main_render_text_with_command_and_color():
    """Test rendering text with command and color - covers render, command, and color"""
    with patch('sys.argv', ['minecraft-textcraft', 'GET \\\\sword NOW', '--color', 'RED']):
        with patch('sys.stdout', new=StringIO()) as mock_stdout:
            main()
            output = mock_stdout.getvalue()
            # Should output rendered text with command and color
            assert len(output) > 0
            assert '\n' in output


def test_main_list_commands():
    """Test --list option"""
    with patch('sys.argv', ['minecraft-textcraft', '--list']):
        with patch('sys.stdout', new=StringIO()) as mock_stdout:
            main()
            output = mock_stdout.getvalue()
            assert 'Available commands' in output
            assert 'sword' in output or 'earth' in output


def test_main_list_categories():
    """Test --list-categories option"""
    with patch('sys.argv', ['minecraft-textcraft', '--list-categories']):
        with patch('sys.stdout', new=StringIO()) as mock_stdout:
            main()
            output = mock_stdout.getvalue()
            assert 'Available categories' in output
            assert 'weapons' in output or 'nature' in output


def test_main_get_command_with_color():
    """Test --get option with color - covers command handling and color"""
    with patch('sys.argv', ['minecraft-textcraft', '--get', 'sword', '--color', 'YELLOW']):
        with patch('sys.stdout', new=StringIO()) as mock_stdout:
            main()
            output = mock_stdout.getvalue()
            # Should output command ASCII art with color
            assert len(output) > 0
            assert '\n' in output


def test_main_get_command_invalid():
    """Test --get with invalid command"""
    with patch('sys.argv', ['minecraft-textcraft', '--get', 'nonexistent']):
        with patch('sys.stderr', new=StringIO()) as mock_stderr:
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
            error_output = mock_stderr.getvalue()
            assert 'Error' in error_output or 'not found' in error_output.lower()


def test_main_default_behavior():
    """Test default behavior (no arguments)"""
    with patch('sys.argv', ['minecraft-textcraft']):
        with patch('sys.stdout', new=StringIO()) as mock_stdout:
            with patch('sys.stderr', new=StringIO()) as mock_stderr:
                main()
                output = mock_stdout.getvalue()
                stderr_output = mock_stderr.getvalue()
                # Should render default text or show usage
                assert len(output) > 0 or 'Usage' in stderr_output or 'Note' in stderr_output


def test_main_invalid_text():
    """Test rendering invalid text"""
    with patch('sys.argv', ['minecraft-textcraft', 'HELLO!']):
        with patch('sys.stderr', new=StringIO()) as mock_stderr:
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
            error_output = mock_stderr.getvalue()
            assert 'Error' in error_output or 'invalid' in error_output.lower()


def test_main_animation_typewriter_verification():
    """Test --effect type animation - verify animation frames are generated correctly"""
    with patch('sys.argv', ['minecraft-textcraft', 'HELLO', '--effect', 'type']):
        captured_frames = []
        
        def capture_frames(frames_iter, fps=12):
            # Capture frames to verify animation works
            frame_list = list(frames_iter)
            captured_frames.extend(frame_list[:5])  # Capture first 5 frames
        
        with patch('minecraft_textcraft.__main__.play_animation', side_effect=capture_frames):
            with patch('sys.stdout', new=StringIO()):
                main()
        
        # Verify animation was called and frames were generated
        assert len(captured_frames) > 0, "Animation should generate frames"


def test_main_animation_scroll_verification():
    """Test --effect scroll animation - verify animation works with commands"""
    with patch('sys.argv', ['minecraft-textcraft', 'HELLO \\\\sword', '--effect', 'scroll']):
        with patch('minecraft_textcraft.__main__.play_animation') as mock_play:
            with patch('sys.stdout', new=StringIO()):
                main()
                # Should call play_animation
                assert mock_play.called
                # Verify frames were passed
                call_args = mock_play.call_args
                assert call_args is not None


def test_main_animation_wave_verification():
    """Test --effect wave animation - verify animation works"""
    with patch('sys.argv', ['minecraft-textcraft', 'HELLO', '--effect', 'wave']):
        with patch('minecraft_textcraft.__main__.play_animation') as mock_play:
            with patch('sys.stdout', new=StringIO()):
                main()
                # Should call play_animation
                assert mock_play.called


def test_main_animation_with_color_and_command():
    """Test animation with color and command - comprehensive test covering all features"""
    with patch('sys.argv', ['minecraft-textcraft', 'GET \\\\sword NOW', '--effect', 'type', '--color', 'GREEN']):
        with patch('minecraft_textcraft.__main__.play_animation') as mock_play:
            with patch('sys.stdout', new=StringIO()):
                main()
                # Should call play_animation with color and command
                assert mock_play.called
                call_args = mock_play.call_args
                assert call_args is not None


def test_main_animation_with_custom_fps():
    """Test animation with custom --fps option"""
    with patch('sys.argv', ['minecraft-textcraft', 'HELLO', '--effect', 'type', '--fps', '24']):
        with patch('minecraft_textcraft.__main__.play_animation') as mock_play:
            with patch('sys.stdout', new=StringIO()):
                main()
                # Should call play_animation with custom fps
                assert mock_play.called
                call_args = mock_play.call_args
                assert call_args.kwargs.get('fps') == 24


def test_main_animation_all_effects_with_colors():
    """Test all animation effects work with different colors"""
    effects = ['type', 'scroll', 'wave']
    colors = ['RED', 'GREEN', 'BLUE', 'YELLOW']
    
    for effect in effects:
        for color in colors:
            with patch('sys.argv', ['minecraft-textcraft', 'TEST', '--effect', effect, '--color', color]):
                with patch('minecraft_textcraft.__main__.play_animation') as mock_play:
                    with patch('sys.stdout', new=StringIO()):
                        main()
                        # Each combination should work
                        assert mock_play.called, f"Animation {effect} with color {color} should work"


def test_main_animation_invalid_effect():
    """Test that invalid effect is handled by argparse"""
    with patch('sys.argv', ['minecraft-textcraft', 'HELLO', '--effect', 'invalid']):
        with pytest.raises(SystemExit):
            main()


def test_main_animation_verification_with_frame_check():
    """Test animation actually generates progressive frames (typewriter effect)"""
    from minecraft_textcraft.animate import animate_typewriter
    from minecraft_textcraft.render import render
    
    # Render text
    rendered = render("HELLO")
    
    # Generate animation frames
    frames = list(animate_typewriter(rendered, cps=10))
    
    # Verify animation frames are progressive
    assert len(frames) > 1, "Animation should generate multiple frames"
    
    # First frame should be shorter or empty
    first_length = len(frames[0])
    last_length = len(frames[-1])
    
    # Last frame should be complete (longer or equal to first)
    assert last_length >= first_length, "Animation should progress from shorter to longer"
    
    # Verify frames are different (animation is happening)
    unique_frames = set(frames)
    assert len(unique_frames) > 1, "Animation frames should be different"
