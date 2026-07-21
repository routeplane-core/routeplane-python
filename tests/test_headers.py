import json

from routeplane import headers
from routeplane.headers import HEADER_NAMES


def test_empty_when_all_none():
    assert headers() == {}


def test_omits_none_values():
    result = headers(provider="openai", residency=None, strategy=None)
    assert result == {"x-routeplane-provider": "openai"}


def test_simple_string_headers():
    result = headers(provider="openai,anthropic", residency="IN", strategy="cost")
    assert result == {
        "x-routeplane-provider": "openai,anthropic",
        "x-routeplane-residency": "IN",
        "x-routeplane-strategy": "cost",
    }


def test_dict_headers_are_json_serialized():
    result = headers(
        config={"retries": 2, "fallback": True},
        metadata={"team": "platform", "env": "prod"},
    )
    assert json.loads(result["x-routeplane-config"]) == {"retries": 2, "fallback": True}
    assert json.loads(result["x-routeplane-metadata"]) == {
        "team": "platform",
        "env": "prod",
    }
    # Compact separators (no spaces) keep the header value tight.
    assert " " not in result["x-routeplane-config"]


def test_int_headers_are_stringified():
    result = headers(timeout_ms=1500)
    assert result == {"x-routeplane-timeout-ms": "1500"}
    assert isinstance(result["x-routeplane-timeout-ms"], str)


def test_all_seventeen_headers_present():
    result = headers(
        provider="openai",
        residency="IN",
        strategy="latency",
        config={"a": 1},
        timeout_ms=1000,
        use_case="chatbot",
        log_level="metadata",
        conversation_id="conv_1",
        currency="INR",
        metadata={"k": "v"},
        pii_mode="tokenize",
        output_mask="mask_1",
        cache_control="no-store",
        idempotency_key="idem_1",
        cohort="cohort_a",
        batch="batch_1",
        trace_id="trace_1",
    )
    # Every declared header name is produced exactly once.
    assert set(result.keys()) == set(HEADER_NAMES.values())
    assert len(result) == 17


def test_header_name_mapping_is_kebab_prefixed():
    for wire in HEADER_NAMES.values():
        assert wire.startswith("x-routeplane-")
        assert wire == wire.lower()


def test_literal_values_pass_through():
    assert headers(log_level="none")["x-routeplane-log-level"] == "none"
    assert headers(pii_mode="tokenize")["x-routeplane-pii-mode"] == "tokenize"
    assert headers(cache_control="no-store")["x-routeplane-cache-control"] == "no-store"
