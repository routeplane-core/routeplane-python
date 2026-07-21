"""Sovereign-routing / residency namespace (``/v1/residency/*``)."""

from __future__ import annotations

from typing import Any

from ._base import BaseResource

__all__ = ["ResidencyResource"]


class ResidencyResource(BaseResource):
    """Read this key's own sovereign-routing decisions."""

    def summary(self) -> dict[str, Any]:
        """``GET /v1/residency/summary`` — counts of region-locked routing decisions."""
        data: dict[str, Any] = self._get("residency/summary").json()
        return data

    def ledger(self) -> dict[str, Any]:
        """``GET /v1/residency/ledger`` — the sovereign-decision ledger view."""
        data: dict[str, Any] = self._get("residency/ledger").json()
        return data
