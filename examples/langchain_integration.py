"""LangChain integration.

``headers()`` returns a plain dict, so it drops into ``ChatOpenAI``'s
``default_headers``. The ``rp_`` key passed as ``api_key`` authenticates via the
gateway's ``Authorization: Bearer rp_...`` fallback.

    pip install routeplane langchain-openai
    python examples/langchain_integration.py
"""

from langchain_openai import ChatOpenAI

from routeplane import headers

llm = ChatOpenAI(
    model="gpt-4o",
    api_key="rp_live_...",
    base_url="https://api.routeplane.ai/v1",
    default_headers=headers(provider="anthropic", residency="IN"),
)

response = llm.invoke("What is DPDP?")
print(response.content)
