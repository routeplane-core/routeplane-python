"""The :class:`Routeplane` client — a thin subclass of ``openai.OpenAI``.

Everything the OpenAI SDK can do works unchanged (``client.chat.completions``,
``client.embeddings``, streaming, retries). The subclass adds three things:

1. gateway auth + default ``x-routeplane-*`` routing headers, so callers don't
   repeat them on every request;
2. ``create_with_meta`` / ``stream_with_meta`` convenience that returns the
   parsed completion *and* the :class:`RouteplaneMeta` gateway metadata;
3. the non-OpenAI resource namespaces (prompts, logs, finops, cache, feedback,
   residency, mcp, models, providers, analytics, status).
"""

from __future__ import annotations

from typing import Any, Mapping, Optional, Tuple, cast

import httpx
import openai
from openai.types.chat import ChatCompletion, ChatCompletionChunk

from ._streaming import RouteplaneStream
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

__all__ = ["Routeplane"]

DEFAULT_BASE_URL = "https://api.routeplane.ai/v1"


class Routeplane(openai.OpenAI):
    """Drop-in ``openai.OpenAI`` pointed at the Routeplane gateway.

    Auth is sent as the native ``x-routeplane-api-key`` header. The OpenAI SDK
    additionally sets ``Authorization: Bearer <api_key>`` from ``api_key``; the
    gateway accepts both and the native header takes precedence, so passing the
    same value to both is intentional and harmless.

    Per-request routing headers still win over the client defaults set here — use
    :func:`routeplane.headers` with ``extra_headers=`` on any individual call.
    """

    _rp_defaults: dict[str, Any]
    _rp_http: httpx.Client

    # Routeplane-only resource namespaces (the OpenAI-shaped surfaces stay on the
    # inherited attributes; these carry the ``rp_``/``_security`` prefixes only
    # where the plain name is already taken by the OpenAI SDK).
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

        # Merge, never clobber, any default_headers the caller passed through.
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

        # One shared httpx client for every REST-shaped namespace; the routing
        # defaults ride along so prompt completions honour them too.
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

        Pair with the OpenAI SDK's ``with_raw_response`` to inspect what the
        gateway did::

            raw = client.chat.completions.with_raw_response.create(...)
            meta = client.meta_from_headers(raw.headers)
            completion = raw.parse()
        """
        return RouteplaneMeta.from_headers(headers)

    def create_with_meta(self, **kwargs: Any) -> Tuple[ChatCompletion, RouteplaneMeta]:
        """Chat completion that also returns the gateway :class:`RouteplaneMeta`.

        ::

            completion, meta = client.create_with_meta(model="gpt-4o", messages=[...])
            print(meta.provider, meta.cache)
        """
        raw = self.chat.completions.with_raw_response.create(**kwargs)
        completion = cast(ChatCompletion, raw.parse())
        return completion, RouteplaneMeta.from_headers(raw.headers)

    def stream_with_meta(self, **kwargs: Any) -> RouteplaneStream[ChatCompletionChunk]:
        """Streaming chat completion that also exposes ``meta`` on the stream.

        ``meta`` is populated from the response headers, which arrive before the
        first chunk, so it can be read immediately::

            stream = client.stream_with_meta(model="gpt-4o", messages=[...])
            print(stream.meta.provider)
            for chunk in stream:
                ...
        """
        kwargs["stream"] = True
        raw = self.chat.completions.with_raw_response.create(**kwargs)
        stream: Any = raw.parse()
        return RouteplaneStream(stream, raw.headers)

    def close(self) -> None:
        """Close the OpenAI transport *and* the shared Routeplane httpx client."""
        try:
            self._rp_http.close()
        finally:
            super().close()
