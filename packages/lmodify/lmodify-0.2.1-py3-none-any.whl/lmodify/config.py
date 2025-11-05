"""Configuration file handling for lmodify."""

import configparser
from pathlib import Path

from .models import Config


class ConfigError(Exception):
    """Raised when there's an issue with configuration."""

    pass


DEFAULT_CONFIG_PATH = Path.home() / ".config" / "lmodify.ini"

DEFAULT_CONFIG_CONTENT = """[lmodify]
# Default path to singularity images (to automate search)
singularity_default_path = /opt/singularity

# BIN_PATH: Where to place the exposed links
bin_path = /opt/bin

# LMOD_PATH: Where to store LMOD files (as ./{package}/{version}.lua)
lmod_path = /opt/lmod

[metadata]
# Your information for generated files
author = Your Name
email = your.email@example.com
organization = Your Organization
"""


def get_default_config_path() -> Path:
    """Return the default configuration file path."""
    return DEFAULT_CONFIG_PATH


def load_config(config_path: Path | None = None) -> Config:
    """
    Load configuration from INI file.

    Args:
        config_path: Path to config file. If None, uses default location.

    Returns:
        Config object

    Raises:
        ConfigError: If config file doesn't exist or is invalid
    """
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH

    if not config_path.exists():
        raise ConfigError(
            f"Configuration file not found: {config_path}\n"
            f"Run 'lmodify init' to create a configuration file."
        )

    parser = configparser.ConfigParser()
    try:
        parser.read(config_path)
    except configparser.Error as e:
        raise ConfigError(f"Invalid configuration file: {e}") from e

    # Build config dictionary
    config_dict = {}

    # Read [lmodify] section
    if "lmodify" in parser:
        config_dict.update(dict(parser["lmodify"]))

    # Read [metadata] section
    if "metadata" in parser:
        config_dict.update(dict(parser["metadata"]))

    try:
        return Config.from_dict(config_dict)
    except (KeyError, ValueError) as e:
        raise ConfigError(f"Invalid configuration: {e}") from e


def create_default_config(
    config_path: Path | None = None,
    values: dict[str, str] | None = None,
) -> None:
    """
    Create a default configuration file.

    Args:
        config_path: Path where to create the config file. If None, uses default.
        values: Optional dictionary of values to override defaults

    Raises:
        ConfigError: If unable to create config file
    """
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH

    # Create parent directory if it doesn't exist
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Create parser with defaults
    parser = configparser.ConfigParser()
    parser.read_string(DEFAULT_CONFIG_CONTENT)

    # Override with provided values
    if values:
        for key, value in values.items():
            # Determine which section the key belongs to
            if key in ["author", "email", "organization"]:
                section = "metadata"
            else:
                section = "lmodify"

            if section not in parser:
                parser.add_section(section)

            parser.set(section, key, value)

    # Write to file
    try:
        with open(config_path, "w") as f:
            parser.write(f)
    except OSError as e:
        raise ConfigError(f"Unable to create config file: {e}") from e


def config_exists(config_path: Path | None = None) -> bool:
    """Check if configuration file exists."""
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH
    return config_path.exists()
