"""List command - List available LMOD packages."""

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from ..config import ConfigError, load_config
from ..lmod import list_packages as get_lmod_packages

console = Console()


@click.command("list", context_settings=dict(help_option_names=["-h", "--help"]))
@click.argument("keyword", required=False)
@click.option(
    "-p",
    "--packages-only",
    is_flag=True,
    help="List only package names, not versions",
)
@click.option(
    "-l",
    "--lmod-path",
    type=click.Path(path_type=Path),
    help="Path to LMOD Lua packages (overrides config)",
)
@click.pass_context
def list_packages(
    ctx: click.Context,
    keyword: str | None,
    packages_only: bool,
    lmod_path: Path | None,
) -> None:
    """
    List available LMOD packages.

    KEYWORD: Optional search term to filter packages (case-insensitive)

    Example:
        lmodify list
        lmodify list seqfu
        lmodify list -p
    """
    # Load config
    config_path = ctx.obj.get("config_path")
    try:
        config = load_config(config_path)
    except ConfigError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()

    # Use config path if not overridden
    if lmod_path is None:
        lmod_path = config.lmod_path

    # Check if lmod_path exists
    if not lmod_path.exists():
        console.print(
            f"[yellow]Warning:[/yellow] LMOD path does not exist: {lmod_path}"
        )
        console.print("No packages found.")
        return

    # Get packages
    packages = get_lmod_packages(lmod_path)

    if not packages:
        console.print("No packages found.")
        return

    # Filter by keyword if provided
    if keyword:
        keyword_lower = keyword.lower()
        packages = [pkg for pkg in packages if keyword_lower in pkg.name.lower()]

        if not packages:
            console.print(f"No packages found matching: {keyword}")
            return

    # Display packages
    if packages_only:
        _display_packages_only(packages)
    else:
        _display_packages_with_versions(packages)


def _display_packages_only(packages: list) -> None:
    """Display only package names."""
    console.print(f"\n[bold]Available Packages ({len(packages)})[/bold]\n")

    for package in packages:
        console.print(f"  {package.name}")

    console.print()


def _display_packages_with_versions(packages: list) -> None:
    """Display packages with their versions."""
    table = Table(title=f"Available Packages ({len(packages)})")

    table.add_column("Package", style="cyan", no_wrap=True)
    table.add_column("Versions", style="green")
    table.add_column("Count", justify="right", style="dim")

    for package in packages:
        versions_str = ", ".join(package.versions)
        table.add_row(
            package.name,
            versions_str,
            str(len(package.versions)),
        )

    console.print()
    console.print(table)
    console.print()
