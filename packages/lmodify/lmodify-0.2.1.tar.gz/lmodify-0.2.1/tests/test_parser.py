"""Tests for parser module."""

from pathlib import Path

import pytest

from lmodify.parser import ParseError, parse_image_filename, parse_package_name_version


class TestParseImageFilename:
    """Tests for parse_image_filename function."""

    def test_depot_galaxyproject_pattern(self):
        """Test parsing depot.galaxyproject.org pattern."""
        path = Path("depot.galaxyproject.org-singularity-kraken2-2.0.8_beta--pl526hc9558a2_2.img")
        result = parse_image_filename(path)

        assert result.name == "kraken2"
        assert result.version == "2.0.8_beta"
        assert result.build == "pl526hc9558a2_2"

    def test_depot_pattern_with_sif(self):
        """Test depot pattern with .sif extension."""
        path = Path("depot.galaxyproject.org-singularity-seqfu-1.16.0--hbd632db_0.sif")
        result = parse_image_filename(path)

        assert result.name == "seqfu"
        assert result.version == "1.16.0"
        assert result.build == "hbd632db_0"

    def test_colon_pattern(self):
        """Test parsing name:version--build pattern."""
        path = Path("checkv:1.0.3--pyhdfd78af_0")
        result = parse_image_filename(path)

        assert result.name == "checkv"
        assert result.version == "1.0.3"
        assert result.build == "pyhdfd78af_0"

    def test_colon_pattern_with_extension(self):
        """Test colon pattern with extension."""
        path = Path("genomad:1.9.0--pyhdfd78af_1.simg")
        result = parse_image_filename(path)

        assert result.name == "genomad"
        assert result.version == "1.9.0"
        assert result.build == "pyhdfd78af_1"

    def test_double_underscore_pattern(self):
        """Test parsing name__version pattern."""
        path = Path("seqfu__1.20.3")
        result = parse_image_filename(path)

        assert result.name == "seqfu"
        assert result.version == "1.20.3"
        assert result.build is None

    def test_double_underscore_with_extension(self):
        """Test double underscore pattern with extension."""
        path = Path("unicycler__0.5.1.simg")
        result = parse_image_filename(path)

        assert result.name == "unicycler"
        assert result.version == "0.5.1"
        assert result.build is None

    def test_double_underscore_multiple_dots(self):
        """Test double underscore with version containing dots."""
        path = Path("visidata__3.1.0.1.sif")
        result = parse_image_filename(path)

        assert result.name == "visidata"
        assert result.version == "3.1.0.1"

    def test_invalid_pattern_raises_error(self):
        """Test that invalid patterns raise ParseError."""
        path = Path("invalid-image-name.sif")

        with pytest.raises(ParseError) as exc_info:
            parse_image_filename(path)

        assert "Unable to parse" in str(exc_info.value)

    def test_parse_package_name_version(self):
        """Test parse_package_name_version helper."""
        path = Path("seqfu__1.20.3.simg")
        name, version = parse_package_name_version(path)

        assert name == "seqfu"
        assert version == "1.20.3"


class TestPackageInfo:
    """Tests for PackageInfo model."""

    def test_str_with_build(self):
        """Test string representation with build."""
        from lmodify.models import PackageInfo

        info = PackageInfo(name="test", version="1.0", build="abc123")
        assert str(info) == "test-1.0--abc123"

    def test_str_without_build(self):
        """Test string representation without build."""
        from lmodify.models import PackageInfo

        info = PackageInfo(name="test", version="1.0")
        assert str(info) == "test-1.0"
