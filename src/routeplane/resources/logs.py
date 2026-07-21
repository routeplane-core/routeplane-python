"""Request-log namespace (``GET /v1/logs``). Phase 5 stub."""

from __future__ import annotations

from ._base import BaseResource

__all__ = ["LogsResource"]


class LogsResource(BaseResource):
    """Access to ``GET /v1/logs``. Not yet implemented — lands in Phase 5."""

    def list(self, **params: object) -> object:
        raise NotImplementedError("LogsResource lands in Phase 5")
