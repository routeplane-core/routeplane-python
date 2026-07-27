"""Mediating an agent's tool loop through the MCP gateway.

Every route used here needs the ``AgenticSecurity`` entitlement. Without it the
gateway answers 404 rather than 403 — it does not reveal that the surface
exists — so an ``httpx.HTTPStatusError`` for 404 means "not entitled".

    pip install routeplane
    python examples/agentic_security.py
"""

from routeplane import Routeplane

rp = Routeplane(api_key="rp_live_...")
mcp = rp.mcp_security

RUN_ID = "run-2026-07-27-001"
AGENT_ID = "support-agent"

# 1. Account the iteration first. The run carries an iteration ceiling, a cost
#    budget, and a kill switch; a "stop" means halt the loop, not retry it.
step = mcp.run_step(run_id=RUN_ID, agent_id=AGENT_ID, cost_micro_usd=1200)
if not step.should_continue:
    raise SystemExit(f"run halted after {step.iterations} iterations: {step.reason}")

# 2. Authorize the specific tool call. Default-deny: the agent needs a grant for
#    this exact (server, tool) pair, and every URL in the arguments has to clear
#    the SSRF egress guard.
decision = mcp.authorize_tool_call(
    agent_id=AGENT_ID,
    server="filesystem",
    tool="fetch_document",
    arguments={"url": "https://docs.example.test/policy.pdf"},
    run_id=RUN_ID,
)
if not decision.allowed:
    if decision.status_code == 429:
        raise SystemExit(f"quota exhausted, retry in {decision.retry_after_ms}ms")
    raise SystemExit(f"tool call refused: {decision.reason}")

tool_result = "...whatever the MCP server returned..."

# 3. Screen the result before it re-enters the model's context. This is where an
#    indirect prompt injection or a leaked secret gets caught.
verdict = mcp.inspect_result(content=tool_result)
if not verdict.allowed:
    raise SystemExit(f"result withheld: {verdict.reason}")

# 4. Bind the whole action into a signed, chained receipt. Arguments are reduced
#    to a values-free shape and the result to a digest — neither is stored.
receipt = mcp.receipts.issue(
    run_id=RUN_ID,
    agent_id=AGENT_ID,
    server="filesystem",
    tool="fetch_document",
    decision="allowed",
    result=tool_result,
)
print(f"receipt: {receipt}")

# Operator views: what the gateway has been refusing, and what it has been running.
print(f"recent denials: {mcp.security_events()}")
print(f"recent runs: {mcp.list_runs()}")
