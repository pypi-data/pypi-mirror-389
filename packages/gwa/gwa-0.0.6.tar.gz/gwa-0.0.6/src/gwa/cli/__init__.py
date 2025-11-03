"""CLI application for GWA"""

from typer import Typer
from rich.console import Console

app: Typer = Typer(
    name="gwa",
    help="A lightning-fast scaffolder for General Web App (GWA) projects.",
    no_args_is_help=True,
    add_completion=False,
)

console = Console()


def init_cli():
    """Register all CLI commands and options with the app."""
    from gwa.cli.callbacks import register_callbacks
    from gwa.cli.commands import register_commands

    # * Register all commands and options with the app
    register_callbacks(app)
    register_commands(app)

    app()
