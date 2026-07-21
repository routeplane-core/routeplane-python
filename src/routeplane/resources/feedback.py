"""Feedback namespace (``POST /v1/feedback``). Phase 5 stub."""

from __future__ import annotations

from ._base import BaseResource

__all__ = ["FeedbackResource"]


class FeedbackResource(BaseResource):
    """Access to ``POST /v1/feedback``. Not yet implemented — lands in Phase 5."""

    def create(self, **body: object) -> object:
        raise NotImplementedError("FeedbackResource lands in Phase 5")
