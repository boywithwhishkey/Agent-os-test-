from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken


class OAuthTokenCipher:
    """Authenticated encryption for OAuth access/refresh tokens at rest."""

    def __init__(self, key: str) -> None:
        try:
            self._fernet = Fernet(key.encode("ascii"))
        except (ValueError, UnicodeError) as exc:
            raise ValueError(
                "AGENT_OS_OAUTH_ENCRYPTION_KEY must be a valid Fernet key"
            ) from exc

    def encrypt(self, value: str) -> str:
        if not value:
            raise ValueError("OAuth token cannot be empty")
        return self._fernet.encrypt(value.encode("utf-8")).decode("ascii")

    def decrypt(self, value: str) -> str:
        try:
            return self._fernet.decrypt(value.encode("ascii")).decode("utf-8")
        except (InvalidToken, UnicodeError, ValueError) as exc:
            raise RuntimeError("Stored OAuth token could not be decrypted") from exc
