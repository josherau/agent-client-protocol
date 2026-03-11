"""Application configuration and API credentials."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the competitor-ads-generator directory
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)


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
class CompetitorPage:
    """A single competitor's Facebook page info."""

    name: str
    page_slug: str  # Facebook page username/slug
    page_id: str = ""  # Numerical ID — set via Meta Graph API lookup
    website: str = ""
    notes: str = ""


@dataclass
class CompetitorConfig:
    """Competitor pages to research in the Ad Library."""

    competitors: list[CompetitorPage] = field(
        default_factory=lambda: [
            CompetitorPage(
                name="Positive Performance — Lindsey Wilson",
                page_slug="positiveperformance",
                website="https://www.positiveperformancetraining.com",
                notes="Mental training programs for athletes & teams. "
                "Mindset Coach Academy certification. Former WNBA/pro player.",
            ),
            CompetitorPage(
                name="Brian Cain Peak Performance",
                page_slug="briancainpeak",
                website="https://briancain.com",
                notes="#1 best-selling author. MPM certification creator. "
                "Works with UFC, MLB, NFL, NCAA champions.",
            ),
            CompetitorPage(
                name="Dr. Michael Gervais — Finding Mastery",
                page_slug="drmichaelgervais",
                website="https://findingmastery.com",
                notes="High performance psychologist. Seattle Seahawks, "
                "Olympians, Fortune 50 CEOs. Finding Mastery podcast.",
            ),
            CompetitorPage(
                name="Dr. Jason Selk",
                page_slug="jasonselk",
                website="https://www.jasonselk.com",
                notes="Former Director of Mental Training, St. Louis Cardinals "
                "(2 World Series). Level Up app co-founder. 5x bestselling author.",
            ),
            CompetitorPage(
                name="Brandon Epstein",
                page_slug="brandontepstein",
                website="https://thebrandonepstein.com",
                notes="High-performance mental coach. Former exec coach for "
                "Gary Vaynerchuk. NFL, MLB, NHL, UFC clients. 85K on IG.",
            ),
            CompetitorPage(
                name="Dr. Cassidy Preston — CEP Mindset",
                page_slug="CEPMindset",
                website="https://cepmindset.com",
                notes="PhD Sport & Performance Psychology. 20+ coaches on staff. "
                "One of largest mental performance firms in North America. "
                "Hockey roots. Author of Mindset First.",
            ),
            CompetitorPage(
                name="Jeff Troesch",
                page_slug="",  # No Facebook page found
                website="https://www.jasonselk.com",
                notes="40 years experience. NBA, MLB, LPGA, PGA, NCAA. "
                "US Solheim Cup 2022 mental consultant. Author of One Day Better. "
                "No Facebook page found — research via keyword search only.",
            ),
        ]
    )
    search_keywords: list[str] = field(
        default_factory=lambda: [
            "mental performance coaching athletes",
            "sports mental toughness training",
            "athlete mindset coaching",
        ]
    )

    @property
    def page_ids(self) -> list[str]:
        """Return only competitors with numerical page IDs set."""
        return [c.page_id for c in self.competitors if c.page_id]

    @property
    def page_slugs(self) -> list[str]:
        """Return all competitor page slugs."""
        return [c.page_slug for c in self.competitors]


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
    competitors: CompetitorConfig = field(default_factory=CompetitorConfig)
    thresholds: OptimizationThresholds = field(default_factory=OptimizationThresholds)
    generation: GenerationConfig = field(default_factory=GenerationConfig)
    scheduler: SchedulerConfig = field(default_factory=SchedulerConfig)
    db_path: str = "ads_data.db"


def load_config() -> AppConfig:
    """Load configuration from environment variables."""
    return AppConfig()
