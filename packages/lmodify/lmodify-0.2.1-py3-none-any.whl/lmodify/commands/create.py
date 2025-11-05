"""Create command - Create new LMOD package from Singularity image."""

from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..config import ConfigError, load_config
from ..lmod import create_lua_file
from ..models import PackageCreationParams
from ..parser import ParseError, parse_package_name_version
from ..singularity import create_command_symlinks, create_wrapper_script

console = Console()


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.argument("commands", nargs=-1)
@click.option(
    "-s",
    "--singularity",
    "singularity_image",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to the Singularity image file",
)
@click.option(
    "-p",
    "--package",
    "package_name",
    help="Package name (auto-detected from image if not provided)",
)
@click.option(
    "-v",
    "--version",
    "version",
    help="Package version (auto-detected from image if not provided)",
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
    "-d",
    "--description",
    default="Bioinformatics tool",
    help="Package description for Lua file",
)
@click.option(
    "-C",
    "--category",
    default="bio",
    help="Package category (bio, chem, physics, tools, etc.)",
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite existing files",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be done without making changes",
)
@click.pass_context
def create(
    ctx: click.Context,
    commands: tuple[str, ...],
    singularity_image: Path,
    package_name: str | None,
    version: str | None,
    lmod_path: Path | None,
    bin_path: Path | None,
    description: str,
    category: str,
    force: bool,
    dry_run: bool,
) -> None:
    """
    Create a new LMOD package from a Singularity image.

    COMMANDS: One or more binaries to expose. If not provided, uses package name.

    Example:
        lmodify create -s image.sif command1 command2
    """
    # Load config
    config_path = ctx.obj.get("config_path")
    try:
        config = load_config(config_path)
    except ConfigError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()

    # Validate image exists
    if not singularity_image.exists():
        console.print(
            f"[red]Error:[/red] Singularity image not found: {singularity_image}"
        )
        raise click.Abort()

    # Parse or validate package name and version
    if package_name is None or version is None:
        try:
            parsed_name, parsed_version = parse_package_name_version(singularity_image)
            if package_name is None:
                package_name = parsed_name
            if version is None:
                version = parsed_version
            console.print(f"[dim]Auto-detected: {package_name} version {version}[/dim]")
        except ParseError as e:
            console.print(f"[red]Error:[/red] {e}")
            raise click.Abort()

    # Use config paths if not overridden
    if lmod_path is None:
        lmod_path = config.lmod_path
    if bin_path is None:
        bin_path = config.bin_path

    # If no commands specified, use package name
    if not commands:
        commands = (package_name,)

    # Create params object
    params = PackageCreationParams(
        singularity_image=singularity_image,
        package_name=package_name,
        version=version,
        commands=list(commands),
        lmod_path=lmod_path,
        bin_path=bin_path,
        force=force,
        dry_run=dry_run,
    )

    # Display what will be created
    _display_creation_plan(params, description, category)

    # Check for existing files
    if not force and not dry_run:
        existing_files = _check_existing_files(params)
        if existing_files:
            console.print("\n[red]Error:[/red] The following files already exist:")
            for file in existing_files:
                console.print(f"  - {file}")
            console.print("\nUse --force to overwrite or --dry-run to preview.")
            raise click.Abort()

    if dry_run:
        console.print("\n[yellow]Dry run - no changes made[/yellow]")
        return

    # Create the package
    try:
        _create_package(params, config.organization, description, category)
        console.print("\n[green]Package created successfully![/green]")
        console.print("\nTo use the module, run:")
        console.print(f"  [cyan]module load {package_name}/{version}[/cyan]")
        console.print("\nRemember to remove cache with")
        console.print("   rm ~/.cache/lmod/*")
        console.print("or use ")
        console.print(f"    module --ignore_cache avail {package_name}")
    except Exception as e:
        console.print(f"\n[red]Error creating package:[/red] {e}")
        raise click.Abort()


def _display_creation_plan(
    params: PackageCreationParams,
    description: str,
    category: str,
) -> None:
    """Display what will be created."""
    console.print(Panel.fit("[bold]Package Creation Plan[/bold]"))

    table = Table(show_header=False, box=None)
    table.add_column("Field", style="cyan")
    table.add_column("Value")

    table.add_row("Package", params.package_name)
    table.add_row("Version", params.version)
    table.add_row("Image", str(params.singularity_image))
    table.add_row("Commands", ", ".join(params.commands))
    table.add_row("Description", description)
    table.add_row("Category", category)
    table.add_row("Bin directory", str(params.bin_dir))
    table.add_row("Lua file", str(params.lua_file))

    console.print(table)


def _check_existing_files(params: PackageCreationParams) -> list[Path]:
    """Check which files already exist."""
    existing = []

    if params.bin_dir.exists():
        existing.append(params.bin_dir)

    if params.lua_file.exists():
        existing.append(params.lua_file)

    return existing


def _create_package(
    params: PackageCreationParams,
    organization: str,
    description: str,
    category: str,
) -> None:
    """Create all package files."""
    # 1. Create bin directory
    params.bin_dir.mkdir(parents=True, exist_ok=True)

    # 2. Create singularity.exec wrapper
    wrapper_path = params.bin_dir / "singularity.exec"
    create_wrapper_script(
        output_path=wrapper_path,
        singularity_image=params.singularity_image,
        package_name=params.package_name,
        organization=organization,
        dry_run=params.dry_run,
    )

    # 3. Create command symlinks
    create_command_symlinks(
        bin_dir=params.bin_dir,
        commands=params.commands,
        dry_run=params.dry_run,
    )

    # 4. Create Lua file
    create_lua_file(
        lua_file_path=params.lua_file,
        package_name=params.package_name,
        version=params.version,
        singularity_image=params.singularity_image,
        bin_dir=params.bin_dir,
        commands=params.commands,
        description=description,
        category=category,
        dry_run=params.dry_run,
    )
