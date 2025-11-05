"""Init command - Create configuration file."""

from pathlib import Path

import click
from rich.console import Console
from rich.prompt import Confirm, Prompt

from ..config import (
    ConfigError,
    config_exists,
    create_default_config,
    get_default_config_path,
)

console = Console()


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.option(
    "-o",
    "--output",
    type=click.Path(path_type=Path),
    help="Output path for config file (default: ~/.config/lmodify.ini)",
)
@click.option(
    "-f",
    "--force",
    is_flag=True,
    help="Overwrite existing config file",
)
@click.option(
    "--singularity-path",
    type=str,
    help="Path to Singularity images",
)
@click.option(
    "--bin-path",
    type=str,
    help="Path for binary wrappers",
)
@click.option(
    "--lmod-path",
    type=str,
    help="Path for LMOD Lua files",
)
@click.option(
    "--name",
    type=str,
    help="Your name (author)",
)
@click.option(
    "--email",
    type=str,
    help="Your email",
)
@click.option(
    "--organization",
    type=str,
    help="Your organization",
)
def init(
    output: Path | None,
    force: bool,
    singularity_path: str | None,
    bin_path: str | None,
    lmod_path: str | None,
    name: str | None,
    email: str | None,
    organization: str | None,
) -> None:
    """
    Create a configuration file with interactive prompts.

    This will guide you through setting up lmodify with the paths
    for your Singularity images, binaries, and LMOD modules.
    """
    # Determine config path
    if output is None:
        config_path = get_default_config_path()
    else:
        config_path = output

    # Check if config already exists
    if config_exists(config_path) and not force:
        console.print(
            f"[yellow]Configuration file already exists:[/yellow] {config_path}"
        )
        if not Confirm.ask("Do you want to overwrite it?"):
            console.print("[red]Aborted.[/red]")
            raise click.Abort()

    # Prompt for values
    values = {}

    # Only show header if we need to prompt for anything
    needs_prompt = any(
        [
            singularity_path is None,
            bin_path is None,
            lmod_path is None,
            name is None,
            email is None,
            organization is None,
        ]
    )

    if needs_prompt:
        console.print("[bold]lmodify Configuration Setup[/bold]\n")
        console.print(
            "Please provide the following paths for your HPC environment.\n"
            "Press Enter to use the default value shown in brackets.\n"
        )

    # Path configurations
    if singularity_path is None:
        values["singularity_default_path"] = Prompt.ask(
            "Path to Singularity images",
            default="/qib/research-projects/bioboxes/singularity",
        )
    else:
        values["singularity_default_path"] = singularity_path

    if bin_path is None:
        values["bin_path"] = Prompt.ask(
            "Path for binary wrappers",
            default="/qib/research-projects/bioboxes/links/",
        )
    else:
        values["bin_path"] = bin_path

    if lmod_path is None:
        values["lmod_path"] = Prompt.ask(
            "Path for LMOD Lua files",
            default="/qib/research-projects/bioboxes/lua/",
        )
    else:
        values["lmod_path"] = lmod_path

    # Metadata configurations
    if any([name is None, email is None, organization is None]):
        console.print("\n[bold]Metadata (for generated files)[/bold]\n")

    if name is None:
        values["author"] = Prompt.ask(
            "Your name",
            default="Your Name",
        )
    else:
        values["author"] = name

    if email is None:
        values["email"] = Prompt.ask(
            "Your email",
            default="your.email@example.com",
        )
    else:
        values["email"] = email

    if organization is None:
        values["organization"] = Prompt.ask(
            "Your organization",
            default="Your Organization",
        )
    else:
        values["organization"] = organization

    # Create config file
    try:
        create_default_config(config_path, values)
        console.print(f"\n[green]Configuration file created:[/green] {config_path}")
        console.print("\nYou can now use lmodify commands. Try:")
        console.print("  [cyan]lmodify list[/cyan]")
        console.print("  [cyan]lmodify create --help[/cyan]")
    except ConfigError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()
