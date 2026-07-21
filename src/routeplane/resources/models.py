"""Model-catalog namespace (``/v1/models``)."""

from __future__ import annotations

from typing import Any, Optional

from ._base import BaseResource, prune_none

__all__ = ["ModelsResource"]


class ModelsResource(BaseResource):
    """The Routeplane model catalog.

    Distinct from the inherited OpenAI ``client.models`` (which lists the active
    provider's models); reached as ``client.rp_models``.
    """

    def list(self, *, provider: Optional[str] = None) -> list[dict[str, Any]]:
        """``GET /v1/models`` — catalog entries, optionally filtered by ``provider``."""
        params = prune_none({"provider": provider})
        data: list[dict[str, Any]] = self._get("models", params=params).json()
        return data

    def get(self, model_id: str) -> dict[str, Any]:
        """``GET /v1/models/{model_id}`` — one catalog entry."""
        data: dict[str, Any] = self._get(f"models/{model_id}").json()
        return data
