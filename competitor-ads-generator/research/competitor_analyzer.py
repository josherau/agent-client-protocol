"""Analyze competitor ads to extract winning patterns."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from models.ad_creative import CompetitorAd

logger = logging.getLogger(__name__)


@dataclass
class AdPattern:
    """A pattern extracted from top-performing competitor ads."""

    hook_style: str  # e.g., "question", "stat", "pain_point", "benefit"
    tone: str  # e.g., "urgent", "casual", "professional"
    cta_style: str
    avg_text_length: int
    common_phrases: list[str] = field(default_factory=list)
    example_ad_ids: list[str] = field(default_factory=list)


@dataclass
class CompetitorInsights:
    """Aggregated insights from competitor ad analysis."""

    total_ads_analyzed: int
    top_performers: list[CompetitorAd]
    patterns: list[AdPattern]
    common_hooks: list[str]
    common_ctas: list[str]
    avg_text_length: int
    platform_distribution: dict[str, int]


class CompetitorAnalyzer:
    """Analyzes competitor ads to find winning patterns and seed ideas."""

    def __init__(self, min_performance_score: float = 40.0) -> None:
        self.min_performance_score = min_performance_score

    def analyze(self, ads: list[CompetitorAd]) -> CompetitorInsights:
        """Run full analysis on a set of competitor ads."""
        logger.info(f"Analyzing {len(ads)} competitor ads")

        # Sort by performance score
        ranked = sorted(ads, key=lambda a: a.performance_score, reverse=True)

        # Get top performers
        top_performers = [
            ad for ad in ranked if ad.performance_score >= self.min_performance_score
        ]
        if not top_performers:
            # Fallback: take top 20%
            cutoff = max(1, len(ranked) // 5)
            top_performers = ranked[:cutoff]

        logger.info(f"Found {len(top_performers)} top-performing ads")

        # Extract patterns
        patterns = self._extract_patterns(top_performers)
        hooks = self._extract_hooks(top_performers)
        ctas = self._extract_ctas(top_performers)
        avg_length = self._avg_text_length(top_performers)
        platform_dist = self._platform_distribution(ads)

        return CompetitorInsights(
            total_ads_analyzed=len(ads),
            top_performers=top_performers,
            patterns=patterns,
            common_hooks=hooks,
            common_ctas=ctas,
            avg_text_length=avg_length,
            platform_distribution=platform_dist,
        )

    def get_seed_ads(
        self, insights: CompetitorInsights, count: int = 10
    ) -> list[CompetitorAd]:
        """Select the best seed ads for creative generation."""
        return insights.top_performers[:count]

    def _extract_patterns(self, ads: list[CompetitorAd]) -> list[AdPattern]:
        """Extract common patterns from top ads."""
        patterns: list[AdPattern] = []

        # Group by hook style
        question_ads = [a for a in ads if "?" in a.ad_text[:100]]
        if question_ads:
            patterns.append(
                AdPattern(
                    hook_style="question",
                    tone="engaging",
                    cta_style=question_ads[0].cta_text,
                    avg_text_length=self._avg_text_length(question_ads),
                    example_ad_ids=[a.ad_id for a in question_ads[:3]],
                )
            )

        # Stat/number-led ads
        stat_ads = [a for a in ads if any(c.isdigit() for c in a.ad_text[:50])]
        if stat_ads:
            patterns.append(
                AdPattern(
                    hook_style="statistic",
                    tone="authoritative",
                    cta_style=stat_ads[0].cta_text,
                    avg_text_length=self._avg_text_length(stat_ads),
                    example_ad_ids=[a.ad_id for a in stat_ads[:3]],
                )
            )

        # Short-form urgency ads
        urgent_keywords = ["now", "today", "limited", "last chance", "don't miss"]
        urgent_ads = [
            a
            for a in ads
            if any(kw in a.ad_text.lower() for kw in urgent_keywords)
        ]
        if urgent_ads:
            patterns.append(
                AdPattern(
                    hook_style="urgency",
                    tone="urgent",
                    cta_style=urgent_ads[0].cta_text,
                    avg_text_length=self._avg_text_length(urgent_ads),
                    example_ad_ids=[a.ad_id for a in urgent_ads[:3]],
                )
            )

        # Benefit-led ads (contain words like "get", "achieve", "unlock")
        benefit_keywords = ["get", "achieve", "unlock", "discover", "transform"]
        benefit_ads = [
            a
            for a in ads
            if any(kw in a.ad_text.lower() for kw in benefit_keywords)
        ]
        if benefit_ads:
            patterns.append(
                AdPattern(
                    hook_style="benefit",
                    tone="aspirational",
                    cta_style=benefit_ads[0].cta_text,
                    avg_text_length=self._avg_text_length(benefit_ads),
                    example_ad_ids=[a.ad_id for a in benefit_ads[:3]],
                )
            )

        return patterns

    def _extract_hooks(self, ads: list[CompetitorAd]) -> list[str]:
        """Extract the opening hooks from top ads."""
        hooks = []
        for ad in ads:
            text = ad.ad_text.strip()
            # Take first sentence or first 100 chars
            first_sentence = text.split(".")[0].split("!")[0].split("?")[0]
            if first_sentence:
                hooks.append(first_sentence[:150])
        return hooks[:20]

    def _extract_ctas(self, ads: list[CompetitorAd]) -> list[str]:
        """Extract unique CTAs from top ads."""
        ctas = list({ad.cta_text for ad in ads if ad.cta_text})
        return ctas[:10]

    def _avg_text_length(self, ads: list[CompetitorAd]) -> int:
        if not ads:
            return 0
        return sum(len(a.ad_text) for a in ads) // len(ads)

    def _platform_distribution(self, ads: list[CompetitorAd]) -> dict[str, int]:
        dist: dict[str, int] = {}
        for ad in ads:
            for platform in ad.platforms:
                dist[platform] = dist.get(platform, 0) + 1
        return dist
