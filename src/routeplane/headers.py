"""Typed builder for the ``x-routeplane-*`` request headers.

The gateway is configured entirely through request headers, so this builder is
the single most reusable piece of the SDK: it works with *any* OpenAI-compatible
client (stock ``openai``, LangChain, LlamaIndex, a raw ``httpx`` call) via that
client's ``extra_headers`` / ``default_headers`` escape hatch.

Only headers with non-``None`` values are emitted. Dict-valued options
(``config``, ``metadata``) are JSON-serialized; integers are stringified.
"""

from __future__ import annotations

import json
from typing import Any, Literal

__all__ = ["headers", "HEADER_NAMES"]

# Maps each keyword argument to its wire header name. Keeping this as data (not
# branches) means the omit-None / serialize logic below stays uniform.
HEADER_NAMES: dict[str, str] = {
    "provider": "x-routeplane-provider",
    "residency": "x-routeplane-residency",
    "strategy": "x-routeplane-strategy",
    "config": "x-routeplane-config",
    "timeout_ms": "x-routeplane-timeout-ms",
    "use_case": "x-routeplane-use-case",
    "log_level": "x-routeplane-log-level",
    "conversation_id": "x-routeplane-conversation-id",
    "currency": "x-routeplane-currency",
    "metadata": "x-routeplane-metadata",
    "pii_mode": "x-routeplane-pii-mode",
    "output_mask": "x-routeplane-output-mask",
    "cache_control": "x-routeplane-cache-control",
    "idempotency_key": "x-routeplane-idempotency-key",
    "cohort": "x-routeplane-cohort",
    "batch": "x-routeplane-batch",
    "trace_id": "x-routeplane-trace-id",
}


def headers(
    *,
    provider: str | None = None,
    residency: str | None = None,
    strategy: Literal["priority", "weighted", "cost", "latency"] | None = None,
    config: dict[str, Any] | None = None,
    timeout_ms: int | None = None,
    use_case: str | None = None,
    log_level: Literal["metadata", "none", "full"] | None = None,
    conversation_id: str | None = None,
    currency: str | None = None,
    metadata: dict[str, str] | None = None,
    pii_mode: Literal["tokenize"] | None = None,
    output_mask: str | None = None,
    cache_control: Literal["no-store"] | None = None,
    idempotency_key: str | None = None,
    cohort: str | None = None,
    batch: str | None = None,
    trace_id: str | None = None,
) -> dict[str, str]:
    """Build a dict of ``x-routeplane-*`` headers for any OpenAI-compatible client.

    Only includes headers whose value is non-``None``. Dict values (``config``,
    ``metadata``) are JSON-serialized; ``timeout_ms`` is stringified.

    Works with ``extra_headers=headers(...)`` on the stock OpenAI SDK,
    ``default_headers=headers(...)`` on LangChain, and any client that forwards
    extra headers to the underlying HTTP request.

    Args:
        provider: Provider or comma-separated fallback chain (e.g. ``"openai"``
            or ``"openai,anthropic"``). Overridden by sovereign routing when the
            request carries personal data and a residency region.
        residency: Requested data-residency region (e.g. ``"IN"``). Only enforced
            when the request also carries personal data.
        strategy: Provider-ordering strategy.
        config: Inline routing/policy config, JSON-serialized onto the wire.
        timeout_ms: Per-request upstream timeout in milliseconds.
        use_case: Free-form use-case label for analytics/FinOps attribution.
        log_level: Per-request logging verbosity.
        conversation_id: Groups requests into one logical conversation.
        currency: Preferred currency for cost reporting (e.g. ``"INR"``).
        metadata: Arbitrary key/value tags, JSON-serialized onto the wire.
        pii_mode: PII handling mode.
        output_mask: Output masking policy reference.
        cache_control: Response-cache directive.
        idempotency_key: Client-supplied idempotency key for safe retries.
        cohort: Experiment/cohort label.
        batch: Batch identifier.
        trace_id: Client-supplied distributed-trace id (echoed back on the response).

    Returns:
        A ``dict[str, str]`` of header name to value, suitable to splat into any
        client's extra/default headers.
    """
    values: dict[str, Any] = {
        "provider": provider,
        "residency": residency,
        "strategy": strategy,
        "config": config,
        "timeout_ms": timeout_ms,
        "use_case": use_case,
        "log_level": log_level,
        "conversation_id": conversation_id,
        "currency": currency,
        "metadata": metadata,
        "pii_mode": pii_mode,
        "output_mask": output_mask,
        "cache_control": cache_control,
        "idempotency_key": idempotency_key,
        "cohort": cohort,
        "batch": batch,
        "trace_id": trace_id,
    }

    out: dict[str, str] = {}
    for key, value in values.items():
        if value is None:
            continue
        header_name = HEADER_NAMES[key]
        if isinstance(value, dict):
            out[header_name] = json.dumps(value, separators=(",", ":"))
        elif isinstance(value, bool):
            # Guard before int: bool is a subclass of int in Python.
            out[header_name] = "true" if value else "false"
        elif isinstance(value, int):
            out[header_name] = str(value)
        else:
            out[header_name] = str(value)
    return out
