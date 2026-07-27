"""Prompt-management namespace (``/v1/prompts/*``).

Gated on the ``PromptRegistry`` entitlement: a tenant without it gets 403
``feature_not_entitled``, and one that is entitled but still behind a rollout
holdback gets 403 ``feature_not_released``.
"""

from __future__ import annotations

from typing import Any, Optional

from ._base import BaseResource, prune_none

__all__ = ["PromptsResource"]


def _routing_headers(provider: Optional[str], cohort: Optional[str]) -> dict[str, str]:
    """Build the per-call routing headers these endpoints honour.

    Provider selection and experiment cohort travel as ``x-routeplane-*``
    headers, never as body fields — the completions body is flattened straight
    into a chat request, so a ``provider`` key placed there is silently dropped
    rather than rejected.
    """
    headers: dict[str, str] = {}
    if provider is not None:
        headers["x-routeplane-provider"] = provider
    if cohort is not None:
        headers["x-routeplane-cohort"] = cohort
    return headers


class PromptsResource(BaseResource):
    """Fetch, render, and complete managed prompt templates (PRD-010)."""

    def get(self, reference: str) -> dict[str, Any]:
        """``GET /v1/prompts/{reference}`` — the stored version, no render.

        ``reference`` is a prompt id, or an id qualified by version or label
        (the response reports the concrete ``version`` a label resolved to).
        """
        data: dict[str, Any] = self._get(f"prompts/{reference}").json()
        return data

    def render(
        self,
        reference: str,
        *,
        variables: Optional[dict[str, Any]] = None,
        missing: Optional[str] = None,
        cohort: Optional[str] = None,
    ) -> dict[str, Any]:
        """``POST /v1/prompts/{reference}/render`` — interpolate, no upstream call.

        ``missing`` selects what an unsupplied variable does: ``"error"`` (the
        default) fails the render, ``"empty"`` substitutes nothing. ``cohort``
        is the sticky assignment key for an A/B-tested prompt; omitting it
        serves the control arm.
        """
        body = prune_none({"variables": variables, "missing": missing})
        data: dict[str, Any] = self._post(
            f"prompts/{reference}/render",
            json=body,
            headers=_routing_headers(None, cohort),
        ).json()
        return data

    def complete(
        self,
        reference: str,
        *,
        variables: Optional[dict[str, Any]] = None,
        missing: Optional[str] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        cohort: Optional[str] = None,
        **overrides: Any,
    ) -> dict[str, Any]:
        """``POST /v1/prompts/{reference}/completions`` — render, then run it.

        The rendered template runs through the ordinary chat pipeline, so
        residency routing, guardrails, caching, and budgets all apply.

        Any extra keyword lands in the chat request as an override —
        ``temperature``, ``max_tokens``, ``user``, and so on — and beats the
        version's stored defaults. ``model`` is one such override, named
        explicitly because a version without a ``default_model`` requires it.
        Sovereign residency routing still overrides everything.
        """
        body = prune_none({"variables": variables, "missing": missing, "model": model})
        body.update(prune_none(overrides))
        data: dict[str, Any] = self._post(
            f"prompts/{reference}/completions",
            json=body,
            headers=_routing_headers(provider, cohort),
        ).json()
        return data
