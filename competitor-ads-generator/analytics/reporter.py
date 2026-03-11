"""Generate performance reports."""

from __future__ import annotations

import logging
from datetime import datetime

from models.performance import AdPerformance, OptimizationDecision, PerformanceReport

logger = logging.getLogger(__name__)


class PerformanceReporter:
    """Generates human-readable performance reports."""

    def generate_summary(self, report: PerformanceReport) -> str:
        """Generate a summary report."""
        lines = [
            "=" * 60,
            f"  PERFORMANCE REPORT — {report.generated_at:%Y-%m-%d %H:%M}",
            "=" * 60,
            "",
            f"Period: {report.period_start:%Y-%m-%d} to {report.period_end:%Y-%m-%d}"
            if report.period_start and report.period_end
            else "",
            f"Total Ads: {len(report.ad_performances)}",
            f"Total Spend: ${report.total_spend:,.2f}",
            f"Total Impressions: {report.total_impressions:,}",
            f"Total Conversions: {report.total_conversions:,}",
            f"Average CTR: {report.avg_ctr:.2%}",
            f"Average CPA: ${report.avg_cpa:,.2f}"
            if report.avg_cpa < float("inf")
            else "Average CPA: N/A",
            "",
        ]

        # Top 5 performers
        sorted_perf = sorted(
            report.ad_performances,
            key=lambda p: p.ctr,
            reverse=True,
        )

        if sorted_perf:
            lines.append("TOP 5 PERFORMERS (by CTR):")
            lines.append("-" * 40)
            for p in sorted_perf[:5]:
                lines.append(
                    f"  Ad {p.ad_id}: CTR={p.ctr:.2%} | "
                    f"CPA=${p.cpa:.2f}" if p.cpa < float("inf") else f"CPA=N/A"
                    f" | Spend=${p.spend:.2f}"
                )
            lines.append("")

        # Bottom 5 performers
        if len(sorted_perf) > 5:
            lines.append("BOTTOM 5 PERFORMERS (by CTR):")
            lines.append("-" * 40)
            for p in sorted_perf[-5:]:
                lines.append(
                    f"  Ad {p.ad_id}: CTR={p.ctr:.2%} | "
                    f"Spend=${p.spend:.2f}"
                )
            lines.append("")

        return "\n".join(lines)

    def generate_decision_report(
        self, decisions: list[OptimizationDecision]
    ) -> str:
        """Generate a report of optimization decisions."""
        lines = [
            "=" * 60,
            f"  OPTIMIZATION DECISIONS — {datetime.now():%Y-%m-%d %H:%M}",
            "=" * 60,
            "",
        ]

        # Group by action
        grouped: dict[str, list[OptimizationDecision]] = {}
        for d in decisions:
            key = d.action.value
            grouped.setdefault(key, []).append(d)

        for action, action_decisions in grouped.items():
            lines.append(f"[{action.upper()}] — {len(action_decisions)} ads")
            lines.append("-" * 40)
            for d in action_decisions:
                p = d.performance
                lines.append(f"  Ad {d.ad_id}:")
                lines.append(f"    Reason: {d.reason}")
                lines.append(
                    f"    Metrics: {p.impressions:,} imp | "
                    f"CTR={p.ctr:.2%} | Spend=${p.spend:.2f}"
                )
            lines.append("")

        # Summary
        lines.append("SUMMARY:")
        for action, action_decisions in grouped.items():
            lines.append(f"  {action}: {len(action_decisions)}")

        return "\n".join(lines)
