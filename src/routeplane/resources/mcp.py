"""Agentic-security MCP namespace (``/v1/mcp/*``).

Gated behind ``Feature::AgenticSecurity`` on the gateway: calls fail if the key
lacks the entitlement. Covers the run/step loop, per-call tool authorization,
tool-result inspection, and the human-in-the-loop legs.
"""

from __future__ import annotations

from typing import Any, Optional

from ._base import BaseResource, prune_none

__all__ = ["McpResource"]


class _HitlResource:
    """Human-in-the-loop legs (``/v1/mcp/hitl/*``).

    Reached as ``client.mcp_security.hitl``; shares the parent's HTTP client.
    """

    def __init__(self, parent: "McpResource") -> None:
        self._parent = parent

    def approve(self, *, decision_id: str) -> dict[str, Any]:
        """``POST /v1/mcp/hitl/approve`` — approve a paused tool call."""
        data: dict[str, Any] = self._parent._post(
            "mcp/hitl/approve", json={"decision_id": decision_id}
        ).json()
        return data

    def deny(self, *, decision_id: str, reason: Optional[str] = None) -> dict[str, Any]:
        """``POST /v1/mcp/hitl/deny`` — deny a paused tool call."""
        body = prune_none({"decision_id": decision_id, "reason": reason})
        data: dict[str, Any] = self._parent._post("mcp/hitl/deny", json=body).json()
        return data

    def status(self, *, decision_id: str) -> dict[str, Any]:
        """``GET /v1/mcp/hitl/status/{decision_id}`` — a decision's current state."""
        data: dict[str, Any] = self._parent._get(
            f"mcp/hitl/status/{decision_id}"
        ).json()
        return data

    def pending(self) -> list[dict[str, Any]]:
        """``GET /v1/mcp/hitl/pending`` — decisions awaiting a human verdict."""
        data: list[dict[str, Any]] = self._parent._get("mcp/hitl/pending").json()
        return data


class McpResource(BaseResource):
    """The agentic-security MCP gateway surface (the moat; PRD-005)."""

    hitl: _HitlResource

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.hitl = _HitlResource(self)

    def run_step(
        self,
        *,
        agent_id: str,
        tool: str,
        server: Optional[str] = None,
        args: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """``POST /v1/mcp/run/step`` — advance an agent run by one mediated tool call."""
        body = prune_none(
            {"agent_id": agent_id, "tool": tool, "server": server, "args": args}
        )
        data: dict[str, Any] = self._post("mcp/run/step", json=body).json()
        return data

    def list_runs(self) -> list[dict[str, Any]]:
        """``GET /v1/mcp/runs`` — the caller's agent runs."""
        data: list[dict[str, Any]] = self._get("mcp/runs").json()
        return data

    def authorize_tool_call(
        self,
        *,
        agent_id: str,
        tool: str,
        server: str,
    ) -> dict[str, Any]:
        """``POST /v1/mcp/tool-call/authorize`` — default-deny ``(server, tool)`` check."""
        body = {"agent_id": agent_id, "tool": tool, "server": server}
        data: dict[str, Any] = self._post("mcp/tool-call/authorize", json=body).json()
        return data

    def inspect_result(self, *, result: dict[str, Any]) -> dict[str, Any]:
        """``POST /v1/mcp/tool-result/inspect`` — inspect a tool result on the return leg."""
        data: dict[str, Any] = self._post(
            "mcp/tool-result/inspect", json={"result": result}
        ).json()
        return data
