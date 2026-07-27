"""Agentic-security MCP namespace (``/v1/mcp/*``).

The gateway gates every route here on the ``AgenticSecurity`` entitlement, and a
tenant without it does not learn the surface exists: the gateway answers **404**
rather than 403. So an ``httpx.HTTPStatusError`` with ``response.status_code ==
404`` on these calls means *"this key is not entitled"* at least as often as it
means *"wrong path"*.

Covers the tool-call authorization gate, tool-result inspection, the run/step
loop, sampling defense, human-in-the-loop approvals, signed receipts, the
anomaly operator surface, and the enforcement-event feed.

Policy verdicts are values, not exceptions. ``authorize_tool_call``,
``inspect_result``, ``sampling_evaluate``, and ``run_step`` return a typed
:class:`Decision` / :class:`RunStep` for both the allow and the deny, because
the gateway is default-deny — a deny is the system working, not an error.
Everything else raises on a non-2xx as usual.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

import httpx

from ._base import BaseResource, prune_none

__all__ = ["McpResource", "Decision", "RunStep"]

# A deny arrives as 422; the per-agent tool-call quota denies with 429 and adds a
# rate-limit envelope. Both are verdicts, so both are returned rather than raised.
_DENY_STATUSES = (422, 429)


@dataclass(frozen=True)
class Decision:
    """An allow/deny verdict from one of the MCP policy gates.

    ``outcome`` is the gateway's own ``"allow"``/``"deny"`` label; ``reason`` is
    a structured, secret-free explanation present only on a deny. The quota
    fields are populated only when a tool call was refused for exceeding the
    agent's per-window ceiling (HTTP 429).
    """

    outcome: str
    reason: Optional[str] = None
    status_code: int = 200
    retry_after_ms: Optional[int] = None
    limit: Optional[int] = None
    window_ms: Optional[int] = None
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def allowed(self) -> bool:
        """``True`` only for an explicit allow."""
        return self.outcome == "allow"

    @classmethod
    def _parse(cls, response: httpx.Response) -> "Decision":
        body: dict[str, Any] = response.json()
        return cls(
            # Absent/unreadable outcome is treated as a deny: this mirrors the
            # gateway's fail-closed posture, so a malformed body can never be
            # read as permission to proceed.
            outcome=body.get("outcome") or "deny",
            reason=body.get("reason"),
            status_code=response.status_code,
            retry_after_ms=body.get("retry_after_ms"),
            limit=body.get("limit"),
            window_ms=body.get("window_ms"),
            raw=body,
        )


@dataclass(frozen=True)
class RunStep:
    """The verdict for one accounted iteration of an agent run.

    ``decision`` is ``"continue"`` or ``"stop"``. On ``stop`` the agent runtime
    must halt the loop — the run has hit its iteration ceiling, its cost budget,
    or its kill switch, and ``reason`` says which.
    """

    decision: str
    iterations: int = 0
    reason: Optional[str] = None
    status_code: int = 200
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def should_continue(self) -> bool:
        """``True`` only for an explicit ``continue``."""
        return self.decision == "continue"

    @classmethod
    def _parse(cls, response: httpx.Response) -> "RunStep":
        body: dict[str, Any] = response.json()
        return cls(
            # Fail-closed, as above: anything that is not an explicit continue
            # stops the loop.
            decision=body.get("decision") or "stop",
            iterations=body.get("iterations") or 0,
            reason=body.get("reason"),
            status_code=response.status_code,
            raw=body,
        )


class _HitlResource:
    """Human-in-the-loop approval queue (``/v1/mcp/hitl/*``).

    Reached as ``client.mcp_security.hitl``; shares the parent's HTTP client.
    Requests are enqueued by the gateway at the enforcement point — operators
    resolve them here, out of band.
    """

    def __init__(self, parent: "McpResource") -> None:
        self._parent = parent

    def approve(self, *, id: str, note: Optional[str] = None) -> dict[str, Any]:
        """``POST /v1/mcp/hitl/approve`` — approve a held high-risk tool call.

        ``note`` is an optional operator label. Raises on 404 (no such request),
        409 (already settled), or 503 (queue full).
        """
        body = prune_none({"id": id, "note": note})
        data: dict[str, Any] = self._parent._post("mcp/hitl/approve", json=body).json()
        return data

    def deny(self, *, id: str, note: Optional[str] = None) -> dict[str, Any]:
        """``POST /v1/mcp/hitl/deny`` — deny a held high-risk tool call."""
        body = prune_none({"id": id, "note": note})
        data: dict[str, Any] = self._parent._post("mcp/hitl/deny", json=body).json()
        return data

    def status(self, *, id: str) -> dict[str, Any]:
        """``GET /v1/mcp/hitl/status/{id}`` — a request's lifecycle status.

        ``status`` is ``pending``/``approved``/``denied``/``expired``, or
        ``unknown`` when no such request is held.
        """
        data: dict[str, Any] = self._parent._get(f"mcp/hitl/status/{id}").json()
        return data

    def pending(self) -> list[dict[str, Any]]:
        """``GET /v1/mcp/hitl/pending`` — snapshot of awaiting approvals."""
        data: list[dict[str, Any]] = self._parent._get("mcp/hitl/pending").json()
        return data


class _ReceiptsResource:
    """Signed action receipts (``/v1/mcp/receipt/*``).

    Reached as ``client.mcp_security.receipts``.
    """

    def __init__(self, parent: "McpResource") -> None:
        self._parent = parent

    def issue(
        self,
        *,
        run_id: str,
        server: str,
        tool: str,
        decision: str,
        agent_id: Optional[str] = None,
        arguments: Optional[dict[str, Any]] = None,
        result: Optional[str] = None,
    ) -> dict[str, Any]:
        """``POST /v1/mcp/receipt/issue`` — issue a signed, chained receipt.

        ``decision`` is ``allowed``, ``denied``, or ``held``. ``arguments`` is
        reduced to a values-free shape and ``result`` to a SHA-256 digest before
        anything is recorded — neither is stored.

        Raises 503 ``receipts_unavailable`` when no signer is configured; the
        gateway never emits an unsigned receipt.
        """
        body = prune_none(
            {
                "agent_id": agent_id,
                "run_id": run_id,
                "server": server,
                "tool": tool,
                "arguments": arguments,
                "decision": decision,
                "result": result,
            }
        )
        data: dict[str, Any] = self._parent._post("mcp/receipt/issue", json=body).json()
        return data

    def verify(self, receipt: dict[str, Any]) -> dict[str, Any]:
        """``POST /v1/mcp/receipt/verify`` — verify a receipt you hold.

        ``mode`` reports how far verification got: ``signature`` when both the
        chain hash and the signature were checked, ``chain_only`` when the
        signer has no in-process verifier (Key Vault — verify the signature
        offline with the exported public key).
        """
        data: dict[str, Any] = self._parent._post("mcp/receipt/verify", json=receipt).json()
        return data


class _AnomalyResource:
    """Behavioral-anomaly operator surface (``/v1/mcp/anomaly/*``).

    Reached as ``client.mcp_security.anomaly``. An agent caught in a runaway
    tool-call loop is quarantined and denied at the authorization gate until an
    operator clears it.
    """

    def __init__(self, parent: "McpResource") -> None:
        self._parent = parent

    def status(self, *, agent_id: str) -> dict[str, Any]:
        """``GET /v1/mcp/anomaly/status/{agent_id}`` — is the agent quarantined?"""
        data: dict[str, Any] = self._parent._get(f"mcp/anomaly/status/{agent_id}").json()
        return data

    def clear(self, *, agent_id: str) -> dict[str, Any]:
        """``POST /v1/mcp/anomaly/clear`` — lift an agent's quarantine.

        ``cleared`` is ``True`` only if the agent was in fact quarantined.
        """
        data: dict[str, Any] = self._parent._post(
            "mcp/anomaly/clear", json={"agent_id": agent_id}
        ).json()
        return data


class McpResource(BaseResource):
    """The agentic-security MCP gateway surface (the moat; PRD-005)."""

    hitl: _HitlResource
    receipts: _ReceiptsResource
    anomaly: _AnomalyResource

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.hitl = _HitlResource(self)
        self.receipts = _ReceiptsResource(self)
        self.anomaly = _AnomalyResource(self)

    def authorize_tool_call(
        self,
        *,
        server: str,
        tool: str,
        agent_id: Optional[str] = None,
        argument_urls: Optional[list[str]] = None,
        arguments: Optional[dict[str, Any]] = None,
        server_manifest: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> Decision:
        """``POST /v1/mcp/tool-call/authorize`` — the default-deny gate.

        Call this *before* letting an agent invoke a tool. The allow requires
        all of: a registered agent, a grant covering this exact ``(server,
        tool)`` pair, an un-drifted server manifest, every URL clearing the SSRF
        egress guard, and headroom under the agent's tool-call quota.

        ``agent_id`` may be omitted when the gateway key is bound to an agent
        identity — the binding then supplies it, and a *disagreeing* value is
        denied outright rather than trusted.

        ``argument_urls`` lists URLs the call would reach; ``arguments`` is the
        full arguments object, which is walked recursively so a URL buried in a
        nested field is checked too. ``server_manifest`` is required for a
        pinned server — omitting it denies. ``run_id`` correlates this call to a
        run's call graph without affecting the verdict.
        """
        body = prune_none(
            {
                "agent_id": agent_id,
                "server": server,
                "tool": tool,
                "argument_urls": argument_urls,
                "arguments": arguments,
                "server_manifest": server_manifest,
                "run_id": run_id,
            }
        )
        response = self._post("mcp/tool-call/authorize", json=body, expect=_DENY_STATUSES)
        return Decision._parse(response)

    def inspect_result(self, *, content: str) -> Decision:
        """``POST /v1/mcp/tool-result/inspect`` — screen a tool result.

        Call this on the return leg, before the result re-enters the model's
        context. A deny means the result was withheld: it carried a secret, an
        injection directive, regulated data out of region, or a tool-poisoning
        attempt — or it simply exceeded the configured size cap.
        """
        response = self._post(
            "mcp/tool-result/inspect", json={"content": content}, expect=_DENY_STATUSES
        )
        return Decision._parse(response)

    def run_step(
        self,
        *,
        run_id: str,
        agent_id: Optional[str] = None,
        cost_micro_usd: int = 0,
    ) -> RunStep:
        """``POST /v1/mcp/run/step`` — account one iteration against a run.

        Charges one iteration (and optionally ``cost_micro_usd`` of spend)
        against the run's breakers. Halt the agent loop whenever the returned
        ``decision`` is ``"stop"``.

        ``run_id`` is caller-chosen; containment is scoped per tenant *and*
        agent, so two callers picking the same id never share a ceiling.
        ``agent_id`` may be omitted when the key carries an agent binding.
        """
        body = prune_none(
            {"agent_id": agent_id, "run_id": run_id, "cost_micro_usd": cost_micro_usd}
        )
        response = self._post("mcp/run/step", json=body, expect=_DENY_STATUSES)
        return RunStep._parse(response)

    def sampling_evaluate(
        self,
        *,
        server: str,
        prompt: str,
        agent_id: Optional[str] = None,
    ) -> Decision:
        """``POST /v1/mcp/sampling/evaluate`` — screen a server-authored prompt.

        MCP servers may ask to sample on an agent's behalf. That prompt is
        untrusted input: this default-deny gate allows it only if the agent's
        policy grants sampling for ``server``, the server is under its rate
        ceiling, and the prompt itself clears the detector chain.
        """
        body = prune_none({"agent_id": agent_id, "server": server, "prompt": prompt})
        response = self._post("mcp/sampling/evaluate", json=body, expect=_DENY_STATUSES)
        return Decision._parse(response)

    def list_runs(self) -> list[dict[str, Any]]:
        """``GET /v1/mcp/runs`` — recent agent-run summaries, newest first.

        Governance metadata only (id, agent, iterations, accrued cost, status
        and stop reason) from a bounded in-memory ring, so this is a live view
        rather than durable history.
        """
        data: dict[str, Any] = self._get("mcp/runs").json()
        runs: list[dict[str, Any]] = data.get("runs", [])
        return runs

    def security_events(self) -> list[dict[str, Any]]:
        """``GET /v1/mcp/security/events`` — recent enforcement denials.

        Newest-first authorize/egress/quota/result-size/anomaly denials for the
        caller's tenant, from the same bounded in-memory ring as
        :meth:`list_runs`. Labels only — never request content.
        """
        data: dict[str, Any] = self._get("mcp/security/events").json()
        events: list[dict[str, Any]] = data.get("events", [])
        return events
