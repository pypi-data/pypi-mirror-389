"""Main CLI entry point for lmodify."""

from pathlib import Path

import click
import rich_click as rc
from rich.console import Console

from . import __version__

# Configure rich-click
rc.USE_RICH_MARKUP = True
rc.SHOW_ARGUMENTS = True
rc.GROUP_ARGUMENTS_OPTIONS = True
rc.USE_MARKDOWN = True

console = Console()


@click.group(context_settings=dict(help_option_names=["-h", "--help"]))
@click.version_option(version=__version__, prog_name="lmodify")
@click.option(
    "-c",
    "--config",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file (default: ~/.config/lmodify.ini)",
)
@click.pass_context
def cli(ctx: click.Context, config: Path | None) -> None:
    """
    lmodify - Create LMOD packages based on Singularity images.

    A tool for managing LMOD modules from Singularity containers in HPC environments.
    """
    # Store config path in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config


def main() -> None:
    """Main entry point."""
    # Import commands here to avoid circular imports
    from .commands import add, create, init, list as list_cmd

    # Register commands
    cli.add_command(init.init)
    cli.add_command(create.create)
    cli.add_command(list_cmd.list_packages)
    cli.add_command(add.add)

    # Run CLI
    cli()


if __name__ == "__main__":
    main()
