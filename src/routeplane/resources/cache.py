"""Cache-control namespace (``POST /v1/cache/purge``)."""

from __future__ import annotations

from ._base import BaseResource

__all__ = ["CacheResource"]


class CacheResource(BaseResource):
    """Manage the exact-match response cache."""

    def purge(self) -> None:
        """``POST /v1/cache/purge`` — evict all cached responses for this key."""
        self._post("cache/purge")
