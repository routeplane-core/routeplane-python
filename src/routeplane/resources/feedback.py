"""Feedback namespace (``POST /v1/feedback``)."""

from __future__ import annotations

from typing import Optional

from ._base import BaseResource

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
        """Score a gateway request using the legacy ``trace_id``/``value`` wire.

        ``score`` must be an integer from -10 through 10; integral floats are
        accepted without rescaling. Invalid types raise ``TypeError`` and
        invalid values raise ``ValueError`` before any request is sent.
        Comments are unsupported: omit them or pass ``None``/``""``.
        Returns ``None`` on acknowledgement, not a durability guarantee.
        """
        if isinstance(score, bool) or not isinstance(score, (int, float)):
            raise TypeError("score must be a number (int or float), not a boolean")
        # Check the bounds before converting: this also rejects NaN/infinity
        # and avoids coercing huge integers or truncating fractional scores.
        if not -10 <= score <= 10 or int(score) != score:
            raise ValueError("score must be an integer from -10 through 10")
        if comment is not None and not isinstance(comment, str):
            raise TypeError("comment must be a string or None")
        if comment is not None and comment != "":
            raise ValueError("comment is not supported by the legacy feedback endpoint")
        body = {"trace_id": request_id, "value": int(score)}
        self._post("feedback", json=body)
