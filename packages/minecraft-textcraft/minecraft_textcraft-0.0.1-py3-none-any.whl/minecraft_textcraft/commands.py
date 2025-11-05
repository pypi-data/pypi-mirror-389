from .sample_commands import SAMPLE_COMMANDS

# Use sample commands for now，can be replaced later
COMMANDS = SAMPLE_COMMANDS


def getCommand(category: str = "weapons") -> dict[str, str]:
    if category not in COMMANDS:
        available_categories = list(COMMANDS.keys())
        raise KeyError(f"Category '{category}' not found. Available categories: {available_categories}")
    
    return COMMANDS[category].copy()


def getCommandByName(category: str, command_name: str) -> str:
    if category not in COMMANDS:
        available_categories = list(COMMANDS.keys())
        raise KeyError(f"Category '{category}' not found. Available categories: {available_categories}")
    
    if command_name not in COMMANDS[category]:
        available_commands = list(COMMANDS[category].keys())
        raise KeyError(f"Command '{command_name}' not found in category '{category}'. Available commands: {available_commands}")
    
    return COMMANDS[category][command_name]


def listCategories() -> list[str]:
    return list(COMMANDS.keys())


def listCommands(category: str = None) -> list[str]:
    if category is None:
        all_commands = []
        for cat_commands in COMMANDS.values():
            all_commands.extend(cat_commands.keys())
        return all_commands
    
    if category not in COMMANDS:
        available_categories = list(COMMANDS.keys())
        raise KeyError(f"Category '{category}' not found. Available categories: {available_categories}")
    
    return list(COMMANDS[category].keys())
