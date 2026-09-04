"""Adversarial tests for the outbound-URL guard.

An MCP endpoint is a URL an operator types in and this server then requests on
their behalf, with their configured bearer token attached. Every case here is
something that turns that into a way to read the inside of the deployment.
"""

from __future__ import annotations

import socket

import pytest

from app.core.config import settings
from app.integrations.url_guard import UnsafeURLError, validate_outbound_url


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "gopher://example.com/",
        "ftp://example.com/",
        "javascript:alert(1)",
        "//example.com/no-scheme",
    ],
)
def test_only_http_and_https_are_accepted(url: str) -> None:
    with pytest.raises(UnsafeURLError):
        validate_outbound_url(url)


@pytest.mark.parametrize(
    "url",
    [
        # Cloud instance metadata — the single highest-value SSRF target in any
        # hosted deployment, and reachable from every one of them.
        "http://169.254.169.254/latest/meta-data/iam/security-credentials/",
        "http://[fe80::1]/",
        # Private ranges: other services inside the same network.
        "http://10.0.0.5/admin",
        "http://172.16.4.1/",
        "http://192.168.1.1/",
        # Unique-local IPv6 and the IPv4-mapped form of a private address.
        "http://[fd00::1]/",
        "http://[::ffff:10.0.0.1]/",
    ],
)
def test_addresses_that_are_not_publicly_routable_are_refused(url: str) -> None:
    with pytest.raises(UnsafeURLError):
        validate_outbound_url(url)


def test_credentials_in_the_url_are_refused() -> None:
    # These would be persisted with the endpoint and echoed back in the
    # connector UI — a credential leak wearing a hostname.
    with pytest.raises(UnsafeURLError, match="Credentials"):
        validate_outbound_url("https://user:token@example.com/rpc")


def test_a_hostname_resolving_to_a_private_address_is_refused(monkeypatch) -> None:
    """The check must follow DNS, not trust the name.

    `metadata.totally-normal.example.com` pointing at 169.254.169.254 is the
    standard way an SSRF filter that only pattern-matches hostnames is defeated.
    """

    def fake_getaddrinfo(host, *args, **kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("169.254.169.254", 0))]

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
    with pytest.raises(UnsafeURLError, match="not publicly routable"):
        validate_outbound_url("https://totally-normal.example.com/rpc")


def test_one_public_address_does_not_excuse_a_private_one(monkeypatch) -> None:
    # A host answering with both must be refused, not accepted on the strength
    # of whichever address happens to be checked first.
    def fake_getaddrinfo(host, *args, **kwargs):
        return [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 0)),
        ]

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
    monkeypatch.setattr(settings, "app_env", "production")
    with pytest.raises(UnsafeURLError):
        validate_outbound_url("https://mixed.example.com/rpc")


def test_loopback_is_allowed_in_development_and_refused_in_production(monkeypatch) -> None:
    # Developing against a local MCP server is ordinary; a guard that makes it
    # impossible gets switched off rather than fixed. Production is where the
    # loophole would matter, and there it is closed.
    monkeypatch.setattr(settings, "app_env", "development")
    assert validate_outbound_url("http://127.0.0.1:8000/rpc")

    monkeypatch.setattr(settings, "app_env", "production")
    with pytest.raises(UnsafeURLError):
        validate_outbound_url("http://127.0.0.1:8000/rpc")


def test_an_unresolvable_host_is_not_treated_as_unsafe() -> None:
    # Nothing can be requested from a name with no address, so there is no
    # forgery to prevent; refusing here would make a DNS blip look like invalid
    # configuration. The call-time re-check covers it if it starts resolving.
    assert validate_outbound_url("https://mcp.example/rpc")


def test_ordinary_public_endpoints_still_work() -> None:
    assert validate_outbound_url("https://example.com/mcp")
