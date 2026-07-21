"""Sovereign-routing / residency namespace (``/v1/residency/*``). Phase 5 stub."""

from __future__ import annotations

from ._base import BaseResource

__all__ = ["ResidencyResource"]


class ResidencyResource(BaseResource):
    """Access to the ``/v1/residency/*`` surface.

    Not yet implemented — lands in Phase 5.
    """

    def classify(self, **body: object) -> object:
        raise NotImplementedError("ResidencyResource lands in Phase 5")
