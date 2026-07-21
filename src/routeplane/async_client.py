"""The :class:`AsyncRouteplane` client — a thin subclass of ``openai.AsyncOpenAI``.

Async twin of :class:`routeplane.Routeplane`; same header injection, the same
resource namespaces, and async-native ``create_with_meta`` / ``stream_with_meta``.

The REST resource namespaces (``prompts``, ``finops``, …) are the same synchronous
``httpx``-backed objects the sync client exposes — they cover low-frequency
admin/analytics endpoints, so they block briefly rather than dragging a second
async HTTP stack into the SDK. The chat/embeddings hot path stays fully async via
the inherited ``openai`` client.
"""

from __future__ import annotations

from typing import Any, Mapping, Optional, Tuple, cast

import httpx
import openai
from openai.types.chat import ChatCompletion, ChatCompletionChunk

from ._streaming import AsyncRouteplaneStream
from .client import DEFAULT_BASE_URL
from .headers import headers as build_headers
from .meta import RouteplaneMeta
from .resources import (
    AnalyticsResource,
    CacheResource,
    FeedbackResource,
    FinopsResource,
    LogsResource,
    McpResource,
    ModelsResource,
    PromptsResource,
    ProvidersResource,
    ResidencyResource,
    StatusResource,
)

__all__ = ["AsyncRouteplane"]


class AsyncRouteplane(openai.AsyncOpenAI):
    """Drop-in ``openai.AsyncOpenAI`` pointed at the Routeplane gateway.

    See :class:`routeplane.Routeplane` for the auth/header semantics — this is
    the ``async``/``await`` variant.
    """

    _rp_defaults: dict[str, Any]
    _rp_http: httpx.Client

    prompts: PromptsResource
    logs: LogsResource
    finops: FinopsResource
    cache: CacheResource
    feedback: FeedbackResource
    residency: ResidencyResource
    mcp_security: McpResource
    rp_models: ModelsResource
    rp_providers: ProvidersResource
    analytics: AnalyticsResource
    status: StatusResource

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        *,
        provider: Optional[str] = None,
        strategy: Optional[str] = None,
        residency: Optional[str] = None,
        use_case: Optional[str] = None,
        timeout_ms: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        self._rp_defaults = {
            "provider": provider,
            "strategy": strategy,
            "residency": residency,
            "use_case": use_case,
            "timeout_ms": timeout_ms,
        }

        default_hdrs = build_headers(
            provider=provider,
            strategy=strategy,  # type: ignore[arg-type]
            residency=residency,
            use_case=use_case,
            timeout_ms=timeout_ms,
        )

        caller_headers = dict(kwargs.pop("default_headers", None) or {})
        merged = {
            "x-routeplane-api-key": api_key,
            **default_hdrs,
            **caller_headers,
        }

        super().__init__(
            api_key=api_key,
            base_url=base_url,
            default_headers=merged,
            **kwargs,
        )

        self._rp_http = httpx.Client()
        self._install_resources(api_key=api_key, base_url=base_url, routing=default_hdrs)

    def _install_resources(
        self, *, api_key: str, base_url: str, routing: Mapping[str, str]
    ) -> None:
        common: dict[str, Any] = {
            "api_key": api_key,
            "base_url": base_url,
            "http_client": self._rp_http,
            "default_headers": routing,
        }
        self.prompts = PromptsResource(**common)
        self.logs = LogsResource(**common)
        self.finops = FinopsResource(**common)
        self.cache = CacheResource(**common)
        self.feedback = FeedbackResource(**common)
        self.residency = ResidencyResource(**common)
        self.mcp_security = McpResource(**common)
        self.rp_models = ModelsResource(**common)
        self.rp_providers = ProvidersResource(**common)
        self.analytics = AnalyticsResource(**common)
        self.status = StatusResource(**common)

    @staticmethod
    def meta_from_headers(headers: Mapping[str, str]) -> RouteplaneMeta:
        """Parse ``x-routeplane-*`` response headers into a :class:`RouteplaneMeta`.

        Pair with the OpenAI SDK's async ``with_raw_response``::

            raw = await client.chat.completions.with_raw_response.create(...)
            meta = client.meta_from_headers(raw.headers)
            completion = raw.parse()
        """
        return RouteplaneMeta.from_headers(headers)

    async def create_with_meta(
        self, **kwargs: Any
    ) -> Tuple[ChatCompletion, RouteplaneMeta]:
        """Chat completion that also returns the gateway :class:`RouteplaneMeta`.

        ::

            completion, meta = await client.create_with_meta(model="gpt-4o", messages=[...])
        """
        raw = await self.chat.completions.with_raw_response.create(**kwargs)
        completion = cast(ChatCompletion, raw.parse())
        return completion, RouteplaneMeta.from_headers(raw.headers)

    async def stream_with_meta(
        self, **kwargs: Any
    ) -> AsyncRouteplaneStream[ChatCompletionChunk]:
        """Streaming chat completion that also exposes ``meta`` on the stream.

        ::

            stream = await client.stream_with_meta(model="gpt-4o", messages=[...])
            print(stream.meta.provider)
            async for chunk in stream:
                ...
        """
        kwargs["stream"] = True
        raw = await self.chat.completions.with_raw_response.create(**kwargs)
        stream: Any = raw.parse()
        return AsyncRouteplaneStream(stream, raw.headers)

    async def close(self) -> None:
        """Close the OpenAI transport *and* the shared Routeplane httpx client."""
        try:
            self._rp_http.close()
        finally:
            await super().close()
