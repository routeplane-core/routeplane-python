"""Minimal usage.

The ``Routeplane`` client subclasses ``openai.OpenAI``, so
``chat.completions.create`` works exactly as you already know it.

    pip install routeplane
    python examples/basic.py
"""

from routeplane import Routeplane

rp = Routeplane(api_key="rp_live_...")

resp = rp.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "What is DPDP?"}],
)
print(resp.choices[0].message.content)
