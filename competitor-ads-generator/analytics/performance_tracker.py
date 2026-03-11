"""Track ad performance by polling Meta Insights API."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta

from facebook_business.adobjects.ad import Ad as MetaAd
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.campaign import Campaign as MetaCampaign

from meta_ads.auth import MetaAuth
from models.performance import AdPerformance, PerformanceReport

logger = logging.getLogger(__name__)

INSIGHT_FIELDS = [
    "ad_id",
    "impressions",
    "clicks",
    "spend",
    "actions",
    "action_values",
    "reach",
    "frequency",
    "ctr",
    "cpc",
    "cpm",
]


class PerformanceTracker:
    """Polls Meta Insights API for ad performance data."""

    def __init__(self, auth: MetaAuth) -> None:
        self.auth = auth

    @property
    def account(self) -> AdAccount:
        return self.auth.ad_account

    def get_ad_performance(
        self,
        ad_id: str,
        days_back: int = 7,
    ) -> AdPerformance:
        """Get performance data for a single ad."""
        ad = MetaAd(ad_id)
        date_preset = self._days_to_preset(days_back)

        insights = ad.get_insights(
            fields=INSIGHT_FIELDS,
            params={"date_preset": date_preset},
        )

        if not insights:
            return AdPerformance(ad_id=ad_id, creative_id="")

        return self._parse_insight(insights[0], ad_id)

    def get_campaign_performance(
        self,
        campaign_id: str,
        days_back: int = 7,
    ) -> PerformanceReport:
        """Get performance data for all ads in a campaign."""
        campaign = MetaCampaign(campaign_id)
        date_preset = self._days_to_preset(days_back)

        insights = campaign.get_insights(
            fields=INSIGHT_FIELDS,
            params={
                "date_preset": date_preset,
                "level": "ad",
            },
        )

        performances = []
        for insight in insights:
            ad_id = insight.get("ad_id", "")
            perf = self._parse_insight(insight, ad_id)
            performances.append(perf)

        return PerformanceReport(
            report_id=f"rpt-{uuid.uuid4().hex[:12]}",
            campaign_id=campaign_id,
            ad_performances=performances,
            period_start=datetime.now() - timedelta(days=days_back),
            period_end=datetime.now(),
        )

    def get_account_performance(
        self,
        days_back: int = 7,
    ) -> PerformanceReport:
        """Get performance across the entire ad account."""
        date_preset = self._days_to_preset(days_back)

        insights = self.account.get_insights(
            fields=INSIGHT_FIELDS,
            params={
                "date_preset": date_preset,
                "level": "ad",
            },
        )

        performances = []
        for insight in insights:
            ad_id = insight.get("ad_id", "")
            perf = self._parse_insight(insight, ad_id)
            performances.append(perf)

        return PerformanceReport(
            report_id=f"rpt-{uuid.uuid4().hex[:12]}",
            ad_performances=performances,
            period_start=datetime.now() - timedelta(days=days_back),
            period_end=datetime.now(),
        )

    def _parse_insight(self, insight: dict, ad_id: str) -> AdPerformance:
        """Parse a Meta Insights API response into AdPerformance."""
        # Extract conversions from actions
        conversions = 0
        revenue = 0.0
        actions = insight.get("actions", [])
        for action in actions:
            if action.get("action_type") in (
                "offsite_conversion",
                "purchase",
                "complete_registration",
                "lead",
            ):
                conversions += int(action.get("value", 0))

        action_values = insight.get("action_values", [])
        for av in action_values:
            if av.get("action_type") in ("offsite_conversion", "purchase"):
                revenue += float(av.get("value", 0))

        return AdPerformance(
            ad_id=ad_id,
            creative_id="",  # Will be mapped by the caller
            impressions=int(insight.get("impressions", 0)),
            clicks=int(insight.get("clicks", 0)),
            spend=float(insight.get("spend", 0)),
            conversions=conversions,
            revenue=revenue,
            reach=int(insight.get("reach", 0)),
            frequency=float(insight.get("frequency", 0)),
        )

    def _days_to_preset(self, days: int) -> str:
        """Map days back to a Meta date preset."""
        presets = {
            1: "today",
            3: "last_3d",
            7: "last_7d",
            14: "last_14d",
            28: "last_28d",
            30: "last_30d",
            90: "last_90d",
        }
        # Find closest preset
        for threshold, preset in sorted(presets.items()):
            if days <= threshold:
                return preset
        return "last_30d"
