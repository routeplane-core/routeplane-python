"""Response metadata.

``create_with_meta`` returns the completion together with a typed
``RouteplaneMeta`` decoded from the gateway's ``x-routeplane-*`` response
headers — which provider served the request, cache disposition, spend headroom.

    pip install routeplane
    python examples/metadata.py
"""

from routeplane import Routeplane

rp = Routeplane(api_key="rp_live_...", provider="openai", strategy="cost")

completion, meta = rp.create_with_meta(
    model="gpt-4o",
    messages=[{"role": "user", "content": "What is DPDP?"}],
)

print(f"Answer: {completion.choices[0].message.content}")
print(f"Served by: {meta.provider}")
print(f"Cache: {meta.cache}")
print(f"Budget remaining: {meta.budget_remaining}")
