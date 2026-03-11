"""Application configuration and API credentials."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class MetaAdsConfig:
    """Meta Marketing API configuration."""

    app_id: str = field(default_factory=lambda: os.environ.get("META_APP_ID", ""))
    app_secret: str = field(
        default_factory=lambda: os.environ.get("META_APP_SECRET", "")
    )
    access_token: str = field(
        default_factory=lambda: os.environ.get("META_ACCESS_TOKEN", "")
    )
    ad_account_id: str = field(
        default_factory=lambda: os.environ.get("META_AD_ACCOUNT_ID", "")
    )
    page_id: str = field(default_factory=lambda: os.environ.get("META_PAGE_ID", ""))
    api_version: str = "v21.0"


@dataclass
class ClaudeConfig:
    """Anthropic Claude API configuration."""

    api_key: str = field(
        default_factory=lambda: os.environ.get("ANTHROPIC_API_KEY", "")
    )
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4096


@dataclass
class OptimizationThresholds:
    """Performance thresholds for auto-optimization decisions."""

    # Kill thresholds — pause ad if worse than these
    min_ctr: float = 0.005  # 0.5%
    max_cpa_multiplier: float = 2.0  # 2x target CPA
    min_roas: float = 1.0
    max_frequency: float = 4.0
    min_impressions_before_decision: int = 1000

    # Scale thresholds — increase budget if better than these
    scale_ctr: float = 0.02  # 2.0%
    scale_cpa_multiplier: float = 0.7  # 0.7x target CPA
    scale_roas: float = 3.0

    # Target metrics
    target_cpa: float = 25.0  # dollars
    target_roas: float = 2.0


@dataclass
class GenerationConfig:
    """Creative generation settings."""

    total_creatives: int = 100
    single_image_count: int = 40
    carousel_count: int = 30
    video_script_count: int = 20
    story_reel_count: int = 10
    max_parallel_generations: int = 10


@dataclass
class SchedulerConfig:
    """Optimization loop schedule."""

    analytics_poll_interval_hours: int = 6
    optimization_check_interval_hours: int = 24
    iteration_batch_size: int = 10


@dataclass
class AppConfig:
    """Root application configuration."""

    meta: MetaAdsConfig = field(default_factory=MetaAdsConfig)
    claude: ClaudeConfig = field(default_factory=ClaudeConfig)
    thresholds: OptimizationThresholds = field(default_factory=OptimizationThresholds)
    generation: GenerationConfig = field(default_factory=GenerationConfig)
    scheduler: SchedulerConfig = field(default_factory=SchedulerConfig)
    db_path: str = "ads_data.db"


def load_config() -> AppConfig:
    """Load configuration from environment variables."""
    return AppConfig()
