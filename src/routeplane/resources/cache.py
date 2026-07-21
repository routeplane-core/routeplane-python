"""Cache-control namespace (``POST /v1/cache/purge``). Phase 5 stub."""

from __future__ import annotations

from ._base import BaseResource

__all__ = ["CacheResource"]


class CacheResource(BaseResource):
    """Access to ``POST /v1/cache/purge``. Not yet implemented — lands in Phase 5."""

    def purge(self, **body: object) -> object:
        raise NotImplementedError("CacheResource lands in Phase 5")
