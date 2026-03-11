"""Score ads and make optimization decisions."""

from __future__ import annotations

import logging

from config.settings import OptimizationThresholds
from models.performance import AdPerformance, OptimizationAction, OptimizationDecision

logger = logging.getLogger(__name__)


class AdScorer:
    """Scores ad performance and recommends optimization actions."""

    def __init__(self, thresholds: OptimizationThresholds) -> None:
        self.thresholds = thresholds

    def score_ad(self, perf: AdPerformance) -> OptimizationDecision:
        """Score a single ad and return an optimization decision."""
        # Not enough data yet
        if perf.impressions < self.thresholds.min_impressions_before_decision:
            return OptimizationDecision(
                ad_id=perf.ad_id,
                creative_id=perf.creative_id,
                action=OptimizationAction.KEEP,
                reason=f"Insufficient data ({perf.impressions} impressions, "
                f"need {self.thresholds.min_impressions_before_decision})",
                performance=perf,
            )

        # Check kill conditions
        kill_reasons = self._check_kill_conditions(perf)
        if kill_reasons:
            return OptimizationDecision(
                ad_id=perf.ad_id,
                creative_id=perf.creative_id,
                action=OptimizationAction.PAUSE,
                reason=f"Kill: {'; '.join(kill_reasons)}",
                performance=perf,
            )

        # Check scale conditions
        scale_reasons = self._check_scale_conditions(perf)
        if len(scale_reasons) >= 2:  # Need at least 2 scale signals
            return OptimizationDecision(
                ad_id=perf.ad_id,
                creative_id=perf.creative_id,
                action=OptimizationAction.ITERATE,
                reason=f"Winner — iterate: {'; '.join(scale_reasons)}",
                performance=perf,
            )

        if scale_reasons:
            return OptimizationDecision(
                ad_id=perf.ad_id,
                creative_id=perf.creative_id,
                action=OptimizationAction.SCALE_UP,
                reason=f"Performing well: {'; '.join(scale_reasons)}",
                performance=perf,
            )

        # Default: keep running
        return OptimizationDecision(
            ad_id=perf.ad_id,
            creative_id=perf.creative_id,
            action=OptimizationAction.KEEP,
            reason="Performing within acceptable range",
            performance=perf,
        )

    def score_batch(
        self, performances: list[AdPerformance]
    ) -> list[OptimizationDecision]:
        """Score a batch of ads."""
        decisions = [self.score_ad(p) for p in performances]

        # Log summary
        action_counts = {}
        for d in decisions:
            action_counts[d.action] = action_counts.get(d.action, 0) + 1

        logger.info(
            f"Scored {len(decisions)} ads: "
            + ", ".join(f"{a.value}={c}" for a, c in action_counts.items())
        )

        return decisions

    def rank_by_performance(
        self, performances: list[AdPerformance]
    ) -> list[AdPerformance]:
        """Rank ads from best to worst performing."""
        # Composite score: weighted combination of key metrics
        def composite_score(p: AdPerformance) -> float:
            score = 0.0
            score += p.ctr * 100  # Weight CTR heavily
            if p.cpa < float("inf"):
                # Lower CPA is better, invert it
                target = self.thresholds.target_cpa
                score += max(0, (target - p.cpa) / target) * 50
            score += min(p.roas, 10) * 10  # Cap ROAS contribution
            # Penalize high frequency
            if p.frequency > self.thresholds.max_frequency:
                score -= 20
            return score

        return sorted(performances, key=composite_score, reverse=True)

    def _check_kill_conditions(self, perf: AdPerformance) -> list[str]:
        reasons = []

        if perf.ctr < self.thresholds.min_ctr:
            reasons.append(f"CTR {perf.ctr:.3%} < {self.thresholds.min_ctr:.1%}")

        if (
            perf.cpa < float("inf")
            and perf.cpa > self.thresholds.target_cpa * self.thresholds.max_cpa_multiplier
        ):
            reasons.append(
                f"CPA ${perf.cpa:.2f} > "
                f"${self.thresholds.target_cpa * self.thresholds.max_cpa_multiplier:.2f}"
            )

        if perf.spend > 0 and perf.roas < self.thresholds.min_roas and perf.revenue > 0:
            reasons.append(f"ROAS {perf.roas:.2f}x < {self.thresholds.min_roas}x")

        if perf.frequency > self.thresholds.max_frequency:
            reasons.append(
                f"Frequency {perf.frequency:.1f} > {self.thresholds.max_frequency}"
            )

        return reasons

    def _check_scale_conditions(self, perf: AdPerformance) -> list[str]:
        reasons = []

        if perf.ctr > self.thresholds.scale_ctr:
            reasons.append(f"CTR {perf.ctr:.3%} > {self.thresholds.scale_ctr:.1%}")

        if (
            perf.cpa < float("inf")
            and perf.cpa < self.thresholds.target_cpa * self.thresholds.scale_cpa_multiplier
        ):
            reasons.append(
                f"CPA ${perf.cpa:.2f} < "
                f"${self.thresholds.target_cpa * self.thresholds.scale_cpa_multiplier:.2f}"
            )

        if perf.roas > self.thresholds.scale_roas:
            reasons.append(f"ROAS {perf.roas:.2f}x > {self.thresholds.scale_roas}x")

        return reasons
