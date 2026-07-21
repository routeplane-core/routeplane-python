"""Custom-provider namespace (``/v1/providers``)."""

from __future__ import annotations

from typing import Any, Optional

from ._base import BaseResource, prune_none

__all__ = ["ProvidersResource"]


class ProvidersResource(BaseResource):
    """Register and manage custom OpenAI-compatible providers.

    Reached as ``client.rp_providers`` to avoid shadowing any inherited attribute.
    """

    def list(self) -> list[dict[str, Any]]:
        """``GET /v1/providers`` — configured custom providers."""
        data: list[dict[str, Any]] = self._get("providers").json()
        return data

    def create(
        self,
        *,
        name: str,
        base_url: str,
        api_key: Optional[str] = None,
    ) -> dict[str, Any]:
        """``POST /v1/providers`` — register a custom provider."""
        body = prune_none({"name": name, "base_url": base_url, "api_key": api_key})
        data: dict[str, Any] = self._post("providers", json=body).json()
        return data

    def delete(self, name: str) -> None:
        """``DELETE /v1/providers/{name}`` — remove a custom provider."""
        self._delete(f"providers/{name}")
