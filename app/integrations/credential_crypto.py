"""Encryption at rest for stored OAuth credentials.

An access token is the one thing in `oauth_connections` that must never sit
in plaintext: it is a live bearer credential for someone's GitHub, GitLab,
Slack or Notion account, and a database backup, a leaked snapshot, or a
misconfigured read replica would otherwise hand it over directly.

Symmetric encryption (Fernet — AES-128-CBC + HMAC, authenticated) keyed by
`AGENT_OS_CREDENTIAL_ENCRYPTION_KEY` is deliberately the whole design here:
there is exactly one deployment-wide secret, generated once
(`Fernet.generate_key()`), configured the same way every other required
secret in this codebase is (an environment variable, never checked into Git
or PROJECT_BRAIN — see CLAUDE.md section 7). This is not the "convenience"
CLAUDE.md's secret-management rule forbids: an encryption key IS the standard
way to hand a service its own key. What that rule forbids is putting a
*credential this key protects* directly into an env var instead.

Failing loudly beats failing open: a missing or wrong key raises rather than
falling back to plaintext or returning a token that silently doesn't work.
"""

from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


class CredentialEncryptionUnavailable(RuntimeError):
    """The encryption key is missing, malformed, or does not match what a
    stored value was encrypted with."""


def _fernet() -> Fernet:
    key = settings.credential_encryption_key.strip()
    if not key:
        raise CredentialEncryptionUnavailable(
            "AGENT_OS_CREDENTIAL_ENCRYPTION_KEY is not set. Generate one with: "
            'python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" '
            "and set it before oauth_backend=postgres can store or read a credential."
        )
    try:
        return Fernet(key.encode())
    except (ValueError, TypeError) as exc:
        raise CredentialEncryptionUnavailable(
            "AGENT_OS_CREDENTIAL_ENCRYPTION_KEY is not a valid Fernet key."
        ) from exc


def encrypt_secret(plaintext: str) -> bytes:
    return _fernet().encrypt(plaintext.encode())


def decrypt_secret(ciphertext: bytes) -> str:
    try:
        return _fernet().decrypt(bytes(ciphertext)).decode()
    except InvalidToken as exc:
        # Either the key changed since this row was written, or the bytes are
        # corrupt. Either way, returning a garbage string that looks like a
        # token would be worse than refusing outright.
        raise CredentialEncryptionUnavailable(
            "Stored credential could not be decrypted — the encryption key does "
            "not match the one it was written with."
        ) from exc
