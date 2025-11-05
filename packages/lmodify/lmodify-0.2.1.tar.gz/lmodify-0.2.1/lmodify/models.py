"""Data models for lmodify package."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class PackageInfo:
    """Information about a package parsed from a Singularity image filename."""

    name: str
    version: str
    build: str | None = None

    def __str__(self) -> str:
        """Return string representation."""
        if self.build:
            return f"{self.name}-{self.version}--{self.build}"
        return f"{self.name}-{self.version}"


@dataclass
class Config:
    """Configuration for lmodify."""

    singularity_default_path: Path
    bin_path: Path
    lmod_path: Path
    author: str = "Your Name"
    email: str = "your.email@example.com"
    organization: str = "Your Organization"

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> "Config":
        """Create Config from dictionary."""
        return cls(
            singularity_default_path=Path(
                data.get("singularity_default_path", "/opt/singularity")
            ),
            bin_path=Path(data.get("bin_path", "/opt/bin")),
            lmod_path=Path(data.get("lmod_path", "/opt/lmod")),
            author=data.get("author", "Your Name"),
            email=data.get("email", "your.email@example.com"),
            organization=data.get("organization", "Your Organization"),
        )


@dataclass
class LmodPackage:
    """Represents an LMOD package with versions."""

    name: str
    versions: list[str] = field(default_factory=list)

    def add_version(self, version: str) -> None:
        """Add a version to this package."""
        if version not in self.versions:
            self.versions.append(version)
            self.versions.sort()

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.name} ({len(self.versions)} versions)"


@dataclass
class PackageCreationParams:
    """Parameters for creating a new package."""

    singularity_image: Path
    package_name: str
    version: str
    commands: list[str]
    lmod_path: Path
    bin_path: Path
    force: bool = False
    dry_run: bool = False

    @property
    def package_dir(self) -> Path:
        """Return the directory name for binaries (package__version)."""
        return Path(f"{self.package_name}__{self.version}")

    @property
    def bin_dir(self) -> Path:
        """Return the full path to the bin directory."""
        return self.bin_path / self.package_dir

    @property
    def lua_dir(self) -> Path:
        """Return the directory for lua files."""
        return self.lmod_path / self.package_name

    @property
    def lua_file(self) -> Path:
        """Return the full path to the lua file."""
        return self.lua_dir / f"{self.version}.lua"
