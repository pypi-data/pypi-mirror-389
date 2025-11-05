"""Singularity wrapper script generation."""

import stat
from pathlib import Path
from string import Template

# Get the template path
TEMPLATE_DIR = Path(__file__).parent / "templates"
SINGULARITY_EXEC_TEMPLATE = TEMPLATE_DIR / "singularity-exec.tmpl"


def generate_wrapper_script(
    singularity_image: Path,
    package_name: str,
    organization: str = "Your Organization",
) -> str:
    """
    Generate the singularity.exec wrapper script content.

    Args:
        singularity_image: Path to the Singularity image
        package_name: Name of the package
        organization: Organization name for the header comment

    Returns:
        Generated script content
    """
    # Read template
    template_content = SINGULARITY_EXEC_TEMPLATE.read_text()
    template = Template(template_content)

    # Substitute values
    script_content = template.substitute(
        singularity_image=str(singularity_image.resolve()),
        package_name=package_name,
        organization=organization,
    )

    return script_content


def create_wrapper_script(
    output_path: Path,
    singularity_image: Path,
    package_name: str,
    organization: str = "Your Organization",
    dry_run: bool = False,
) -> None:
    """
    Create the singularity.exec wrapper script.

    Args:
        output_path: Where to write the script
        singularity_image: Path to the Singularity image
        package_name: Name of the package
        organization: Organization name
        dry_run: If True, don't actually create the file
    """
    script_content = generate_wrapper_script(
        singularity_image, package_name, organization
    )

    if dry_run:
        return

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write script
    output_path.write_text(script_content)

    # Make executable
    current_permissions = output_path.stat().st_mode
    output_path.chmod(current_permissions | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def create_command_symlinks(
    bin_dir: Path,
    commands: list[str],
    dry_run: bool = False,
) -> None:
    """
    Create symlinks for commands pointing to singularity.exec.

    Args:
        bin_dir: Directory containing singularity.exec
        commands: List of command names to create symlinks for
        dry_run: If True, don't actually create symlinks
    """
    wrapper_script = bin_dir / "singularity.exec"

    if not dry_run and not wrapper_script.exists():
        raise FileNotFoundError(
            f"Wrapper script not found: {wrapper_script}. "
            "Create it first with create_wrapper_script()."
        )

    for command in commands:
        symlink_path = bin_dir / command

        if dry_run:
            continue

        # Remove existing symlink if it exists
        if symlink_path.exists() or symlink_path.is_symlink():
            symlink_path.unlink()

        # Create relative symlink
        symlink_path.symlink_to("singularity.exec")


def add_command_symlink(
    bin_dir: Path,
    command: str,
    force: bool = False,
    dry_run: bool = False,
) -> bool:
    """
    Add a single command symlink.

    Args:
        bin_dir: Directory containing singularity.exec
        command: Command name to add
        force: If True, overwrite existing symlink
        dry_run: If True, don't actually create the symlink

    Returns:
        True if symlink was created (or would be in dry_run), False otherwise
    """
    wrapper_script = bin_dir / "singularity.exec"
    symlink_path = bin_dir / command

    if not dry_run and not wrapper_script.exists():
        raise FileNotFoundError(
            f"Wrapper script not found: {wrapper_script}. "
            "Package directory may not exist or be incomplete."
        )

    # Check if symlink already exists
    if symlink_path.exists() or symlink_path.is_symlink():
        if not force:
            return False

        if not dry_run:
            symlink_path.unlink()

    if not dry_run:
        symlink_path.symlink_to("singularity.exec")

    return True
