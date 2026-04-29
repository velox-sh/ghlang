"""Run ghlang as a module: ``python -m ghlang``."""

from ghlang import version


def main() -> None:
    """Print the package version."""
    print(version())


if __name__ == "__main__":
    main()
