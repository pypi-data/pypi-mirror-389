"""Parser for Singularity image filenames."""

import re
from pathlib import Path

from .models import PackageInfo


class ParseError(Exception):
    """Raised when unable to parse package information from filename."""

    pass


def parse_image_filename(image_path: Path) -> PackageInfo:
    """
    Parse package information from Singularity image filename.

    Supports three patterns:
    1. depot.galaxyproject.org-singularity-{name}-{version}--{build}...
    2. {name}:{version}--{build}
    3. {name}__{version}[.extension]

    Args:
        image_path: Path to the Singularity image file

    Returns:
        PackageInfo object with parsed information

    Raises:
        ParseError: If unable to parse the filename
    """
    # Get basename and strip known Singularity extensions
    basename = image_path.name

    # Strip known Singularity extensions for pattern matching
    # Only strip if it ends with a recognized extension
    known_extensions = (".img", ".sif", ".simg")
    stem = basename
    for ext in known_extensions:
        if basename.endswith(ext):
            stem = basename[: -len(ext)]
            break

    # Pattern 1: depot.galaxyproject.org-singularity-{name}-{version}--{build}
    depot_pattern = r"^depot\.galaxyproject\.org-singularity-([^-]+)-([^-]+)--(.+?)(?:\.img|\.sif|\.simg)?$"
    match = re.match(depot_pattern, basename)
    if match:
        name, version, build = match.groups()
        return PackageInfo(name=name, version=version, build=build)

    # Pattern 2: {name}:{version}--{build}
    colon_pattern = r"^([^:]+):([^-]+)--(.+?)(?:\.img|\.sif|\.simg)?$"
    match = re.match(colon_pattern, basename)
    if match:
        name, version, build = match.groups()
        return PackageInfo(name=name, version=version, build=build)

    # Pattern 3: {name}__{version}
    double_underscore_pattern = r"^([^_]+)__(.+)$"
    match = re.match(double_underscore_pattern, stem)
    if match:
        name, version = match.groups()
        return PackageInfo(name=name, version=version)

    # If none matched, raise error
    raise ParseError(
        f"Unable to parse package information from '{basename}'. "
        "Expected one of these patterns:\n"
        "  1. depot.galaxyproject.org-singularity-{name}-{version}--{build}\n"
        "  2. {name}:{version}--{build}\n"
        "  3. {name}__{version}\n"
        "Please provide --package and --version explicitly."
    )


def parse_package_name_version(image_path: Path) -> tuple[str, str]:
    """
    Parse package name and version from image filename.

    Returns:
        Tuple of (name, version)

    Raises:
        ParseError: If unable to parse the filename
    """
    info = parse_image_filename(image_path)
    return info.name, info.version
