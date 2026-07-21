"""Official Python SDK for the Routeplane AI Gateway.

Three ways in, smallest to largest:

1. Change nothing but ``base_url`` on the stock ``openai`` client.
2. Splat :func:`headers` into ``extra_headers`` on any OpenAI-compatible client.
3. Use :class:`Routeplane` / :class:`AsyncRouteplane` for auth + defaults +
   typed response metadata (:class:`RouteplaneMeta`).
"""

from ._version import __version__
from .async_client import AsyncRouteplane
from .client import Routeplane
from .headers import headers
from .meta import RouteplaneMeta

__all__ = [
    "Routeplane",
    "AsyncRouteplane",
    "headers",
    "RouteplaneMeta",
    "__version__",
]
