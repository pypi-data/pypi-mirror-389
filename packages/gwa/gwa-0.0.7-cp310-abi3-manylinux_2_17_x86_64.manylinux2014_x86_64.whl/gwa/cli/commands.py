from pathlib import Path
from typing import Optional

import typer

from gwa import _core

from gwa.cli import console


def register_commands(app: typer.Typer):
    """Register all commands with the Typer app."""
    app.command()(create)


def create(
    name: str = typer.Argument(..., help="Name for the new project directory."),
    destination: Path = typer.Option(
        Path("."),
        "--destination",
        "-d",
        help="The directory where the new project folder will be placed.",
    ),
    db_name: Optional[str] = typer.Option(
        None, "--db-name", help="Database name for the project."
    ),
    db_admin: Optional[str] = typer.Option(
        None, "--db-admin", help="Database admin username."
    ),
    db_password: Optional[str] = typer.Option(
        None, "--db-password", help="Database password."
    ),
    include_server: bool = typer.Option(
        True, "--server/--no-server", help="Include backend server component."
    ),
    include_frontend: bool = typer.Option(
        True, "--frontend/--no-frontend", help="Include frontend component."
    ),
    include_tauri: bool = typer.Option(
        True, "--tauri/--no-tauri", help="Include Tauri desktop component."
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip all interactive prompts and use default values for rapid testing.",
    ),
) -> None:
    """Create a new GWA project from the template."""
    console.print(
        f"[bold blue]🚀 Creating new GWA project:[/bold blue] [green]{name}[/green]"
    )

    # Build the configuration dictionary to match the Rust function signature
    config_dict = {
        "project_name": name,
        "destination": str(destination),
        "author_name": "Test User" if yes else "GWA User",
        "author_email": "test@example.com" if yes else "user@example.com",
        "app_identifier": f"com.example.{name.lower().replace('-', '')}",
        "deno_package_name": f"@test/{name}" if yes else f"@user/{name}",
    }

    # Set database configuration
    if db_name:
        config_dict["db_name"] = db_name
    elif yes:
        config_dict["db_name"] = name.lower().replace("-", "_")
    else:
        config_dict["db_name"] = name.lower().replace("-", "_")

    if db_admin:
        config_dict["db_owner_admin"] = db_admin
    elif yes:
        config_dict["db_owner_admin"] = f"{name.lower().replace('-', '_')}_owner"
    else:
        config_dict["db_owner_admin"] = f"{name.lower().replace('-', '_')}_owner"

    if db_password:
        config_dict["db_owner_pword"] = db_password
    elif yes:
        config_dict["db_owner_pword"] = "password"
    else:
        config_dict["db_owner_pword"] = "password"

    # Set component inclusion
    config_dict["include_server"] = include_server
    config_dict["include_frontend"] = include_frontend
    config_dict["include_tauri_desktop"] = include_tauri

    # If --yes flag is provided, use more complete defaults
    if yes:
        console.print(
            "[bold yellow]⚠️ Fast-track mode enabled (--yes). Using default values.[/bold yellow]"
        )

    # Confirm with user before proceeding (unless --yes is specified)
    if not yes:
        confirm = typer.confirm("Proceed with project creation?", default=True)
        if not confirm:
            console.print("[yellow]Operation cancelled by user.[/yellow]")
            raise typer.Exit(code=0)

    # Check if Rust module is available
    if _core is None:
        console.print(
            "[bold red]Error: Rust module not available. Please build the project with 'maturin develop'.[/bold red]"
        )
        raise typer.Exit(code=1)

    try:
        console.print("[bold]⚙️ Starting project generation...[/bold]")
        success = _core.run_engine(config_dict)
        if success:
            console.print(
                f"[bold green]✅ Project '{name}' created successfully![/bold green]"
            )
            console.print(f"[bold]📁 Location:[/bold] {destination / name}")
        else:
            console.print("[bold red]❌ Project generation failed.[/bold red]")
            raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[bold red]❌ Error during generation:[/bold red] {e}")
        raise typer.Exit(code=1)
