"""Shared HTTP plumbing for the non-OpenAI endpoint namespaces.

The OpenAI-shaped surfaces (chat, embeddings, …) are served by the inherited
``openai`` client. Everything Routeplane adds on top — prompts, logs, finops,
cache, feedback, mcp, status, residency — is plain REST, so those namespaces
share one small ``httpx``-backed base instead of dragging in the OpenAI request
machinery.
"""

from __future__ import annotations

from typing import Any, Mapping, Optional
from urllib.parse import urlsplit, urlunsplit

import httpx

__all__ = ["BaseResource"]


def _origin_of(base_url: str) -> str:
    """Return just ``scheme://host[:port]`` for a base URL.

    Some routes (``/status``, ``/healthz``) live at the host root rather than
    under ``/v1``. We deliberately compute the origin by parts instead of using
    ``urljoin`` — ``urljoin("https://h/v1", "/status")`` happens to work, but
    the general joining rules silently drop path segments, so building the URL
    explicitly avoids that whole class of surprise.
    """
    parts = urlsplit(base_url)
    return urlunsplit((parts.scheme, parts.netloc, "", "", ""))


class BaseResource:
    """Base for the REST-shaped Routeplane resource namespaces.

    Holds a lazily-shared :class:`httpx.Client` carrying the gateway auth header.
    Callers normally reach these through :class:`routeplane.Routeplane`, not
    directly.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str,
        *,
        http_client: Optional[httpx.Client] = None,
        default_headers: Optional[Mapping[str, str]] = None,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._origin = _origin_of(base_url)
        self._auth_headers: dict[str, str] = {
            "x-routeplane-api-key": api_key,
            **dict(default_headers or {}),
        }
        self._client = http_client or httpx.Client()

    def _url(self, path: str) -> str:
        """Build an absolute URL.

        A ``path`` starting with ``/`` is resolved against the host origin
        (e.g. ``/status``); anything else is resolved under the ``/v1`` base
        (e.g. ``prompts/foo`` → ``…/v1/prompts/foo``).
        """
        if path.startswith("/"):
            return f"{self._origin}{path}"
        return f"{self._base_url}/{path}"

    def _get(
        self,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> httpx.Response:
        merged = {**self._auth_headers, **dict(headers or {})}
        response = self._client.get(self._url(path), params=params, headers=merged)
        response.raise_for_status()
        return response

    def _post(
        self,
        path: str,
        *,
        json: Any = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> httpx.Response:
        merged = {**self._auth_headers, **dict(headers or {})}
        response = self._client.post(self._url(path), json=json, headers=merged)
        response.raise_for_status()
        return response
