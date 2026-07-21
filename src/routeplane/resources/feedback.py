"""Feedback namespace (``POST /v1/feedback``)."""

from __future__ import annotations

from typing import Optional

from ._base import BaseResource, prune_none

__all__ = ["FeedbackResource"]


class FeedbackResource(BaseResource):
    """Attach a quality signal to a prior request."""

    def create(
        self,
        *,
        request_id: str,
        score: float,
        comment: Optional[str] = None,
    ) -> None:
        """``POST /v1/feedback`` — score a request (``request_id``) with an optional note."""
        body = prune_none({"request_id": request_id, "score": score, "comment": comment})
        self._post("feedback", json=body)
