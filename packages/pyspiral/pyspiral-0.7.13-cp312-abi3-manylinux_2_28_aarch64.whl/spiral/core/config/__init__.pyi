from spiral.core.authn import Token

class ClientSettings:
    """Client configuration loaded from ~/.spiral.toml and environment variables."""

    @staticmethod
    def load() -> ClientSettings:
        """Load ClientSettings from ~/.spiral.toml and environment variables.

        Configuration priority (highest to lowest):
        1. Environment variables (SPIRAL__*)
        2. Config file (~/.spiral.toml)
        3. Default values
        """
        ...

    @property
    def server_url(self) -> str:
        """The Spiral API endpoint URL."""
        ...

    @property
    def spfs_url(self) -> str:
        """The SpFS endpoint URL."""
        ...

    @property
    def file_format(self) -> str:
        """File format for table storage (vortex or parquet)."""
        ...

    @property
    def token(self) -> Token | None:
        """Authentication token (if provided via SPIRAL__TOKEN)."""
        ...

    @token.setter
    def token(self, token: Token):
        """Set the config's authentication token"""
        ...

    def to_json(self) -> str:
        """Serialize to a JSON string"""
        ...
    @staticmethod
    def from_json(json: str) -> ClientSettings:
        """Deserialize from a JSON-formatted string"""
