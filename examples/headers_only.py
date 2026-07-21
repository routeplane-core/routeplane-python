"""Layer 1 — keep the stock ``openai`` client and steer the gateway per request
with the typed ``headers()`` builder.

Passing the ``rp_`` key as ``api_key`` authenticates via the gateway's
``Authorization: Bearer rp_...`` fallback, so no extra auth header is needed.

    pip install routeplane openai
    python examples/headers_only.py
"""

from openai import OpenAI

from routeplane import headers

client = OpenAI(
    api_key="rp_live_...",
    base_url="https://api.routeplane.ai/v1",
)

resp = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello"}],
    extra_headers=headers(
        provider="anthropic,openai",  # try Anthropic, fall back to OpenAI
        residency="IN",  # keep regulated data in-region
        strategy="cost",  # cheapest eligible provider first
        use_case="support-bot",  # FinOps cost attribution
    ),
)
print(resp.choices[0].message.content)
