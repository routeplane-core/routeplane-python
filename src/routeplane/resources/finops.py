"""FinOps usage namespace (``GET /v1/finops/usage``). Phase 5 stub."""

from __future__ import annotations

from ._base import BaseResource

__all__ = ["FinopsResource"]


class FinopsResource(BaseResource):
    """Access to ``GET /v1/finops/usage``. Not yet implemented — lands in Phase 5."""

    def usage(self, **params: object) -> object:
        raise NotImplementedError("FinopsResource lands in Phase 5")
