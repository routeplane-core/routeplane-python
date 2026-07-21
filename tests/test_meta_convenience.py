"""Tests for ``create_with_meta`` / ``stream_with_meta`` on both clients."""

import json

import httpx
import respx

from routeplane import AsyncRouteplane, Routeplane

BASE = "https://api.routeplane.ai/v1"
CHAT = f"{BASE}/chat/completions"

_COMPLETION = {
    "id": "chatcmpl-1",
    "object": "chat.completion",
    "created": 0,
    "model": "gpt-4o",
    "choices": [
        {
            "index": 0,
            "message": {"role": "assistant", "content": "hi"},
            "finish_reason": "stop",
        }
    ],
    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
}

_META_HEADERS = {"x-routeplane-provider": "anthropic", "x-routeplane-cache": "hit"}


def _chunk(content, finish=None):
    return {
        "id": "c1",
        "object": "chat.completion.chunk",
        "created": 0,
        "model": "gpt-4o",
        "choices": [{"index": 0, "delta": {"content": content}, "finish_reason": finish}],
    }


def _sse():
    body = (
        f"data: {json.dumps(_chunk('Hel'))}\n\n"
        f"data: {json.dumps(_chunk('lo', 'stop'))}\n\n"
        "data: [DONE]\n\n"
    )
    return httpx.Response(
        200,
        headers={"content-type": "text/event-stream", "x-routeplane-provider": "openai"},
        content=body.encode(),
    )


@respx.mock
def test_create_with_meta_sync():
    respx.post(CHAT).mock(
        return_value=httpx.Response(200, json=_COMPLETION, headers=_META_HEADERS)
    )
    client = Routeplane(api_key="rp_test", base_url=BASE)
    try:
        completion, meta = client.create_with_meta(
            model="gpt-4o", messages=[{"role": "user", "content": "hi"}]
        )
        assert completion.choices[0].message.content == "hi"
        assert meta.provider == "anthropic"
        assert meta.cache == "hit"
    finally:
        client.close()


@respx.mock
def test_stream_with_meta_sync():
    respx.post(CHAT).mock(return_value=_sse())
    client = Routeplane(api_key="rp_test", base_url=BASE)
    try:
        stream = client.stream_with_meta(
            model="gpt-4o", messages=[{"role": "user", "content": "hi"}]
        )
        # meta is available from the response headers before the first chunk.
        assert stream.meta.provider == "openai"
        contents = [c.choices[0].delta.content for c in stream]
        assert contents == ["Hel", "lo"]
    finally:
        client.close()


@respx.mock
async def test_create_with_meta_async():
    respx.post(CHAT).mock(
        return_value=httpx.Response(200, json=_COMPLETION, headers=_META_HEADERS)
    )
    client = AsyncRouteplane(api_key="rp_test", base_url=BASE)
    try:
        completion, meta = await client.create_with_meta(
            model="gpt-4o", messages=[{"role": "user", "content": "hi"}]
        )
        assert completion.choices[0].message.content == "hi"
        assert meta.provider == "anthropic"
    finally:
        await client.close()


@respx.mock
async def test_stream_with_meta_async():
    respx.post(CHAT).mock(return_value=_sse())
    client = AsyncRouteplane(api_key="rp_test", base_url=BASE)
    try:
        stream = await client.stream_with_meta(
            model="gpt-4o", messages=[{"role": "user", "content": "hi"}]
        )
        assert stream.meta.provider == "openai"
        contents = [c.choices[0].delta.content async for c in stream]
        assert contents == ["Hel", "lo"]
    finally:
        await client.close()
