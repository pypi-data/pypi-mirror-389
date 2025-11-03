from typing import Optional

import typer


def register_callbacks(app: typer.Typer):
    """Register all global options with the Typer app."""
    app.callback(invoke_without_command=True)(version)


def define_version_globals():
    # declare global variables
    global __version_crates__
    global __python_version__
    global __version_pypi__
    # import statements
    from gwa._core import get_crate_version
    from importlib.metadata import version
    from sys import version_info as v_info

    # assign global variables
    __version_crates__ = get_crate_version()
    __version_pypi__ = version("gwa")
    __python_version__ = f"{v_info.major}.{v_info.minor}.{v_info.micro}"


define_version_globals()


def version(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show the version of GWA CLI.",
        is_eager=True,
    ),
):
    from rich.console import Console
    from rich.table import Table

    # Create a clean table
    table = Table(show_header=False, box=None, padding=(0, 2))

    table.add_row("[bold cyan]Python[/]", f"[green]{__python_version__}[/]")
    table.add_row("[dim](cli) py[/]", f"[blue italic]{__version_pypi__}[/]")
    table.add_row("[dim](engine) rs[/]", f"[blue italic]{__version_crates__}[/]")

    console = Console()
    console.print(table)
