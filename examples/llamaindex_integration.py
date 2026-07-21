"""LlamaIndex integration.

``headers()`` plugs into the LlamaIndex OpenAI LLM's ``default_headers``. The
``rp_`` key passed as ``api_key`` authenticates via the gateway's
``Authorization: Bearer rp_...`` fallback.

    pip install routeplane llama-index-llms-openai
    python examples/llamaindex_integration.py
"""

from llama_index.llms.openai import OpenAI as LlamaOpenAI

from routeplane import headers

llm = LlamaOpenAI(
    model="gpt-4o",
    api_key="rp_live_...",
    api_base="https://api.routeplane.ai/v1",
    default_headers=headers(provider="openai,anthropic", strategy="cost"),
)

response = llm.complete("What is data residency?")
print(response.text)
