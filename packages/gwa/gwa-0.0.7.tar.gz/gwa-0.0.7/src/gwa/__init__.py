"""GWA - Your package description here."""

from gwa.cli import init_cli


def main() -> None:
    """Main entry point for the GWA CLI."""
    # todo: Add the TUI

    # todo: Create a way to choose between CLI and TUI (maybe a command line argument?) 
    # todo: I mean, called as 'gwa' will call the cli
    # todo: But if it is called as 'gwa tui', it should call the TUI

    init_cli()
    # init_tui()  # Uncomment this line to enable TUI


if __name__ == "__main__":
    main()
