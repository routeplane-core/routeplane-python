"""Request-log namespace (``GET /v1/logs``)."""

from __future__ import annotations

from typing import Any, Optional

from ._base import BaseResource, prune_none

__all__ = ["LogsResource"]


class LogsResource(BaseResource):
    """Read the caller's own recent request logs."""

    def list(self, *, limit: Optional[int] = None) -> list[dict[str, Any]]:
        """``GET /v1/logs`` — recent request-log entries, newest first."""
        params = prune_none({"limit": limit})
        data: list[dict[str, Any]] = self._get("logs", params=params).json()
        return data
