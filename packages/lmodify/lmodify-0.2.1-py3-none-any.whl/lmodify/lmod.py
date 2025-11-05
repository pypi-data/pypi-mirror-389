"""LMOD Lua file generation."""

from pathlib import Path
from string import Template

from .models import LmodPackage

# Get the template path
TEMPLATE_DIR = Path(__file__).parent / "templates"
PACKAGE_LUA_TEMPLATE = TEMPLATE_DIR / "package-lua.tmpl"


def generate_lua_file(
    package_name: str,
    version: str,
    singularity_image: Path,
    bin_dir: Path,
    commands: list[str],
    description: str = "Bioinformatics tool",
    category: str = "bio",
) -> str:
    """
    Generate LMOD Lua file content.

    Args:
        package_name: Name of the package
        version: Package version
        singularity_image: Path to Singularity image
        bin_dir: Path to directory with binaries
        commands: List of available commands
        description: Package description
        category: Package category (bio, chem, physics, tools, etc.)

    Returns:
        Generated Lua file content
    """
    # Read template
    template_content = PACKAGE_LUA_TEMPLATE.read_text()
    template = Template(template_content)

    # Format commands list for help text
    commands_list = "\n".join(f"  - {cmd}" for cmd in commands)

    # Main command (first in list or package name)
    main_command = commands[0] if commands else package_name

    # Package name in uppercase for environment variables
    package_name_upper = package_name.upper().replace("-", "_")

    # Substitute values
    lua_content = template.substitute(
        package_name=package_name,
        version=version,
        singularity_image=str(singularity_image.resolve()),
        bin_dir=str(bin_dir.resolve()),
        commands_list=commands_list,
        main_command=main_command,
        description=description,
        category=category,
        package_name_upper=package_name_upper,
    )

    return lua_content


def create_lua_file(
    lua_file_path: Path,
    package_name: str,
    version: str,
    singularity_image: Path,
    bin_dir: Path,
    commands: list[str],
    description: str = "Bioinformatics tool",
    category: str = "bio",
    dry_run: bool = False,
) -> None:
    """
    Create LMOD Lua file.

    Args:
        lua_file_path: Where to write the Lua file
        package_name: Name of the package
        version: Package version
        singularity_image: Path to Singularity image
        bin_dir: Path to directory with binaries
        commands: List of available commands
        description: Package description
        category: Package category
        dry_run: If True, don't actually create the file
    """
    lua_content = generate_lua_file(
        package_name=package_name,
        version=version,
        singularity_image=singularity_image,
        bin_dir=bin_dir,
        commands=commands,
        description=description,
        category=category,
    )

    if dry_run:
        return

    # Ensure parent directory exists
    lua_file_path.parent.mkdir(parents=True, exist_ok=True)

    # Write Lua file
    lua_file_path.write_text(lua_content)


def list_packages(lmod_path: Path) -> list[LmodPackage]:
    """
    List all packages available in LMOD path.

    Args:
        lmod_path: Path to LMOD directory

    Returns:
        List of LmodPackage objects
    """
    if not lmod_path.exists():
        return []

    packages: dict[str, LmodPackage] = {}

    # Iterate through package directories
    for package_dir in lmod_path.iterdir():
        if not package_dir.is_dir():
            continue

        package_name = package_dir.name

        # Find all .lua files (versions)
        lua_files = list(package_dir.glob("*.lua"))

        if lua_files:
            package = LmodPackage(name=package_name)

            for lua_file in lua_files:
                # Version is the filename without .lua extension
                version = lua_file.stem
                package.add_version(version)

            packages[package_name] = package

    # Return sorted by package name
    return sorted(packages.values(), key=lambda p: p.name)


def find_package_versions(lmod_path: Path, package_name: str) -> list[str]:
    """
    Find all versions of a specific package.

    Args:
        lmod_path: Path to LMOD directory
        package_name: Name of the package to search for

    Returns:
        List of version strings
    """
    package_dir = lmod_path / package_name

    if not package_dir.exists() or not package_dir.is_dir():
        return []

    versions = []
    for lua_file in package_dir.glob("*.lua"):
        versions.append(lua_file.stem)

    return sorted(versions)
