"""Agentic-security MCP namespace (``/v1/mcp/*``). Phase 5 stub.

Gated behind ``Feature::AgenticSecurity`` on the gateway; the client surface for
the run/step, HITL, and receipt legs lands in Phase 5.
"""

from __future__ import annotations

from ._base import BaseResource

__all__ = ["McpResource"]


class McpResource(BaseResource):
    """Access to the ``/v1/mcp/*`` agentic-security surface.

    Not yet implemented — lands in Phase 5.
    """

    def run_step(self, **body: object) -> object:
        raise NotImplementedError("McpResource lands in Phase 5")

    def runs(self, **params: object) -> object:
        raise NotImplementedError("McpResource lands in Phase 5")
