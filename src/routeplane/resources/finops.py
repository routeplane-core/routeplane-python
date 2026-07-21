"""FinOps usage/cost namespace (``/v1/finops/*``)."""

from __future__ import annotations

from typing import Any, Optional

from ._base import BaseResource, prune_none

__all__ = ["FinopsResource"]


class FinopsResource(BaseResource):
    """Usage rollups, cost time-series, and cost-saver metrics."""

    def usage(self) -> dict[str, Any]:
        """``GET /v1/finops/usage`` — the durable usage summary."""
        data: dict[str, Any] = self._get("finops/usage").json()
        return data

    def usage_daily(
        self,
        *,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """``GET /v1/finops/usage/daily`` — daily usage rollups over a date range."""
        params = prune_none({"from": from_date, "to": to_date})
        data: list[dict[str, Any]] = self._get("finops/usage/daily", params=params).json()
        return data

    def timeseries(
        self,
        *,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> dict[str, Any]:
        """``GET /v1/finops/timeseries`` — cost/usage time-series."""
        params = prune_none({"from": from_date, "to": to_date})
        data: dict[str, Any] = self._get("finops/timeseries", params=params).json()
        return data

    def cache_savings(self) -> dict[str, Any]:
        """``GET /v1/finops/cache-savings`` — spend avoided by the response cache."""
        data: dict[str, Any] = self._get("finops/cache-savings").json()
        return data

    def saver_metrics(self) -> dict[str, Any]:
        """``GET /v1/finops/saver-metrics`` — difficulty-router / downgrade savings."""
        data: dict[str, Any] = self._get("finops/saver-metrics").json()
        return data
