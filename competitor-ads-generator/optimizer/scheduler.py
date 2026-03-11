"""Schedule optimization loops to run automatically."""

from __future__ import annotations

import logging
from typing import Callable

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config.settings import SchedulerConfig

logger = logging.getLogger(__name__)


class OptimizationScheduler:
    """Runs optimization cycles on a configurable schedule."""

    def __init__(self, config: SchedulerConfig) -> None:
        self.config = config
        self.scheduler = BlockingScheduler()

    def schedule_analytics(self, callback: Callable[[], None]) -> None:
        """Schedule periodic analytics polling."""
        self.scheduler.add_job(
            callback,
            trigger=IntervalTrigger(hours=self.config.analytics_poll_interval_hours),
            id="analytics_poll",
            name="Poll Meta Insights API",
            replace_existing=True,
        )
        logger.info(
            f"Analytics polling scheduled every "
            f"{self.config.analytics_poll_interval_hours} hours"
        )

    def schedule_optimization(self, callback: Callable[[], None]) -> None:
        """Schedule periodic optimization checks."""
        self.scheduler.add_job(
            callback,
            trigger=IntervalTrigger(
                hours=self.config.optimization_check_interval_hours
            ),
            id="optimization_check",
            name="Run optimization cycle",
            replace_existing=True,
        )
        logger.info(
            f"Optimization checks scheduled every "
            f"{self.config.optimization_check_interval_hours} hours"
        )

    def start(self) -> None:
        """Start the scheduler (blocking)."""
        logger.info("Starting optimization scheduler...")
        try:
            self.scheduler.start()
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")

    def stop(self) -> None:
        """Stop the scheduler."""
        self.scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
