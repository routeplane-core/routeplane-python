from unittest.mock import patch

import httpx
import openai
import pytest
import respx

from routeplane import AsyncRouteplane, Routeplane
from routeplane.resources.status import StatusResource


def _capture_openai_init(cls):
    """Patch ``cls.__init__`` to record the kwargs the subclass forwards to it.

    Lets us assert on what ``Routeplane`` passes to ``openai.OpenAI`` without
    standing up a real HTTP client or network.
    """
    captured: dict = {}

    def fake_init(self, **kwargs):
        captured.update(kwargs)

    return captured, patch.object(cls, "__init__", fake_init)


def test_client_sets_auth_and_routing_headers():
    captured, patcher = _capture_openai_init(openai.OpenAI)
    with patcher:
        Routeplane(api_key="rp_test", provider="anthropic", strategy="cost")
    hdrs = captured["default_headers"]
    assert hdrs["x-routeplane-api-key"] == "rp_test"
    assert hdrs["x-routeplane-provider"] == "anthropic"
    assert hdrs["x-routeplane-strategy"] == "cost"
    assert captured["api_key"] == "rp_test"
    assert captured["base_url"] == "https://api.routeplane.ai/v1"


def test_client_default_base_url_and_no_extra_headers():
    captured, patcher = _capture_openai_init(openai.OpenAI)
    with patcher:
        Routeplane(api_key="rp_test")
    hdrs = captured["default_headers"]
    # Only auth when no routing options are set.
    assert hdrs == {"x-routeplane-api-key": "rp_test"}


def test_client_base_url_override():
    captured, patcher = _capture_openai_init(openai.OpenAI)
    with patcher:
        Routeplane(api_key="rp_test", base_url="https://gateway.example.com/v1")
    assert captured["base_url"] == "https://gateway.example.com/v1"


def test_client_merges_caller_default_headers():
    captured, patcher = _capture_openai_init(openai.OpenAI)
    with patcher:
        Routeplane(
            api_key="rp_test",
            provider="openai",
            default_headers={"x-tenant": "acme"},
        )
    hdrs = captured["default_headers"]
    assert hdrs["x-tenant"] == "acme"
    assert hdrs["x-routeplane-provider"] == "openai"
    assert hdrs["x-routeplane-api-key"] == "rp_test"


def test_client_stores_rp_defaults():
    captured, patcher = _capture_openai_init(openai.OpenAI)
    with patcher:
        client = Routeplane(api_key="rp_test", residency="IN", use_case="rag")
    assert client._rp_defaults["residency"] == "IN"
    assert client._rp_defaults["use_case"] == "rag"
    assert client._rp_defaults["provider"] is None


def test_async_client_sets_headers():
    captured, patcher = _capture_openai_init(openai.AsyncOpenAI)
    with patcher:
        AsyncRouteplane(api_key="rp_test", provider="gemini", residency="IN")
    hdrs = captured["default_headers"]
    assert hdrs["x-routeplane-api-key"] == "rp_test"
    assert hdrs["x-routeplane-provider"] == "gemini"
    assert hdrs["x-routeplane-residency"] == "IN"


def test_meta_from_headers_helper():
    meta = Routeplane.meta_from_headers({"x-routeplane-provider": "openai"})
    assert meta.provider == "openai"


@respx.mock
def test_status_resource_hits_origin_root():
    route = respx.get("https://api.routeplane.ai/status").mock(
        return_value=httpx.Response(200, json={"status": "ok", "version": "1.2.3"})
    )
    res = StatusResource(api_key="rp_test", base_url="https://api.routeplane.ai/v1")
    status = res.retrieve()

    assert status.status == "ok"
    assert status.version == "1.2.3"
    assert status.raw == {"status": "ok", "version": "1.2.3"}
    # /status resolves against the host origin, not under /v1.
    assert route.called
    sent = route.calls.last.request
    assert str(sent.url) == "https://api.routeplane.ai/status"
    assert sent.headers["x-routeplane-api-key"] == "rp_test"


@respx.mock
def test_status_resource_raises_on_error():
    respx.get("https://api.routeplane.ai/status").mock(
        return_value=httpx.Response(500, json={"error": "boom"})
    )
    res = StatusResource(api_key="rp_test", base_url="https://api.routeplane.ai/v1")
    with pytest.raises(httpx.HTTPStatusError):
        res.retrieve()
