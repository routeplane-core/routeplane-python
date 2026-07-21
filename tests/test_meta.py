from routeplane import RouteplaneMeta


def test_empty_headers_yield_defaults():
    meta = RouteplaneMeta.from_headers({})
    assert meta.provider is None
    assert meta.cache is None
    assert meta.hedged is False
    assert meta.shed is False
    assert meta.pii_masked is False
    assert meta.idempotent_replayed is False


def test_parses_string_fields():
    meta = RouteplaneMeta.from_headers(
        {
            "x-routeplane-provider": "anthropic",
            "x-routeplane-trace-id": "trace_1",
            "x-routeplane-request-id": "req_1",
            "x-routeplane-cache": "hit",
            "x-routeplane-guardrails": "passed",
            "x-routeplane-budget-remaining": "42.50",
            "x-routeplane-budget-warning": "80%",
            "x-routeplane-compliance-warning": "residency-relaxed",
        }
    )
    assert meta.provider == "anthropic"
    assert meta.trace_id == "trace_1"
    assert meta.request_id == "req_1"
    assert meta.cache == "hit"
    assert meta.guardrails == "passed"
    assert meta.budget_remaining == "42.50"
    assert meta.budget_warning == "80%"
    assert meta.compliance_warning == "residency-relaxed"


def test_parses_boolean_flags_true():
    meta = RouteplaneMeta.from_headers(
        {
            "x-routeplane-hedged": "true",
            "x-routeplane-shed": "true",
            "x-routeplane-pii-masked": "true",
            "x-routeplane-idempotent-replayed": "true",
        }
    )
    assert meta.hedged is True
    assert meta.shed is True
    assert meta.pii_masked is True
    assert meta.idempotent_replayed is True


def test_parses_boolean_flags_false():
    meta = RouteplaneMeta.from_headers(
        {
            "x-routeplane-hedged": "false",
            "x-routeplane-shed": "FALSE",
            "x-routeplane-pii-masked": "0",
        }
    )
    assert meta.hedged is False
    assert meta.shed is False
    assert meta.pii_masked is False


def test_boolean_flags_are_case_insensitive():
    meta = RouteplaneMeta.from_headers({"x-routeplane-hedged": "True"})
    assert meta.hedged is True


def test_is_frozen():
    meta = RouteplaneMeta.from_headers({"x-routeplane-provider": "openai"})
    try:
        meta.provider = "anthropic"  # type: ignore[misc]
    except Exception as exc:  # dataclass(frozen=True) raises FrozenInstanceError
        assert "cannot assign" in str(exc).lower() or "frozen" in type(exc).__name__.lower()
    else:
        raise AssertionError("RouteplaneMeta should be frozen")


def test_works_with_httpx_headers():
    import httpx

    hdrs = httpx.Headers({"X-Routeplane-Cache": "miss", "X-Routeplane-Hedged": "true"})
    meta = RouteplaneMeta.from_headers(hdrs)
    assert meta.cache == "miss"
    assert meta.hedged is True
