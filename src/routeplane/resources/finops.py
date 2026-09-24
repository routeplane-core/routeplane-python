"""FinOps usage/cost namespace (``/v1/finops/*``)."""

from __future__ import annotations

import math
import warnings
from datetime import datetime
from typing import Literal, Optional, TypedDict

from ._base import BaseResource, prune_none

__all__ = [
    "CacheSavings",
    "DailyPricingEvidence",
    "DailyUsageReport",
    "FinopsResource",
    "SaverMetrics",
    "TimeseriesData",
    "UsageData",
]


class FinOpsUsageTotals(TypedDict):
    requests: int
    successful_requests: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_micro_usd: int
    cost_by_currency: dict[str, int]


class _FinOpsLatencyRequired(TypedDict):
    count: int


class FinOpsLatencyPercentiles(_FinOpsLatencyRequired, total=False):
    p50_ms: int
    p95_ms: int
    p99_ms: int
    max_ms: int


class _UsageDataRequired(TypedDict):
    tenant_id: str
    window: int
    events_matched: int
    totals: FinOpsUsageTotals
    by_model: dict[str, FinOpsUsageTotals]
    by_key: dict[str, FinOpsUsageTotals]
    latency: FinOpsLatencyPercentiles


class UsageData(_UsageDataRequired, total=False):
    by_use_case: dict[str, FinOpsUsageTotals]


class DailyModelUsage(TypedDict):
    provider: str
    model: str
    requests: int
    errors: int
    total_tokens: int
    cost_micro_usd: Optional[int]
    pricing: "DailyPricingEvidence"


class DailyKeyUsage(DailyModelUsage):
    key: str
    prompt_tokens: int
    completion_tokens: int
    cost_inr_paise: Optional[int]


DailyPricingSource = TypedDict(
    "DailyPricingSource",
    {
        "class": Literal["durable_rollup"],
        "systems": list[Literal["telemetry_rung_1"]],
        "schema_version": Literal["routeplane.finops.cost.v1"],
    },
)


class DailyPricingCoverage(TypedDict):
    eligible_count: int
    observed_count: int
    priced_count: int
    unpriced_count: int
    invalid_pricing_count: int
    versioned_priced_count: int
    pricing_coverage_state: Literal["known", "legacy_unknown", "corrupt"]
    pricing_book_versions: list[str]
    pricing_book_versions_truncated: bool
    numeric_overflowed: bool
    missing_reasons: list[str]


class DailyPricingComponentCoverage(TypedDict):
    input_output_split_available: bool
    inr_view_available: bool


class DailyPricingEvidence(TypedDict):
    data_state: Literal["live", "partial", "unavailable"]
    availability: Literal["available", "partial", "unavailable"]
    value: Optional[int]
    unit: Literal["micro_currency"]
    currency: Literal["USD"]
    scale: Literal[6]
    cost_status: Literal["estimated", "unpriced", "unavailable"]
    source: DailyPricingSource
    coverage: DailyPricingCoverage
    component_coverage: DailyPricingComponentCoverage


class DailyLatency(TypedDict):
    p50: Optional[float]
    p95: Optional[float]
    p99: Optional[float]


class DailyUsageTotals(TypedDict):
    requests: int
    errors: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_micro_usd: Optional[int]
    input_cost_micro_usd: Optional[int]
    output_cost_micro_usd: Optional[int]
    cost_inr_paise: Optional[int]
    pricing: DailyPricingEvidence


class DailyUsage(DailyUsageTotals):
    date: str
    streaming: int
    sovereign_routed: int
    latency_ms: DailyLatency
    by_model: list[DailyModelUsage]
    by_key: list[DailyKeyUsage]


class TimeseriesBucket(TypedDict):
    ts: str
    requests: int
    errors: int
    cost_micro_usd: int
    tokens: int
    avg_latency_ms: int


class TimeseriesData(TypedDict):
    tenant_id: str
    window_mins: int
    window_secs: int
    bucket_secs: int
    total_events_in_window: int
    buckets: list[TimeseriesBucket]
    note: str


class CacheSavings(TypedDict):
    tenant_id: str
    window_mins: int
    cache_hits: int
    cacheable_lookups: int
    saved_cost_micro_usd: int
    saved_tokens: int
    note: str


class SaverCache(TypedDict):
    hits: int
    misses: int
    cacheable_lookups: int
    hit_rate: float
    saved_cost_micro_usd: int
    saved_tokens: int


class SaverTenant(TypedDict):
    cache: SaverCache
    note: str


class SaverMetrics(TypedDict):
    tenant_id: str
    window_mins: int
    tenant: SaverTenant
    not_instrumented: dict[str, str]


# Durable daily estimated usage; not a provider invoice or reconciled bill.
# Functional syntax is required because `from` is a Python keyword but is the
# exact JSON field name on the wire.
DailyUsageReport = TypedDict(
    "DailyUsageReport",
    {
        "tenant_id": str,
        "from": str,
        "to": str,
        "days": list[DailyUsage],
        "totals": DailyUsageTotals,
        "note": str,
    },
)


def _legacy_window_mins(from_date: str, to_date: str) -> int:
    """Convert a legacy absolute range to the relative window the server supports."""

    def parse(value: str) -> datetime:
        try:
            # Python 3.9's fromisoformat does not accept the common trailing Z.
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("legacy timeseries dates must be ISO-8601 values") from exc

    start = parse(from_date)
    end = parse(to_date)
    try:
        seconds = (end - start).total_seconds()
    except TypeError as exc:
        raise ValueError("legacy timeseries dates must use compatible timezones") from exc
    if seconds < 0:
        raise ValueError("legacy timeseries from_date must not be after to_date")
    return max(1, math.ceil(seconds / 60))


class FinopsResource(BaseResource):
    """Usage rollups, cost time-series, and cost-saver metrics."""

    def usage(self) -> UsageData:
        """``GET /v1/finops/usage`` — recent process-local estimated usage."""
        data: UsageData = self._get("finops/usage").json()
        return data

    def usage_daily(
        self,
        *,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> DailyUsageReport:
        """Return the complete durable daily report envelope.

        The response retains its tenant/date scope, totals, and provenance note;
        monetary fields are null unless the adjacent pricing evidence proves
        complete, versioned coverage. A fully priced zero remains numeric zero;
        costs are gateway price-book estimates, not billed or reconciled amounts.
        """
        params = prune_none({"from": from_date, "to": to_date})
        data: DailyUsageReport = self._get("finops/usage/daily", params=params).json()
        return data

    def timeseries(
        self,
        *,
        window_mins: Optional[int] = None,
        buckets: Optional[int] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> TimeseriesData:
        """Return the recent process-local cost/usage time series.

        ``window_mins`` and ``buckets`` are the gateway's native query contract.
        The legacy ``from_date``/``to_date`` pair remains accepted for source
        compatibility, but is converted to a relative duration and emits a
        :class:`DeprecationWarning`; it cannot select absolute durable history.
        """
        if from_date is not None or to_date is not None:
            if window_mins is not None or buckets is not None:
                raise ValueError("do not combine timeseries date-range and window options")
            if from_date is None or to_date is None:
                raise ValueError("legacy timeseries ranges require both from_date and to_date")
            warnings.warn(
                "timeseries(from_date=..., to_date=...) is deprecated; use window_mins=...",
                DeprecationWarning,
                stacklevel=2,
            )
            window_mins = _legacy_window_mins(from_date, to_date)
        params = prune_none({"window_mins": window_mins, "buckets": buckets})
        data: TimeseriesData = self._get("finops/timeseries", params=params).json()
        return data

    def cache_savings(self) -> CacheSavings:
        """``GET /v1/finops/cache-savings`` — spend avoided by the response cache."""
        data: CacheSavings = self._get("finops/cache-savings").json()
        return data

    def saver_metrics(self) -> SaverMetrics:
        """Return recent cache saver metrics plus explicit uninstrumented reasons."""
        data: SaverMetrics = self._get("finops/saver-metrics").json()
        return data
