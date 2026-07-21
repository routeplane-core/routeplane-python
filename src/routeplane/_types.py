"""Typed models for Routeplane's non-OpenAI endpoints.

Phase 1 ships only :class:`Status` (the model behind ``GET /status``). The
remaining resource models (prompts, logs, finops, cache, feedback, mcp,
residency) land in Phase 5 — see ``resources/`` for the matching stubs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

__all__ = ["Status"]


@dataclass(frozen=True)
class Status:
    """Response of ``GET /status`` — gateway liveness/build metadata.

    Fields mirror the gateway's status payload but stay permissive: unknown keys
    are preserved in :attr:`raw` so a gateway that grows a field does not break
    older SDKs.
    """

    status: Optional[str] = None
    version: Optional[str] = None
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Status":
        return cls(
            status=data.get("status"),
            version=data.get("version"),
            raw=dict(data),
        )
