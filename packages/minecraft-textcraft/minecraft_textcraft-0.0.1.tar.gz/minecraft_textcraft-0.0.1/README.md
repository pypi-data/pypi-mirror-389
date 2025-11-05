# minecraft-textcraft

A Python package that converts text into blocky Minecraft-style ASCII art, with support for special inline commands like \sword, \heart, and \diamond. Commands are center-aligned with text for a professional, visually appealing output.

# Quickstart

To setup:
```bash
git clone git@github.com:swe-students-fall2025/3-python-package-brio.git
cd 3-python-package-brio
pipenv shell
pipenv install -e ".[dev]"
```

To build:
```bash
pipenv run python -m build
```
Artifacts will be in `dist/`.

To run:
```bash
pipenv run minecraft-textcraft
```

To run tests:
```bash
pipenv run pytest
```

