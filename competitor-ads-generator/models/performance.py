"""Data models for ad performance metrics."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class OptimizationAction(str, Enum):
    KEEP = "keep"
    PAUSE = "pause"
    SCALE_UP = "scale_up"
    ITERATE = "iterate"


class AdPerformance(BaseModel):
    """Performance snapshot for a single ad."""

    ad_id: str
    creative_id: str
    impressions: int = 0
    clicks: int = 0
    spend: float = 0.0
    conversions: int = 0
    revenue: float = 0.0
    reach: int = 0
    frequency: float = 0.0
    recorded_at: datetime = Field(default_factory=datetime.now)

    @property
    def ctr(self) -> float:
        """Click-through rate."""
        return self.clicks / self.impressions if self.impressions > 0 else 0.0

    @property
    def cpc(self) -> float:
        """Cost per click."""
        return self.spend / self.clicks if self.clicks > 0 else 0.0

    @property
    def cpm(self) -> float:
        """Cost per 1000 impressions."""
        return (self.spend / self.impressions * 1000) if self.impressions > 0 else 0.0

    @property
    def cpa(self) -> float:
        """Cost per acquisition/conversion."""
        return self.spend / self.conversions if self.conversions > 0 else float("inf")

    @property
    def roas(self) -> float:
        """Return on ad spend."""
        return self.revenue / self.spend if self.spend > 0 else 0.0


class PerformanceReport(BaseModel):
    """Aggregated performance report for a campaign or time period."""

    report_id: str
    campaign_id: str | None = None
    ad_performances: list[AdPerformance] = Field(default_factory=list)
    period_start: datetime | None = None
    period_end: datetime | None = None
    generated_at: datetime = Field(default_factory=datetime.now)

    @property
    def total_spend(self) -> float:
        return sum(p.spend for p in self.ad_performances)

    @property
    def total_impressions(self) -> int:
        return sum(p.impressions for p in self.ad_performances)

    @property
    def total_conversions(self) -> int:
        return sum(p.conversions for p in self.ad_performances)

    @property
    def avg_ctr(self) -> float:
        total_impressions = self.total_impressions
        total_clicks = sum(p.clicks for p in self.ad_performances)
        return total_clicks / total_impressions if total_impressions > 0 else 0.0

    @property
    def avg_cpa(self) -> float:
        total_conversions = self.total_conversions
        return (
            self.total_spend / total_conversions if total_conversions > 0 else float("inf")
        )


class OptimizationDecision(BaseModel):
    """Decision made by the optimization engine for a specific ad."""

    ad_id: str
    creative_id: str
    action: OptimizationAction
    reason: str
    performance: AdPerformance
    decided_at: datetime = Field(default_factory=datetime.now)
