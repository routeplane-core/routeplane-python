"""CrewAI integration.

``headers()`` drops into the CrewAI ``LLM``'s ``extra_headers``. The ``rp_`` key
passed as ``api_key`` authenticates via the gateway's
``Authorization: Bearer rp_...`` fallback.

    pip install routeplane crewai
    python examples/crewai_integration.py
"""

from crewai import LLM

from routeplane import headers

llm = LLM(
    model="openai/gpt-4o",
    api_key="rp_live_...",
    base_url="https://api.routeplane.ai/v1",
    extra_headers=headers(provider="anthropic", residency="IN"),
)

print(llm.call("What is DPDP?"))
