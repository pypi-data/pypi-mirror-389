"""
Main entry point for minecraft-textcraft package.
Provides command-line interface for all core functions.
"""
import argparse
import sys
import traceback
from .render import render
from .commands import listCommands, get_command, listCategories
from .colorize_ascii import colorize_ascii, Color

try:
    from .animate import animate_typewriter, animate_scroll, animate_wave, play_animation
    _ANIM_AVAILABLE = True
except Exception:
    _ANIM_AVAILABLE = False


def _get_color(color_string: str) -> Color:
    """Get Color enum from string"""
    return Color.from_string(color_string)


def _apply_color(text: str, color_string: str) -> str:
    """Apply color to text"""
    return colorize_ascii(text, _get_color(color_string))


def _handle_error(message: str, exit_code: int = 1):
    """Handle error with consistent formatting"""
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(exit_code)


def main():
    """Main entry point for the command-line interface"""
    parser = argparse.ArgumentParser(
        description="Minecraft-style ASCII art text renderer. See DEMO_COMMANDS.md for examples.",
        formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=35, width=100)
    )
    
    # Main arguments
    parser.add_argument(
        "text",
        nargs="?",
        default=None,
        help="Text to render (use double backslash \\\\ for commands)"
    )
    
    # Command list operations
    parser.add_argument(
        "--list",
        "--list-commands",
        dest="list_commands",
        action="store_true",
        help="List all available commands"
    )
    parser.add_argument(
        "--list-categories",
        action="store_true",
        help="List all command categories"
    )
    
    # Get command
    parser.add_argument(
        "--get",
        "--get-command",
        dest="get_command",
        metavar="NAME",
        help="Get ASCII art for a specific command"
    )
    parser.add_argument(
        "--effect",
        choices=["type", "scroll", "wave"],
        help="Apply animation effect"
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=12,
        help="Animation frames per second (default: 12)"
    )
    parser.add_argument(
        "--color",
        default=None,
        help="Output color: RED, GREEN, YELLOW, BLUE (default: no color)"
    )
    
    args = parser.parse_args()
    
    if args.list_commands:
        try:
            commands = listCommands()
            if commands:
                print("Available commands:")
                for cmd in sorted(commands):
                    print(f"  - {cmd}")
            else:
                print("No commands available.")
        except Exception as e:
            _handle_error(f"listing commands: {e}")
        return
    
    if args.list_categories:
        try:
            categories = listCategories()
            if categories:
                print("Available categories:")
                for cat in sorted(categories):
                    commands = listCommands(cat)
                    print(f"  - {cat}: {len(commands)} commands")
            else:
                print("No categories available.")
        except Exception as e:
            _handle_error(f"listing categories: {e}")
        return
    
    if args.get_command:
        try:
            command_art = get_command(args.get_command)
            if args.color:
                print(_apply_color(command_art, args.color))
            else:
                print(command_art)
        except ValueError as e:
            _handle_error(str(e))
        except Exception as e:
            _handle_error(f"getting command: {e}")
        return
    
    text = args.text or "HELLO"
    if args.text is None:
        print("Note: No text provided, using default 'HELLO'", file=sys.stderr)
        print("Usage: minecraft-textcraft 'YOUR TEXT' (see DEMO_COMMANDS.md for examples)", file=sys.stderr)
        print()
    
    try:
        result = render(text)
        
        if args.effect and _ANIM_AVAILABLE:
            color = _get_color(args.color) if args.color else Color.DEFAULT
            if args.effect == "type":
                frames = animate_typewriter(result, color=color, cps=12)
            elif args.effect == "scroll":
                frames = animate_scroll(result, color=color, cols_per_frame=1, loops=1)
            elif args.effect == "wave":
                frames = animate_wave(result, color=color, amplitude=2, period_cols=10, frames=36)
            play_animation(frames, fps=args.fps)
        else:
            if args.color:
                print(_apply_color(result, args.color))
            else:
                print(result)
            
            if args.effect and not _ANIM_AVAILABLE:
                print("Warning: Animation requested but animation support is not available.", file=sys.stderr)
    
    except ValueError as e:
        _handle_error(str(e))
    except KeyboardInterrupt:
        print("\nInterrupted by user.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Error rendering text: {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
