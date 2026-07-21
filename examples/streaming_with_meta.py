"""Streaming plus gateway metadata.

``stream_with_meta`` returns an iterable stream whose ``.meta`` is populated from
the response headers — which arrive before the first chunk — so you can read
which provider served the request immediately.

    pip install routeplane
    python examples/streaming_with_meta.py
"""

from routeplane import Routeplane

rp = Routeplane(api_key="rp_live_...", provider="openai")

stream = rp.stream_with_meta(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Explain sovereign routing"}],
)

print(f"Served by: {stream.meta.provider}")
for chunk in stream:
    content = chunk.choices[0].delta.content
    if content:
        print(content, end="")
print()
