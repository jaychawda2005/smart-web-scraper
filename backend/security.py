"""
security.py
-----------
SSRF protection and URL validation for SmartScrape.

This module validates user-supplied URLs before any HTTP request is made.
It blocks access to private, loopback, link-local, and cloud-metadata
addresses to prevent Server-Side Request Forgery (SSRF) attacks.
"""

import ipaddress
import socket
from urllib.parse import urlparse

# Schemes that are allowed
ALLOWED_SCHEMES = {"http", "https"}

# Hostnames that are always blocked regardless of IP resolution
BLOCKED_HOSTNAMES = {
    "localhost",
    "metadata.google.internal",  # GCP metadata
}

# IP network ranges that must never be fetched
BLOCKED_NETWORKS = [
    # Loopback
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
    # Link-local
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("fe80::/10"),
    # Private / RFC-1918
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    # Unique local (IPv6)
    ipaddress.ip_network("fc00::/7"),
    # Any-address
    ipaddress.ip_network("0.0.0.0/8"),
    # Cloud metadata (AWS / Azure / GCP instance metadata)
    ipaddress.ip_network("169.254.169.254/32"),
    # Multicast
    ipaddress.ip_network("224.0.0.0/4"),
    ipaddress.ip_network("ff00::/8"),
]


def _is_ip_blocked(ip_str: str) -> bool:
    """Return True if the resolved IP address falls inside a blocked range."""
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        # Cannot parse — treat as blocked
        return True

    for network in BLOCKED_NETWORKS:
        if ip in network:
            return True
    return False


def validate_url(url: str) -> tuple[bool, str]:
    """
    Validate a user-supplied URL.

    Returns a tuple of (is_valid, error_message).
    If is_valid is True, error_message will be an empty string.
    """
    # --- Basic checks ---
    if not url or not url.strip():
        return False, "URL must not be empty."

    url = url.strip()

    # Parse URL structure
    try:
        parsed = urlparse(url)
    except Exception:
        return False, "Invalid URL format."

    # Scheme check
    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        return False, (
            f"Unsupported URL scheme '{parsed.scheme}'. "
            "Only http:// and https:// are allowed."
        )

    # Must have a hostname
    hostname = parsed.hostname
    if not hostname:
        return False, "URL must include a valid hostname."

    # Blocked hostnames (case-insensitive)
    if hostname.lower() in BLOCKED_HOSTNAMES:
        return False, "The requested URL is not allowed (blocked hostname)."

    # If it is already an IP literal, check it directly
    try:
        ip_obj = ipaddress.ip_address(hostname)
        if _is_ip_blocked(str(ip_obj)):
            return False, "The requested URL is not allowed (private or reserved IP address)."
        # It is a valid public IP — nothing more to check here
        return True, ""
    except ValueError:
        # Not an IP literal — it is a hostname; resolve it
        pass

    # DNS resolution — check all resolved addresses
    try:
        results = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        return False, f"DNS resolution failed for '{hostname}'. The host does not exist or is unreachable."

    if not results:
        return False, "Could not resolve hostname."

    for result in results:
        # result is a 5-tuple; index 4 is (address, port, ...)
        resolved_ip = result[4][0]
        if _is_ip_blocked(resolved_ip):
            return False, "The requested URL is not allowed (resolves to a private or reserved IP address)."

    return True, ""
