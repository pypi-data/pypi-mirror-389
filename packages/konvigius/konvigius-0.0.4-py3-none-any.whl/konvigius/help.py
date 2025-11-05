# src/konvigius/help.py
"""Contains the built-in manual text for the konvigius package."""

from importlib.resources import files


def manual() -> str:
    """Return the package manual in Markdown format."""
    return (files(__package__) / "MANUAL.md").read_text(encoding="utf-8")
