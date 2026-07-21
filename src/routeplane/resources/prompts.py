"""Prompt-management namespace (``/v1/prompts/*``). Phase 5 stub."""

from __future__ import annotations

from ._base import BaseResource

__all__ = ["PromptsResource"]


class PromptsResource(BaseResource):
    """Access to ``GET /v1/prompts/{ref}``, render, and completions.

    Not yet implemented — lands in Phase 5.
    """

    def retrieve(self, reference: str) -> object:
        raise NotImplementedError("PromptsResource lands in Phase 5")

    def render(self, reference: str, variables: dict[str, object] | None = None) -> object:
        raise NotImplementedError("PromptsResource lands in Phase 5")
