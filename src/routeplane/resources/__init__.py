"""Non-OpenAI endpoint namespaces.

The OpenAI-shaped surfaces (chat, embeddings, …) are served by the inherited
``openai`` client; everything Routeplane adds on top lives here as a small
``httpx``-backed :class:`BaseResource` subclass.
"""

from ._base import BaseResource
from .analytics import AnalyticsResource
from .cache import CacheResource
from .feedback import FeedbackResource
from .finops import (
    CacheSavings,
    DailyPricingEvidence,
    DailyUsageReport,
    FinopsResource,
    SaverMetrics,
    TimeseriesData,
    UsageData,
)
from .logs import LogsResource
from .mcp import Decision, McpResource, RunStep
from .models import ModelsResource
from .prompts import PromptsResource
from .providers import ProvidersResource
from .residency import ResidencyResource
from .status import StatusResource

__all__ = [
    "BaseResource",
    "AnalyticsResource",
    "CacheResource",
    "CacheSavings",
    "DailyPricingEvidence",
    "Decision",
    "DailyUsageReport",
    "FeedbackResource",
    "FinopsResource",
    "LogsResource",
    "McpResource",
    "RunStep",
    "SaverMetrics",
    "TimeseriesData",
    "UsageData",
    "ModelsResource",
    "PromptsResource",
    "ProvidersResource",
    "ResidencyResource",
    "StatusResource",
]
