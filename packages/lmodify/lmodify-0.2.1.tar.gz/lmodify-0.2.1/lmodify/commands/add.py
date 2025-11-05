"""Add command - Add a new command to an existing package."""

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from ..config import ConfigError, load_config
from ..lmod import find_package_versions
from ..singularity import add_command_symlink

console = Console()


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.argument("package")
@click.argument("command")
@click.option(
    "-v",
    "--version",
    help="Add command to specific version (if not specified, adds to all versions)",
)
@click.option(
    "-l",
    "--lmod-path",
    type=click.Path(path_type=Path),
    help="Path to LMOD Lua packages (overrides config)",
)
@click.option(
    "-b",
    "--bin-path",
    type=click.Path(path_type=Path),
    help="Path for binary wrappers (overrides config)",
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite existing command symlink",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be done without making changes",
)
@click.pass_context
def add(
    ctx: click.Context,
    package: str,
    command: str,
    version: str | None,
    lmod_path: Path | None,
    bin_path: Path | None,
    force: bool,
    dry_run: bool,
) -> None:
    """
    Add a new command to an existing package.

    PACKAGE: Name of the package
    COMMAND: Name of the command to add

    Example:
        lmodify add seqfu seqfu-stats
        lmodify add seqfu seqfu-stats --version 1.20.3
    """
    # Load config
    config_path = ctx.obj.get("config_path")
    try:
        config = load_config(config_path)
    except ConfigError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()

    # Use config paths if not overridden
    if lmod_path is None:
        lmod_path = config.lmod_path
    if bin_path is None:
        bin_path = config.bin_path

    # Find package versions
    if version:
        versions = [version]
        # Verify version exists
        available = find_package_versions(lmod_path, package)
        if version not in available:
            console.print(
                f"[red]Error:[/red] Version {version} not found for package {package}"
            )
            console.print(f"Available versions: {', '.join(available)}")
            raise click.Abort()
    else:
        versions = find_package_versions(lmod_path, package)
        if not versions:
            console.print(f"[red]Error:[/red] Package not found: {package}")
            console.print("Run 'lmodify list' to see available packages.")
            raise click.Abort()

    # Display plan
    _display_add_plan(package, command, versions, bin_path)

    if dry_run:
        console.print("\n[yellow]Dry run - no changes made[/yellow]")
        return

    # Add command to each version
    results = []
    for ver in versions:
        package_dir = bin_path / f"{package}__{ver}"

        try:
            added = add_command_symlink(
                bin_dir=package_dir,
                command=command,
                force=force,
                dry_run=dry_run,
            )
            results.append((ver, added, None))
        except FileNotFoundError as e:
            results.append((ver, False, str(e)))
        except Exception as e:
            results.append((ver, False, str(e)))

    # Display results
    _display_results(package, command, results, force)


def _display_add_plan(
    package: str,
    command: str,
    versions: list[str],
    bin_path: Path,
) -> None:
    """Display what will be added."""
    console.print(f"\n[bold]Adding command '{command}' to {package}[/bold]\n")

    table = Table(show_header=True)
    table.add_column("Version", style="cyan")
    table.add_column("Bin Directory", style="dim")

    for version in versions:
        package_dir = bin_path / f"{package}__{version}"
        table.add_row(version, str(package_dir))

    console.print(table)


def _display_results(
    package: str,
    command: str,
    results: list[tuple[str, bool, str | None]],
    force: bool,
) -> None:
    """Display results of adding command."""
    console.print("\n[bold]Results:[/bold]\n")

    success_count = 0
    skip_count = 0
    error_count = 0

    for version, added, error in results:
        if error:
            console.print(f"  [red]✗[/red] {version}: {error}")
            error_count += 1
        elif added:
            console.print(f"  [green]✓[/green] {version}: Command added")
            success_count += 1
        else:
            console.print(
                f"  [yellow]•[/yellow] {version}: Command already exists (use --force to overwrite)"
            )
            skip_count += 1

    # Summary
    console.print()
    if success_count > 0:
        console.print(
            f"[green]Successfully added command to {success_count} version(s)[/green]"
        )
    if skip_count > 0:
        console.print(
            f"[yellow]Skipped {skip_count} version(s) (already exists)[/yellow]"
        )
    if error_count > 0:
        console.print(f"[red]Failed for {error_count} version(s)[/red]")
