from enum import Enum

ESC = "\x1b"

class Color(Enum):
    RED = 31
    GREEN = 32
    YELLOW = 33
    BLUE = 34
    DEFAULT = 0

    def __str__(self):
        return f"{ESC}[{self.value}m"

    @classmethod
    def from_string(cls, s: str) -> "Color":
        try:
            return cls[s.upper()]
        except KeyError:
            return cls.DEFAULT


def colorize_ascii(ascii: str, color: Color):
    return f"{color}{ascii}{Color.DEFAULT}"
