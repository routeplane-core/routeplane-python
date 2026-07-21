"""``GET /status`` — the one Phase-1 resource that is fully implemented."""

from __future__ import annotations

from .._types import Status
from ._base import BaseResource

__all__ = ["StatusResource"]


class StatusResource(BaseResource):
    """Read the gateway's status endpoint."""

    def retrieve(self) -> Status:
        """Fetch ``GET /status`` and parse it into a :class:`~routeplane._types.Status`.

        Returns:
            The parsed status; the full raw payload is preserved on
            :attr:`Status.raw`.
        """
        response = self._get("/status")
        data = response.json()
        if not isinstance(data, dict):
            data = {"status": data}
        return Status.from_dict(data)
