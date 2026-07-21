"""The :class:`Routeplane` client — a thin subclass of ``openai.OpenAI``.

Everything the OpenAI SDK can do works unchanged (``client.chat.completions``,
``client.embeddings``, streaming, retries). The subclass only injects the
gateway auth header plus any default ``x-routeplane-*`` routing headers so the
caller does not have to pass them on every call.
"""

from __future__ import annotations

from typing import Any, Mapping, Optional

import openai

from .headers import headers as build_headers
from .meta import RouteplaneMeta

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
