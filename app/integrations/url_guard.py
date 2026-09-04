"""Outbound URL validation for operator-supplied connector endpoints.

An MCP server endpoint (and, later, any custom REST/GraphQL connector) is a URL
somebody types into THYNACT and the server then requests on their behalf. That
is a server-side request forgery primitive unless it is constrained: without
this guard, `http://169.254.169.254/latest/meta-data/iam/security-credentials/`
is a perfectly valid "MCP server", and the response body comes back through the
connector UI. Bearer tokens configured for that "server" are sent to it too.

Two rules:

- **Only http/https.** Anything else (file:, gopher:, ftp:) has no legitimate
  use here and several illegitimate ones.
- **Only addresses that are actually on the public internet.** Every resolved
  address must be global — loopback, private ranges, link-local (which is where
  cloud metadata lives), unique-local, and the reserved blocks are all refused.

Resolution happens here rather than trusting the hostname, because
`metadata.something.example.com` can resolve to 169.254.169.254 just as easily
as a literal. And because DNS can change between the check and the request,
callers validate at configuration time *and* immediately before each call —
that narrows the rebinding window rather than closing it, which is the honest
description of what a guard at this layer can do. Closing it entirely needs
connection-time pinning in the HTTP transport.

Loopback is permitted outside production, and only there: developing against
an MCP server on localhost is normal, and a guard that makes local development
impossible gets disabled rather than fixed.
"""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlsplit

from app.core.config import settings

ALLOWED_SCHEMES = frozenset({"http", "https"})


class UnsafeURLError(ValueError):
    """The URL is not one this server is willing to request.

    The message is shown to the operator who supplied the URL, so it says what
    was rejected and why — but never anything the request itself returned.
    """


def _addresses_for(host: str) -> list[ipaddress.IPv4Address | ipaddress.IPv6Address]:
    """Every address the hostname currently resolves to.

    All of them are checked, not just the first: a host answering with one
    public and one private address must not pass on the strength of the public
    one.

    A hostname that does not resolve yields an empty list rather than an error.
    That is deliberate and it does not weaken the guard: nothing can be
    requested from a name that has no address, so there is no forgery to
    prevent, and refusing here would turn an ordinary DNS blip into "your
    connector configuration is invalid". If the name starts resolving later,
    the call-time check runs before the request goes out.
    """
    try:
        return [ipaddress.ip_address(host)]
    except ValueError:
        pass

    try:
        infos = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        return []

    resolved = []
    for info in infos:
        address = info[4][0]
        try:
            resolved.append(ipaddress.ip_address(address))
        except ValueError:  # pragma: no cover - getaddrinfo returned a non-address
            continue
    return resolved


def _is_permitted(address: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    if address.is_loopback:
        # Only outside production, where pointing at a locally-run MCP server
        # is ordinary development rather than an attempt to reach an internal
        # service.
        return settings.app_env != "production"
    # `is_global` already excludes private, link-local (169.254.0.0/16 and
    # fe80::/10 — where cloud instance metadata lives), unique-local, multicast
    # and the reserved blocks.
    return address.is_global


def validate_outbound_url(url: str) -> str:
    """Return the URL unchanged, or raise UnsafeURLError explaining the refusal."""
    parts = urlsplit(url.strip())

    if parts.scheme.lower() not in ALLOWED_SCHEMES:
        raise UnsafeURLError(
            f"Only http and https URLs are allowed (got {parts.scheme or 'no scheme'})"
        )

    # Credentials in the URL would be written to whatever stores the endpoint
    # and echoed back in the connector UI, which is a credential leak dressed
    # up as a hostname.
    if parts.username or parts.password:
        raise UnsafeURLError("Credentials must not be embedded in the URL")

    host = parts.hostname
    if not host:
        raise UnsafeURLError("URL has no host")

    for address in _addresses_for(host):
        if not _is_permitted(address):
            # Deliberately does not echo the resolved address: for a hostname
            # the operator did not control, that turns the error message into
            # a DNS oracle.
            raise UnsafeURLError(
                f"{host} resolves to an address that is not publicly routable. "
                "Endpoints on loopback, private, link-local or reserved ranges are refused."
            )

    return url.strip()
