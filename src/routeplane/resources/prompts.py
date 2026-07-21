"""Prompt-management namespace (``/v1/prompts/*``)."""

from __future__ import annotations

from typing import Any, Optional

from ._base import BaseResource, prune_none

__all__ = ["PromptsResource"]


class PromptsResource(BaseResource):
    """Fetch, render, and complete managed prompt templates (PRD-010)."""

    def get(self, reference: str) -> dict[str, Any]:
        """``GET /v1/prompts/{reference}`` — the raw template + metadata."""
        data: dict[str, Any] = self._get(f"prompts/{reference}").json()
        return data

    def render(
        self,
        reference: str,
        *,
        variables: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """``POST /v1/prompts/{reference}/render`` — interpolate ``variables``."""
        body = prune_none({"variables": variables})
        data: dict[str, Any] = self._post(f"prompts/{reference}/render", json=body).json()
        return data

    def complete(
        self,
        reference: str,
        *,
        variables: Optional[dict[str, str]] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> dict[str, Any]:
        """``POST /v1/prompts/{reference}/completions`` — render then route to a model."""
        body = prune_none({"variables": variables, "model": model, "provider": provider})
        data: dict[str, Any] = self._post(f"prompts/{reference}/completions", json=body).json()
        return data
