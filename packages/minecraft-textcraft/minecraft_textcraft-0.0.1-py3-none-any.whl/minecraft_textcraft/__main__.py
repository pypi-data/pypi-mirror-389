from .colorize_ascii import colorize_ascii, Color

HELLO = """
█   █ █████ █     █     █████
█   █ █     █     █     █   █
█████ ████  █     █     █   █
█   █ █     █     █     █   █
█   █ █████ █████ █████ █████
"""


def main():
    print(colorize_ascii(HELLO.strip("\n"), Color.RED))


if __name__ == "__main__":
    main()
