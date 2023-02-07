import os
import pathlib


class Token:
    """A Cape Personal Access Token (PAT).

    See https://docs.capeprivacy.com/reference/user-tokens for more info.

    Args:
        token: String representing the Personal Access Token.
    """

    def __init__(self, token: str):
        self._token = token

    @property
    def token(self):
        return self._token

    @property
    def raw(self):
        return self._token

    def to_disk(self, location: os.PathLike):
        """Write the PAT to ``location``."""
        with open(location, "w") as f:
            f.write(self.token)

    @classmethod
    def from_disk(cls, location: os.PathLike):
        """Load a PAT from ``location``."""
        location = pathlib.Path(location)
        if not location.exists():
            raise ValueError(f"Token file not found at {str(location)}.")
        with open(location, "r") as f:
            token = f.read()
        return cls(token)
