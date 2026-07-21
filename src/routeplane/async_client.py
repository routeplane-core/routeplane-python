"""The :class:`AsyncRouteplane` client — a thin subclass of ``openai.AsyncOpenAI``.

Async twin of :class:`routeplane.Routeplane`; same header-injection behavior.
"""

from __future__ import annotations

from typing import Any, Mapping, Optional

import openai

from .client import DEFAULT_BASE_URL
from .headers import headers as build_headers
from .meta import RouteplaneMeta

__all__ = ["AsyncRouteplane"]


class AsyncRouteplane(openai.AsyncOpenAI):
    """Drop-in ``openai.AsyncOpenAI`` pointed at the Routeplane gateway.

    See :class:`routeplane.Routeplane` for the auth/header semantics — this is
    the ``async``/``await`` variant.
    """

    _rp_defaults: dict[str, Any]

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

    @staticmethod
    def meta_from_headers(headers: Mapping[str, str]) -> RouteplaneMeta:
        """Parse ``x-routeplane-*`` response headers into a :class:`RouteplaneMeta`.

        Pair with the OpenAI SDK's async ``with_raw_response``::

            raw = await client.chat.completions.with_raw_response.create(...)
            meta = client.meta_from_headers(raw.headers)
            completion = raw.parse()
        """
        return RouteplaneMeta.from_headers(headers)
