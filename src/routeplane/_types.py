"""Typed models for Routeplane's non-OpenAI endpoints.

:class:`Status` (the model behind ``GET /status``) is the one endpoint that
parses into a dataclass. The other resource namespaces return permissive
``dict`` / ``list[dict]`` payloads straight from the gateway, so a gateway that
grows a field never breaks an older SDK.
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
