"""Automated decision engine for ad optimization."""

from __future__ import annotations

import logging

from analytics.performance_tracker import PerformanceTracker
from analytics.reporter import PerformanceReporter
from analytics.scorer import AdScorer
from config.settings import OptimizationThresholds
from meta_ads.campaign_manager import CampaignManager
from models.performance import OptimizationAction, OptimizationDecision

logger = logging.getLogger(__name__)


class DecisionEngine:
    """Makes and executes optimization decisions automatically."""

    def __init__(
        self,
        tracker: PerformanceTracker,
        scorer: AdScorer,
        campaign_manager: CampaignManager,
        reporter: PerformanceReporter,
    ) -> None:
        self.tracker = tracker
        self.scorer = scorer
        self.campaign_manager = campaign_manager
        self.reporter = reporter

    def run_optimization_cycle(
        self,
        campaign_id: str,
        days_back: int = 7,
        dry_run: bool = False,
    ) -> list[OptimizationDecision]:
        """Run a full optimization cycle for a campaign.

        1. Pull performance data
        2. Score all ads
        3. Execute decisions (pause/scale)
        4. Return decisions for iteration

        Args:
            campaign_id: The Meta campaign ID to optimize
            days_back: How many days of data to analyze
            dry_run: If True, don't execute changes, just return decisions
        """
        logger.info(f"Running optimization cycle for campaign {campaign_id}")

        # 1. Get performance data
        report = self.tracker.get_campaign_performance(campaign_id, days_back)
        logger.info(f"Retrieved performance for {len(report.ad_performances)} ads")

        # 2. Score all ads
        decisions = self.scorer.score_batch(report.ad_performances)

        # 3. Log the decision report
        decision_report = self.reporter.generate_decision_report(decisions)
        logger.info(f"\n{decision_report}")

        # 4. Execute decisions
        if not dry_run:
            self._execute_decisions(decisions)
        else:
            logger.info("DRY RUN — no changes executed")

        return decisions

    def get_winners(
        self, decisions: list[OptimizationDecision]
    ) -> list[OptimizationDecision]:
        """Get ads that should be iterated on (top performers)."""
        return [
            d
            for d in decisions
            if d.action in (OptimizationAction.ITERATE, OptimizationAction.SCALE_UP)
        ]

    def get_losers(
        self, decisions: list[OptimizationDecision]
    ) -> list[OptimizationDecision]:
        """Get ads that should be paused."""
        return [d for d in decisions if d.action == OptimizationAction.PAUSE]

    def _execute_decisions(self, decisions: list[OptimizationDecision]) -> None:
        """Execute optimization decisions via the Meta API."""
        paused = 0
        scaled = 0

        for decision in decisions:
            try:
                if decision.action == OptimizationAction.PAUSE:
                    self.campaign_manager.pause_ad(decision.ad_id)
                    paused += 1

                elif decision.action == OptimizationAction.SCALE_UP:
                    # Scale up by activating and potentially increasing budget
                    self.campaign_manager.activate_ad(decision.ad_id)
                    scaled += 1

            except Exception as e:
                logger.error(
                    f"Failed to execute {decision.action.value} "
                    f"for ad {decision.ad_id}: {e}"
                )

        logger.info(f"Executed: {paused} paused, {scaled} scaled up")
