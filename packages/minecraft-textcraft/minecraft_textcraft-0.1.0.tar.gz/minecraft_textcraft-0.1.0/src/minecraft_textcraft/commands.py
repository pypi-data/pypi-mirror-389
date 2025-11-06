from .sample_commands import SAMPLE_COMMANDS
COMMANDS = SAMPLE_COMMANDS


def listCategories() -> list[str]:
    return list(COMMANDS.keys())


def getCommand(category: str = "weapons") -> dict[str, str]:
    if category not in COMMANDS:
        available_categories = listCategories()
        raise KeyError(f"Category '{category}' not found. Available categories: {available_categories}")
    
    return COMMANDS[category].copy()


def getCommandByName(category: str, command_name: str) -> str:
    if category not in COMMANDS:
        available_categories = listCategories()
        raise KeyError(f"Category '{category}' not found. Available categories: {available_categories}")
    
    if command_name not in COMMANDS[category]:
        available_commands = list(COMMANDS[category].keys())
        raise KeyError(f"Command '{command_name}' not found in category '{category}'. Available commands: {available_commands}")
    
    return COMMANDS[category][command_name]


def listCommands(category: str = None) -> list[str]:
    if category is None:
        all_commands = []
        for cat_commands in COMMANDS.values():
            all_commands.extend(cat_commands.keys())
        return all_commands
    
    if category not in COMMANDS:
        available_categories = listCategories()
        raise KeyError(f"Category '{category}' not found. Available categories: {available_categories}")
    
    return list(COMMANDS[category].keys())


def get_command(name: str) -> str:
    """
    Get ASCII art for a specific command by name.
    Searches through all categories to find the command.
    
    Args:nName of the command (e.g., "sword", "heart", "earth")
    
    Returns ASCII art string for the command
    
    Raises ValueError if command is not found in any category
    """
    # Search through all categories to find the command
    for category, commands in COMMANDS.items():
        if name in commands:
            return commands[name]
    
    all_commands = listCommands()
    available = ", ".join(sorted(all_commands)) if all_commands else "none"
    raise ValueError(
        f"Command '{name}' not found. Available commands: {available}"
    )