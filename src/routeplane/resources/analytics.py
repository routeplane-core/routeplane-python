"""In-process analytics namespace (``/analytics`` — host root, not ``/v1``)."""

from __future__ import annotations

from typing import Any

from ._base import BaseResource

__all__ = ["AnalyticsResource"]


class AnalyticsResource(BaseResource):
    """Recent in-memory usage events and per-provider latency."""

    def events(self) -> list[dict[str, Any]]:
        """``GET /analytics`` — the last recorded usage events (in-memory ring)."""
        data: list[dict[str, Any]] = self._get("/analytics").json()
        return data

    def latency(self) -> dict[str, Any]:
        """``GET /analytics/latency`` — per-provider latency summary."""
        data: dict[str, Any] = self._get("/analytics/latency").json()
        return data
