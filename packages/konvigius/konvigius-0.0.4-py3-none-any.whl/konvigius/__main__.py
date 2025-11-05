"""
Executed when you run `python -m konvigius`.

This entry point gives a short explanation or runs a simple diagnostic.
"""

from . import __version__


def main() -> None:
    print(f"\nKonvigius v{__version__}")
    print()
    print("This package provides configuration utilities.")
    print("It is not meant to be executed directly.")
    print("Try importing it in Python code, or run your own CLI that uses it.")
    print()
    print("The Konvigius project includes several demo Python files with simple ")
    print("examples located in the /examples directory.")
    print("Additionally, the README.md file provides a few illustrative examples.")
    print(
        "Finally, the manual() function generates a complete user manual in Markdown "
    )
    print("format.\n")
    print()
    print("Try this:\n")
    print(">>> import konvigius")
    print(">>> print(konvigius.manual())")
    print("\nOr this, even more simple:\n")
    print('python -c "import konvigius; print(konvigius.manual())"')


if __name__ == "__main__":  # pragma: nocoverage
    main()
