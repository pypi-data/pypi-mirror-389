"""
Render functions for converting text into Minecraft-style ASCII art.
Supports A-Z, 0-9 text and inline commands.
"""

import re
from typing import List, Tuple
from .font_data import get_char, get_char_height, CHAR_HEIGHT, CHAR_WIDTH
from .commands import get_command, listCommands


def _validate_text(text: str) -> bool:
    """
    Validate that text contains only A-Z, 0-9, and spaces.

    Args:
        text: Text to validate

    Returns:
        True if valid, False otherwise
    """
    return bool(re.match(r"^[A-Za-z0-9\s]+$", text))


def _parse_input(input_str: str) -> Tuple[List[str], List[str]]:
    """
    Parse input string into text parts and command parts.

    Commands are specified with double backslash: \\command

    Args:
        input_str: Input string to parse

    Returns:
        Tuple of (text_parts, command_parts)
        text_parts: List of text segments
        command_parts: List of command names (without backslashes)
    """
    # Split by double backslash pattern
    parts = re.split(r"(\\\\\w+)", input_str)

    text_parts = []
    command_parts = []

    for part in parts:
        if not part:
            continue
        if part.startswith("\\\\"):
            command_name = part[2:]
            command_parts.append(command_name)
            text_parts.append(None)
        else:
            text_parts.append(part)
            command_parts.append(None)

    return text_parts, command_parts


def renderTextOnly(text: str) -> str:
    """
    Render text only (A-Z, 0-9) into 16-block tall Minecraft-style ASCII art.

    Args:
        text: Text to render (only A-Z, 0-9, spaces allowed)

    Returns:
        Multi-line string representing the rendered text

    Raises:
        ValueError: If text contains invalid characters

    Edge Cases Handled:
        - Empty string → returns empty string
        - Whitespace-only string → returns empty string (no visible output)
        - Invalid characters → raises ValueError with details
    """
    # Edge case: empty string
    if not text:
        return ""

    # Edge case: whitespace-only string
    if not text.strip():
        return ""

    if not _validate_text(text):
        invalid_chars = set(text) - set(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 "
        )
        raise ValueError(
            f"Text contains invalid characters. Only A-Z, 0-9, and spaces are allowed. Invalid: {invalid_chars}"
        )

    # Convert to uppercase for rendering
    text = text.upper()

    # Get character data for each character
    char_data_list = []
    for char in text:
        try:
            char_data = get_char(char)
            char_data_list.append(char_data)
        except KeyError as e:
            # Edge case: character not in font (shouldn't happen after validation, but defensive)
            raise ValueError(f"Character '{char}' cannot be rendered: {e}")

    # Edge case: no valid characters (shouldn't happen, but defensive)
    if not char_data_list:
        return ""

    # All characters have the same height (16)
    height = get_char_height()
    result_lines = []

    # Spacing between characters (6 spaces for better readability)
    CHAR_SPACING = 6

    for row in range(height):
        line = ""
        for i, char_data in enumerate(char_data_list):
            # Edge case: ensure we don't go out of bounds
            if row < len(char_data):
                line += char_data[row]
            else:
                # If somehow row is out of bounds, add spaces
                # Use CHAR_WIDTH since get_char() always returns padded rows
                line += " " * CHAR_WIDTH

            # Add spacing between characters (except after the last character)
            if i < len(char_data_list) - 1:
                line += " " * CHAR_SPACING

        result_lines.append(line)

    return "\n".join(result_lines)


def renderCommandOnly(command_name: str) -> str:
    """
    Render a single command only, padded to its natural width box.

    Each command is padded to its own maximum width so all rows align properly
    within that command's box. Different commands can have different box sizes.
    For example: sword might be 20 chars wide, earth might be 45 chars wide.

    Args:
        command_name: Name of the command (e.g., "sword", "heart")

    Returns:
        Multi-line string representing the rendered command,
        with each row padded to the command's maximum width
    """
    # Get command art using get_command (searches all categories automatically)
    command_art = get_command(command_name)

    # Split command into lines
    lines = command_art.split("\n")
    if not lines:
        return ""

    # Find the maximum width for THIS specific command
    # Filter out empty/whitespace-only lines to find the actual content width
    non_empty_lines = [line for line in lines if line.strip()]

    # Edge case: if command has no content, return empty
    if not non_empty_lines:
        return ""

    max_width = max(len(line) for line in non_empty_lines)

    # Pad each row to this command's maximum width (creates a box for this command)
    padded_lines = []
    for line in lines:
        # Pad each line to the command's natural width
        padded_line = line.ljust(max_width)
        padded_lines.append(padded_line)

    return "\n".join(padded_lines)


def renderTextAndCommands(text: str) -> str:
    """
    Render text with inline commands mixed in.
    Commands are specified with double backslash: \\command

    Args:
        text: Text with inline commands (e.g., "HELLO \\heart WORLD")

    Returns:
        Multi-line string representing the rendered text and commands

    Raises:
        ValueError: If malformed commands are detected (e.g., \\\\ without command name)
    """
    if not text:
        return ""

    # Parse the input
    parts = []
    current_text = ""
    i = 0

    while i < len(text):
        # Check for double backslash
        if i < len(text) - 1 and text[i] == "\\" and text[i + 1] == "\\":
            # Found start of command
            if current_text:
                parts.append(("text", current_text))
                current_text = ""

            # Find the command name
            i += 2  # Skip \\
            command_start = i
            while i < len(text) and (text[i].isalnum() or text[i] == "_"):
                i += 1
            command_name = text[command_start:i]

            # Edge case: malformed command (\\ followed by nothing or invalid characters)
            if not command_name:
                raise ValueError(
                    f"Malformed command detected at position {i-2}. "
                    "Commands must be in the format: \\\\commandname (e.g., \\\\sword)"
                )

            parts.append(("command", command_name))
            # Don't increment i here, it's already at the right position
        else:
            current_text += text[i]
            i += 1

    if current_text:
        parts.append(("text", current_text))

    # Edge case: no valid parts to render
    if not parts:
        return ""

    # Render each part
    rendered_parts = []
    for part_type, part_content in parts:
        if part_type == "text":
            # Only render if there's actual non-whitespace text
            if part_content and part_content.strip():
                rendered = renderTextOnly(part_content)
                rendered_parts.append(rendered)
            # Skip whitespace-only text parts
        elif part_type == "command":
            rendered = renderCommandOnly(part_content)
            rendered_parts.append(rendered)

    # Edge case: all parts were empty/whitespace
    if not rendered_parts:
        return ""

    # Combine parts horizontally with proper alignment
    return _combine_horizontally(rendered_parts)


def _combine_horizontally(parts: List[str]) -> str:
    """
    Combine multiple rendered parts horizontally, center-aligning them vertically.

    Args:
        parts: List of rendered ASCII art strings

    Returns:
        Combined multi-line string
    """
    if not parts:
        return ""

    # Filter out empty parts
    non_empty_parts = [p for p in parts if p and p.strip()]
    if not non_empty_parts:
        return ""

    # Split each part into lines
    part_lines = []
    max_height = CHAR_HEIGHT

    for part in non_empty_parts:
        # Split into lines, preserving all lines (including trailing empty ones)
        lines = part.split("\n")
        # Remove trailing empty lines but keep leading/middle empty lines
        while lines and not lines[-1].strip():
            lines.pop()
        if not lines:
            continue
        part_lines.append(lines)
        max_height = max(max_height, len(lines))

    # Edge case: all parts were empty after splitting
    if not part_lines:
        return ""

    # Pad all parts to max_height by adding empty lines at top/bottom for center alignment
    padded_parts = []
    for lines in part_lines:
        height = len(lines)
        if height < max_height:
            # Center align: add half padding above and below
            pad_top = (max_height - height) // 2
            pad_bottom = max_height - height - pad_top

            # Get width of lines for padding - use max width to handle any variations
            # Each part should already have consistent width, but we use max for safety
            width = max(len(line) for line in lines) if lines else 0
            if width == 0:
                continue  # Skip parts with no width
            padded = [" " * width] * pad_top + lines + [" " * width] * pad_bottom
            padded_parts.append(padded)
        else:
            padded_parts.append(lines)

    # Spacing between commands (4 spaces)
    COMMAND_SPACING = 4

    # Combine horizontally
    result_lines = []
    for row in range(max_height):
        line = ""
        for i, part in enumerate(padded_parts):
            if row < len(part):
                line += part[row]
            else:
                # Edge case: Add spaces if this part is shorter than expected
                if part:
                    width = max(len(p) for p in part) if part else 0
                    line += " " * width

            # Add spacing between commands (except after the last command)
            if i < len(padded_parts) - 1:
                line += " " * COMMAND_SPACING

        result_lines.append(line)

    return "\n".join(result_lines)


def render(input_str: str) -> str:
    """
    Main render function that routes input to appropriate sub-function.

    Automatically detects if input contains:
    - Text only → renderTextOnly()
    - Commands only → renderCommandOnly() or handles multiple commands
    - Text and commands → renderTextAndCommands()

    Args:
        input_str: Input string with optional commands (\\command format)

    Returns:
        Multi-line string representing the rendered output
    """
    if not input_str:
        return ""

    # Check if input contains double backslash (commands)
    has_commands = "\\\\" in input_str

    # Check if input contains text (A-Z, 0-9)
    text_only_part = re.sub(r"\\\\\w+", "", input_str).strip()
    has_text = bool(text_only_part) and bool(re.search(r"[A-Za-z0-9]", text_only_part))

    # Route to appropriate function
    if has_text and has_commands:
        # Mixed text and commands
        return renderTextAndCommands(input_str)
    elif has_commands:
        # Commands only - extract all commands
        commands = re.findall(r"\\\\(\w+)", input_str)
        if len(commands) == 1:
            return renderCommandOnly(commands[0])
        else:
            # Multiple commands only - combine them
            parts = []
            for cmd in commands:
                rendered = renderCommandOnly(cmd)
                parts.append(rendered)
            return _combine_horizontally(parts)
    else:
        # Text only
        return renderTextOnly(input_str)
