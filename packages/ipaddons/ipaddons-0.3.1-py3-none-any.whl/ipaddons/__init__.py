from __future__ import annotations

from ._version import __version__, __version_tuple__
from .tools import IPv4Allocation, IPv6Allocation, ip_allocation

__all__ = ["IPv4Allocation", "IPv6Allocation", "ip_allocation"]
