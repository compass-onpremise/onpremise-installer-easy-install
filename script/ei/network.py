"""Network utilities for easy-install."""

from __future__ import annotations

import ipaddress
import socket
from typing import Optional


def get_primary_ip() -> Optional[str]:
    """Detect primary non-loopback IPv4 address."""

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            addr = sock.getsockname()[0]
            ipaddress.IPv4Address(addr)
            if addr.startswith("127."):
                return None
            return addr
    except Exception:
        return None


def is_valid_domain(domain: str) -> bool:
    if not domain:
        return False
    if len(domain) > 253:
        return False
    labels = domain.split(".")
    if len(labels) < 2:
        return False
    for label in labels:
        if not label or len(label) > 63:
            return False
        if label.startswith("-") or label.endswith("-"):
            return False
    return True
