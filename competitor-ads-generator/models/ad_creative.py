"""Data models for ad creatives."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class AdFormat(str, Enum):
    SINGLE_IMAGE = "single_image"
    CAROUSEL = "carousel"
    VIDEO_SCRIPT = "video_script"
    STORY_REEL = "story_reel"


class CompetitorAd(BaseModel):
    """A competitor ad scraped from the Ad Library."""

    ad_id: str
    page_name: str
    page_id: str
    ad_text: str
    cta_text: str = ""
    format: AdFormat = AdFormat.SINGLE_IMAGE
    image_urls: list[str] = Field(default_factory=list)
    video_url: str | None = None
    started_running: datetime | None = None
    is_active: bool = True
    estimated_reach: str = ""
    platforms: list[str] = Field(default_factory=list)
    longevity_days: int = 0

    @property
    def performance_score(self) -> float:
        """Estimate performance based on longevity and activity."""
        score = 0.0
        if self.is_active:
            score += 30.0
        score += min(self.longevity_days * 0.5, 50.0)
        if len(self.platforms) > 1:
            score += 20.0
        return score


class GeneratedCreative(BaseModel):
    """A generated ad creative ready for upload."""

    creative_id: str
    seed_ad_id: str  # which competitor ad inspired this
    format: AdFormat
    headline: str
    primary_text: str
    description: str = ""
    cta: str = "Learn More"
    image_path: str | None = None
    carousel_cards: list[CarouselCard] | None = None
    video_script: str | None = None
    brand_applied: bool = False
    created_at: datetime = Field(default_factory=datetime.now)


class CarouselCard(BaseModel):
    """A single card in a carousel ad."""

    headline: str
    description: str
    image_path: str | None = None
    link_url: str = ""


# Fix forward reference
GeneratedCreative.model_rebuild()
