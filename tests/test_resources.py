"""URL/method/body contract tests for the non-OpenAI resource namespaces.

Each test constructs the resource directly (no OpenAI machinery) and mocks the
gateway with ``respx``, asserting the exact HTTP verb, path, query, and body.
"""

import json

import httpx
import pytest
import respx

from routeplane.resources import (
    AnalyticsResource,
    CacheResource,
    FeedbackResource,
    FinopsResource,
    LogsResource,
    McpResource,
    ModelsResource,
    PromptsResource,
    ProvidersResource,
    ResidencyResource,
)

BASE = "https://api.routeplane.ai/v1"
ORIGIN = "https://api.routeplane.ai"


def _kwargs():
    return {"api_key": "rp_test", "base_url": BASE}


def _sent(route):
    return route.calls.last.request


def _body(route):
    return json.loads(_sent(route).content)


# --- prompts ---------------------------------------------------------------


@respx.mock
def test_prompts_get():
    route = respx.get(f"{BASE}/prompts/greeting").mock(
        return_value=httpx.Response(200, json={"reference": "greeting"})
    )
    out = PromptsResource(**_kwargs()).get("greeting")
    assert out == {"reference": "greeting"}
    assert _sent(route).headers["x-routeplane-api-key"] == "rp_test"


@respx.mock
def test_prompts_render():
    route = respx.post(f"{BASE}/prompts/greeting/render").mock(
        return_value=httpx.Response(200, json={"rendered": "hi Sam"})
    )
    out = PromptsResource(**_kwargs()).render("greeting", variables={"name": "Sam"})
    assert out == {"rendered": "hi Sam"}
    assert _body(route) == {"variables": {"name": "Sam"}}


@respx.mock
def test_prompts_complete_prunes_none():
    route = respx.post(f"{BASE}/prompts/greeting/completions").mock(
        return_value=httpx.Response(200, json={"id": "c1"})
    )
    out = PromptsResource(**_kwargs()).complete(
        "greeting", variables={"name": "Sam"}, model="gpt-4o"
    )
    assert out == {"id": "c1"}
    body = _body(route)
    assert body == {"variables": {"name": "Sam"}, "model": "gpt-4o"}
    assert "provider" not in body  # None args never reach the wire


# --- logs ------------------------------------------------------------------


@respx.mock
def test_logs_list_with_limit():
    route = respx.get(f"{BASE}/logs").mock(
        return_value=httpx.Response(200, json=[{"id": "log_1"}])
    )
    out = LogsResource(**_kwargs()).list(limit=5)
    assert out == [{"id": "log_1"}]
    assert _sent(route).url.params["limit"] == "5"


@respx.mock
def test_logs_list_no_params():
    route = respx.get(f"{BASE}/logs").mock(return_value=httpx.Response(200, json=[]))
    LogsResource(**_kwargs()).list()
    assert _sent(route).url.query == b""


# --- finops ----------------------------------------------------------------


@respx.mock
def test_finops_usage():
    respx.get(f"{BASE}/finops/usage").mock(
        return_value=httpx.Response(200, json={"total": 1})
    )
    assert FinopsResource(**_kwargs()).usage() == {"total": 1}


@respx.mock
def test_finops_usage_daily_range():
    route = respx.get(f"{BASE}/finops/usage/daily").mock(
        return_value=httpx.Response(200, json=[{"day": "2026-07-01"}])
    )
    out = FinopsResource(**_kwargs()).usage_daily(
        from_date="2026-07-01", to_date="2026-07-20"
    )
    assert out == [{"day": "2026-07-01"}]
    params = _sent(route).url.params
    assert params["from"] == "2026-07-01"
    assert params["to"] == "2026-07-20"


@respx.mock
def test_finops_timeseries():
    respx.get(f"{BASE}/finops/timeseries").mock(
        return_value=httpx.Response(200, json={"points": []})
    )
    assert FinopsResource(**_kwargs()).timeseries() == {"points": []}


@respx.mock
def test_finops_cache_savings():
    respx.get(f"{BASE}/finops/cache-savings").mock(
        return_value=httpx.Response(200, json={"saved": 3})
    )
    assert FinopsResource(**_kwargs()).cache_savings() == {"saved": 3}


@respx.mock
def test_finops_saver_metrics():
    respx.get(f"{BASE}/finops/saver-metrics").mock(
        return_value=httpx.Response(200, json={"downgrades": 2})
    )
    assert FinopsResource(**_kwargs()).saver_metrics() == {"downgrades": 2}


# --- cache -----------------------------------------------------------------


@respx.mock
def test_cache_purge_returns_none():
    route = respx.post(f"{BASE}/cache/purge").mock(return_value=httpx.Response(204))
    assert CacheResource(**_kwargs()).purge() is None
    assert route.called


# --- feedback --------------------------------------------------------------


@respx.mock
def test_feedback_create_prunes_comment():
    route = respx.post(f"{BASE}/feedback").mock(return_value=httpx.Response(204))
    assert FeedbackResource(**_kwargs()).create(request_id="req_1", score=1.0) is None
    body = _body(route)
    assert body == {"request_id": "req_1", "score": 1.0}
    assert "comment" not in body


@respx.mock
def test_feedback_create_with_comment():
    route = respx.post(f"{BASE}/feedback").mock(return_value=httpx.Response(204))
    FeedbackResource(**_kwargs()).create(request_id="req_1", score=0.0, comment="meh")
    assert _body(route) == {"request_id": "req_1", "score": 0.0, "comment": "meh"}


# --- residency -------------------------------------------------------------


@respx.mock
def test_residency_summary_and_ledger():
    respx.get(f"{BASE}/residency/summary").mock(
        return_value=httpx.Response(200, json={"locked": 4})
    )
    respx.get(f"{BASE}/residency/ledger").mock(
        return_value=httpx.Response(200, json={"entries": []})
    )
    res = ResidencyResource(**_kwargs())
    assert res.summary() == {"locked": 4}
    assert res.ledger() == {"entries": []}


# --- mcp -------------------------------------------------------------------


@respx.mock
def test_mcp_run_step_prunes_none():
    route = respx.post(f"{BASE}/mcp/run/step").mock(
        return_value=httpx.Response(200, json={"run_id": "r1"})
    )
    out = McpResource(**_kwargs()).run_step(agent_id="a1", tool="search")
    assert out == {"run_id": "r1"}
    body = _body(route)
    assert body == {"agent_id": "a1", "tool": "search"}
    assert "server" not in body and "args" not in body


@respx.mock
def test_mcp_list_runs():
    respx.get(f"{BASE}/mcp/runs").mock(
        return_value=httpx.Response(200, json=[{"run_id": "r1"}])
    )
    assert McpResource(**_kwargs()).list_runs() == [{"run_id": "r1"}]


@respx.mock
def test_mcp_authorize_tool_call():
    route = respx.post(f"{BASE}/mcp/tool-call/authorize").mock(
        return_value=httpx.Response(200, json={"allowed": True})
    )
    out = McpResource(**_kwargs()).authorize_tool_call(
        agent_id="a1", tool="fetch", server="files"
    )
    assert out == {"allowed": True}
    assert _body(route) == {"agent_id": "a1", "tool": "fetch", "server": "files"}


@respx.mock
def test_mcp_inspect_result():
    route = respx.post(f"{BASE}/mcp/tool-result/inspect").mock(
        return_value=httpx.Response(200, json={"verdict": "clean"})
    )
    out = McpResource(**_kwargs()).inspect_result(result={"text": "hi"})
    assert out == {"verdict": "clean"}
    assert _body(route) == {"result": {"text": "hi"}}


@respx.mock
def test_mcp_hitl_approve_and_deny():
    approve = respx.post(f"{BASE}/mcp/hitl/approve").mock(
        return_value=httpx.Response(200, json={"state": "approved"})
    )
    deny = respx.post(f"{BASE}/mcp/hitl/deny").mock(
        return_value=httpx.Response(200, json={"state": "denied"})
    )
    mcp = McpResource(**_kwargs())
    assert mcp.hitl.approve(decision_id="d1") == {"state": "approved"}
    assert _body(approve) == {"decision_id": "d1"}
    assert mcp.hitl.deny(decision_id="d1", reason="unsafe") == {"state": "denied"}
    assert _body(deny) == {"decision_id": "d1", "reason": "unsafe"}


@respx.mock
def test_mcp_hitl_deny_prunes_reason():
    deny = respx.post(f"{BASE}/mcp/hitl/deny").mock(
        return_value=httpx.Response(200, json={"state": "denied"})
    )
    McpResource(**_kwargs()).hitl.deny(decision_id="d1")
    assert _body(deny) == {"decision_id": "d1"}


@respx.mock
def test_mcp_hitl_status_and_pending():
    status = respx.get(f"{BASE}/mcp/hitl/status/d1").mock(
        return_value=httpx.Response(200, json={"state": "pending"})
    )
    respx.get(f"{BASE}/mcp/hitl/pending").mock(
        return_value=httpx.Response(200, json=[{"decision_id": "d1"}])
    )
    mcp = McpResource(**_kwargs())
    assert mcp.hitl.status(decision_id="d1") == {"state": "pending"}
    assert status.called
    assert mcp.hitl.pending() == [{"decision_id": "d1"}]


# --- models ----------------------------------------------------------------


@respx.mock
def test_models_list_with_provider():
    route = respx.get(f"{BASE}/models").mock(
        return_value=httpx.Response(200, json=[{"id": "gpt-4o"}])
    )
    out = ModelsResource(**_kwargs()).list(provider="openai")
    assert out == [{"id": "gpt-4o"}]
    assert _sent(route).url.params["provider"] == "openai"


@respx.mock
def test_models_get():
    respx.get(f"{BASE}/models/gpt-4o").mock(
        return_value=httpx.Response(200, json={"id": "gpt-4o"})
    )
    assert ModelsResource(**_kwargs()).get("gpt-4o") == {"id": "gpt-4o"}


# --- analytics (host-root, not /v1) ---------------------------------------


@respx.mock
def test_analytics_events_hits_origin_root():
    route = respx.get(f"{ORIGIN}/analytics").mock(
        return_value=httpx.Response(200, json=[{"event": "usage"}])
    )
    out = AnalyticsResource(**_kwargs()).events()
    assert out == [{"event": "usage"}]
    assert str(_sent(route).url) == f"{ORIGIN}/analytics"


@respx.mock
def test_analytics_latency_hits_origin_root():
    route = respx.get(f"{ORIGIN}/analytics/latency").mock(
        return_value=httpx.Response(200, json={"p50": 12})
    )
    assert AnalyticsResource(**_kwargs()).latency() == {"p50": 12}
    assert str(_sent(route).url) == f"{ORIGIN}/analytics/latency"


# --- providers -------------------------------------------------------------


@respx.mock
def test_providers_list():
    respx.get(f"{BASE}/providers").mock(
        return_value=httpx.Response(200, json=[{"name": "acme"}])
    )
    assert ProvidersResource(**_kwargs()).list() == [{"name": "acme"}]


@respx.mock
def test_providers_create_prunes_none():
    route = respx.post(f"{BASE}/providers").mock(
        return_value=httpx.Response(200, json={"name": "acme"})
    )
    out = ProvidersResource(**_kwargs()).create(
        name="acme", base_url="https://acme.example/v1"
    )
    assert out == {"name": "acme"}
    body = _body(route)
    assert body == {"name": "acme", "base_url": "https://acme.example/v1"}
    assert "api_key" not in body


@respx.mock
def test_providers_delete_returns_none():
    route = respx.delete(f"{BASE}/providers/acme").mock(
        return_value=httpx.Response(204)
    )
    assert ProvidersResource(**_kwargs()).delete("acme") is None
    assert route.called


@respx.mock
def test_resource_raises_on_error():
    respx.get(f"{BASE}/finops/usage").mock(return_value=httpx.Response(500))
    with pytest.raises(httpx.HTTPStatusError):
        FinopsResource(**_kwargs()).usage()
