# Routeplane Python SDK

The official Python SDK for the [Routeplane](https://routeplane.ai) AI Gateway — a
neutral, OpenAI-compatible proxy in front of 14 LLM providers with sovereign
routing, guardrails, FinOps, and agentic security.

Routeplane speaks the OpenAI wire format, so you don't have to relearn anything.
This SDK meets you at whatever level of integration you want:

1. **Change one line** — point the stock `openai` client at the gateway.
2. **Add headers** — use `headers()` with *any* OpenAI-compatible client or framework.
3. **Use the client** — `Routeplane` gives you auth, default routing, and typed
   response metadata.

## Install

```bash
pip install routeplane
```

## 1. Minimal — 30 seconds, just change `base_url`

If you already use the OpenAI SDK, point it at Routeplane and pass your gateway
key. Nothing else changes.

```python
import openai

client = openai.OpenAI(
    api_key="rp_your_gateway_key",
    base_url="https://api.routeplane.ai/v1",
    default_headers={"x-routeplane-api-key": "rp_your_gateway_key"},
)

resp = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello!"}],
)
print(resp.choices[0].message.content)
```

## 2. Intermediate — `headers()` with any client

Routeplane is configured through `x-routeplane-*` request headers (provider
routing, residency, strategy, budgets, and more). The `headers()` builder is a
typed way to produce them, and it drops into *any* client's extra-headers
escape hatch — so it works far beyond this SDK.

```python
import openai
from routeplane import headers

client = openai.OpenAI(
    api_key="rp_your_gateway_key",
    base_url="https://api.routeplane.ai/v1",
    default_headers={"x-routeplane-api-key": "rp_your_gateway_key"},
)

resp = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Summarize this contract."}],
    extra_headers=headers(
        provider="anthropic,openai",   # fallback chain
        strategy="cost",               # cheapest eligible provider first
        residency="IN",                # keep Indian PII in-region
        use_case="contract-summary",   # shows up in FinOps
    ),
)
```

`headers()` only emits the options you set, JSON-serializes dict values
(`config`, `metadata`), and stringifies ints (`timeout_ms`). All 17 request
headers are typed.

## 3. Full — the `Routeplane` client with rich metadata

`Routeplane` subclasses `openai.OpenAI`, so everything works exactly as before —
but it wires up auth for you, lets you set default routing once, and can parse
the gateway's response headers into a typed `RouteplaneMeta`.

```python
from routeplane import Routeplane

client = Routeplane(
    api_key="rp_your_gateway_key",
    provider="openai,anthropic",   # client-wide default fallback chain
    strategy="latency",
    residency="IN",
    use_case="support-bot",
)

# Ordinary call — same OpenAI API you already know.
resp = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hi"}],
)

# Want to know what the gateway did? Read the response headers.
raw = client.chat.completions.with_raw_response.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hi"}],
)
meta = client.meta_from_headers(raw.headers)
completion = raw.parse()

print(meta.provider)          # which provider actually served it
print(meta.cache)             # "hit" | "miss" | "bypass"
print(meta.budget_remaining)  # spend headroom
print(meta.pii_masked)        # was PII masked on the way out?
```

Per-call `extra_headers=headers(...)` still override the client defaults, so you
can set a house style once and deviate where you need to.

### Async

```python
from routeplane import AsyncRouteplane

client = AsyncRouteplane(api_key="rp_your_gateway_key", strategy="cost")

resp = await client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello!"}],
)
```

## Framework examples

Because `headers()` returns a plain dict of headers, it plugs into anything that
forwards headers to the OpenAI API.

### LangChain

```python
from langchain_openai import ChatOpenAI
from routeplane import headers

llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key="rp_your_gateway_key",
    base_url="https://api.routeplane.ai/v1",
    default_headers={
        "x-routeplane-api-key": "rp_your_gateway_key",
        **headers(provider="anthropic,openai", strategy="cost"),
    },
)
```

### LlamaIndex

```python
from llama_index.llms.openai import OpenAI
from routeplane import headers

llm = OpenAI(
    model="gpt-4o-mini",
    api_key="rp_your_gateway_key",
    api_base="https://api.routeplane.ai/v1",
    default_headers={
        "x-routeplane-api-key": "rp_your_gateway_key",
        **headers(residency="IN", use_case="rag"),
    },
)
```

### CrewAI

```python
from crewai import LLM
from routeplane import headers

llm = LLM(
    model="openai/gpt-4o-mini",
    base_url="https://api.routeplane.ai/v1",
    api_key="rp_your_gateway_key",
    extra_headers={
        "x-routeplane-api-key": "rp_your_gateway_key",
        **headers(strategy="latency", use_case="research-crew"),
    },
)
```

## Request headers reference

All are `x-routeplane-*` and all are optional except the API key. Build them with
`headers(...)`.

| Option | Header | Notes |
| --- | --- | --- |
| `provider` | `x-routeplane-provider` | Provider or comma-separated fallback chain |
| `residency` | `x-routeplane-residency` | Data-residency region (e.g. `IN`) |
| `strategy` | `x-routeplane-strategy` | `priority` \| `weighted` \| `cost` \| `latency` |
| `config` | `x-routeplane-config` | Inline routing config (JSON) |
| `timeout_ms` | `x-routeplane-timeout-ms` | Upstream timeout, ms |
| `use_case` | `x-routeplane-use-case` | Analytics/FinOps label |
| `log_level` | `x-routeplane-log-level` | `metadata` \| `none` \| `full` |
| `conversation_id` | `x-routeplane-conversation-id` | Groups a conversation |
| `currency` | `x-routeplane-currency` | Cost-reporting currency |
| `metadata` | `x-routeplane-metadata` | Arbitrary tags (JSON) |
| `pii_mode` | `x-routeplane-pii-mode` | `tokenize` |
| `output_mask` | `x-routeplane-output-mask` | Output masking policy |
| `cache_control` | `x-routeplane-cache-control` | `no-store` |
| `idempotency_key` | `x-routeplane-idempotency-key` | Safe-retry key |
| `cohort` | `x-routeplane-cohort` | Experiment cohort |
| `batch` | `x-routeplane-batch` | Batch id |
| `trace_id` | `x-routeplane-trace-id` | Client trace id (echoed back) |

## Response metadata

`RouteplaneMeta.from_headers(response_headers)` (or `client.meta_from_headers(...)`)
parses the gateway's `x-routeplane-*` response headers: `provider`, `trace_id`,
`request_id`, `cache`, `guardrails`, `hedged`, `shed`, `budget_remaining`,
`budget_warning`, `compliance_warning`, `pii_masked`, `idempotent_replayed`.

## Examples

Runnable scripts live in [`examples/`](examples):

| File | Shows |
| --- | --- |
| [`basic.py`](examples/basic.py) | Minimal `Routeplane` client — a drop-in OpenAI subclass |
| [`headers_only.py`](examples/headers_only.py) | Stock `openai` SDK + `headers()` for per-request steering |
| [`streaming_with_meta.py`](examples/streaming_with_meta.py) | Streaming with the gateway's decision metadata |
| [`metadata.py`](examples/metadata.py) | `create_with_meta` — completion plus typed `RouteplaneMeta` |
| [`resources.py`](examples/resources.py) | Non-OpenAI surfaces — status, logs, FinOps, prompts, cache |
| [`langchain_integration.py`](examples/langchain_integration.py) | LangChain (`ChatOpenAI`) |
| [`llamaindex_integration.py`](examples/llamaindex_integration.py) | LlamaIndex (`llama-index-llms-openai`) |
| [`crewai_integration.py`](examples/crewai_integration.py) | CrewAI (`LLM`) |

See [`examples/`](examples) for more.

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check .
mypy src
```

## License

Apache-2.0. See [LICENSE](LICENSE).
