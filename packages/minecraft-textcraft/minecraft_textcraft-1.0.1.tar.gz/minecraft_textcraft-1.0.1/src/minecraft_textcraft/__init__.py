__version__ = "1.0.1"

from .add import add
from .colorize_ascii import colorize_ascii, Color
from .commands import getCommand, getCommandByName, get_command, listCategories, listCommands
from .animate import animate_typewriter, animate_scroll, animate_wave, play_animation
from .render import render, renderTextOnly, renderCommandOnly, renderTextAndCommands
