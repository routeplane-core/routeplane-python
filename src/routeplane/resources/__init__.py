"""Non-OpenAI endpoint namespaces.

Only :class:`StatusResource` is implemented in Phase 1; the rest are stubs that
land in Phase 5.
"""

from ._base import BaseResource
from .cache import CacheResource
from .feedback import FeedbackResource
from .finops import FinopsResource
from .logs import LogsResource
from .mcp import McpResource
from .prompts import PromptsResource
from .residency import ResidencyResource
from .status import StatusResource

__all__ = [
    "BaseResource",
    "CacheResource",
    "FeedbackResource",
    "FinopsResource",
    "LogsResource",
    "McpResource",
    "PromptsResource",
    "ResidencyResource",
    "StatusResource",
]
