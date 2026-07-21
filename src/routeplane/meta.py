"""Parse the ``x-routeplane-*`` *response* headers into a typed object.

Every response the gateway returns carries a handful of ``x-routeplane-*``
headers describing what the gateway did — which provider served the request,
whether the response came from cache, whether budgets are close to exhaustion,
and so on. :class:`RouteplaneMeta` turns that loosely-typed header bag into a
frozen dataclass so callers can branch on ``meta.cache == "hit"`` instead of
digging through raw headers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional

__all__ = ["RouteplaneMeta"]

_TRUE = {"true", "1", "yes", "on"}


def _flag(headers: Mapping[str, str], name: str) -> bool:
    value = headers.get(name)
    if value is None:
        return False
    return value.strip().lower() in _TRUE


@dataclass(frozen=True)
class RouteplaneMeta:
    """Typed view over the ``x-routeplane-*`` response headers.

    Construct it with :meth:`from_headers`, passing any case-insensitive header
    mapping (``httpx.Headers``, ``requests`` headers, or a plain ``dict``).
    """

    provider: Optional[str] = None
    trace_id: Optional[str] = None
    request_id: Optional[str] = None
    cache: Optional[str] = None  # "hit" | "miss" | "bypass"
    guardrails: Optional[str] = None
    hedged: bool = False
    shed: bool = False
    budget_remaining: Optional[str] = None
    budget_warning: Optional[str] = None
    compliance_warning: Optional[str] = None
    pii_masked: bool = False
    idempotent_replayed: bool = False

    @classmethod
    def from_headers(cls, headers: Mapping[str, str]) -> "RouteplaneMeta":
        """Parse response headers into a :class:`RouteplaneMeta`.

        Args:
            headers: A case-insensitive mapping of response headers. ``httpx``
                and ``requests`` both provide this; a plain ``dict`` works too as
                long as keys are lowercase ``x-routeplane-*``.

        Returns:
            A populated :class:`RouteplaneMeta`. Missing headers fall back to
            ``None`` (strings) or ``False`` (flags).
        """
        return cls(
            provider=headers.get("x-routeplane-provider"),
            trace_id=headers.get("x-routeplane-trace-id"),
            request_id=headers.get("x-routeplane-request-id"),
            cache=headers.get("x-routeplane-cache"),
            guardrails=headers.get("x-routeplane-guardrails"),
            hedged=_flag(headers, "x-routeplane-hedged"),
            shed=_flag(headers, "x-routeplane-shed"),
            budget_remaining=headers.get("x-routeplane-budget-remaining"),
            budget_warning=headers.get("x-routeplane-budget-warning"),
            compliance_warning=headers.get("x-routeplane-compliance-warning"),
            pii_masked=_flag(headers, "x-routeplane-pii-masked"),
            idempotent_replayed=_flag(headers, "x-routeplane-idempotent-replayed"),
        )
