"""Tests for config module."""

from pathlib import Path

import pytest

from lmodify.config import (
    ConfigError,
    config_exists,
    create_default_config,
    load_config,
)


class TestConfigCreation:
    """Tests for config file creation."""

    def test_create_default_config(self, tmp_path):
        """Test creating default config file."""
        config_path = tmp_path / "test_config.ini"

        create_default_config(config_path)

        assert config_path.exists()
        content = config_path.read_text()
        assert "[lmodify]" in content
        assert "[metadata]" in content
        assert "singularity_default_path" in content

    def test_create_config_with_custom_values(self, tmp_path):
        """Test creating config with custom values."""
        config_path = tmp_path / "test_config.ini"
        values = {
            "singularity_default_path": "/custom/path",
            "author": "Test Author",
            "email": "test@example.com",
        }

        create_default_config(config_path, values)

        content = config_path.read_text()
        assert "/custom/path" in content
        assert "Test Author" in content
        assert "test@example.com" in content

    def test_config_exists(self, tmp_path):
        """Test config_exists function."""
        config_path = tmp_path / "test_config.ini"

        assert not config_exists(config_path)

        create_default_config(config_path)

        assert config_exists(config_path)


class TestConfigLoading:
    """Tests for loading config files."""

    def test_load_config(self, tmp_path):
        """Test loading a valid config file."""
        config_path = tmp_path / "test_config.ini"
        create_default_config(config_path)

        config = load_config(config_path)

        assert config.singularity_default_path == Path("/opt/singularity")
        assert config.bin_path == Path("/opt/bin")
        assert config.lmod_path == Path("/opt/lmod")

    def test_load_config_missing_file(self, tmp_path):
        """Test loading non-existent config raises error."""
        config_path = tmp_path / "missing.ini"

        with pytest.raises(ConfigError) as exc_info:
            load_config(config_path)

        assert "not found" in str(exc_info.value)
        assert "lmodify init" in str(exc_info.value)

    def test_load_config_with_custom_values(self, tmp_path):
        """Test loading config with custom values."""
        config_path = tmp_path / "test_config.ini"
        values = {
            "singularity_default_path": "/my/singularity",
            "bin_path": "/my/bin",
            "lmod_path": "/my/lmod",
            "author": "John Doe",
            "email": "john@example.com",
            "organization": "Test Org",
        }

        create_default_config(config_path, values)
        config = load_config(config_path)

        assert config.singularity_default_path == Path("/my/singularity")
        assert config.bin_path == Path("/my/bin")
        assert config.lmod_path == Path("/my/lmod")
        assert config.author == "John Doe"
        assert config.email == "john@example.com"
        assert config.organization == "Test Org"


class TestConfigModel:
    """Tests for Config model."""

    def test_config_from_dict(self):
        """Test creating Config from dictionary."""
        from lmodify.models import Config

        data = {
            "singularity_default_path": "/opt/sing",
            "bin_path": "/opt/bin",
            "lmod_path": "/opt/lmod",
            "author": "Test",
            "email": "test@test.com",
            "organization": "Test Org",
        }

        config = Config.from_dict(data)

        assert config.singularity_default_path == Path("/opt/sing")
        assert config.bin_path == Path("/opt/bin")
        assert config.author == "Test"

    def test_config_from_dict_with_defaults(self):
        """Test Config.from_dict uses defaults for missing values."""
        from lmodify.models import Config

        data = {}
        config = Config.from_dict(data)

        assert config.author == "Your Name"
        assert config.email == "your.email@example.com"
