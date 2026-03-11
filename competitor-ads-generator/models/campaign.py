"""Data models for Meta campaign structures."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class CampaignObjective(str, Enum):
    CONVERSIONS = "OUTCOME_SALES"
    TRAFFIC = "OUTCOME_TRAFFIC"
    AWARENESS = "OUTCOME_AWARENESS"
    ENGAGEMENT = "OUTCOME_ENGAGEMENT"
    LEADS = "OUTCOME_LEADS"


class CampaignStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    DELETED = "DELETED"
    ARCHIVED = "ARCHIVED"


class Campaign(BaseModel):
    """A Meta Ads campaign."""

    campaign_id: str | None = None
    name: str
    objective: CampaignObjective = CampaignObjective.CONVERSIONS
    status: CampaignStatus = CampaignStatus.PAUSED
    daily_budget: float = 50.0  # dollars
    created_at: datetime = Field(default_factory=datetime.now)


class AdSet(BaseModel):
    """An ad set within a campaign."""

    ad_set_id: str | None = None
    campaign_id: str
    name: str
    daily_budget: float = 20.0
    targeting: TargetingSpec = Field(default_factory=lambda: TargetingSpec())
    status: CampaignStatus = CampaignStatus.PAUSED
    optimization_goal: str = "OFFSITE_CONVERSIONS"
    billing_event: str = "IMPRESSIONS"


class TargetingSpec(BaseModel):
    """Targeting specification for an ad set."""

    age_min: int = 25
    age_max: int = 55
    genders: list[int] = Field(default_factory=lambda: [1, 2])  # 1=male, 2=female
    geo_locations: dict = Field(
        default_factory=lambda: {"countries": ["US"]}
    )
    interests: list[dict] = Field(default_factory=list)
    custom_audiences: list[dict] = Field(default_factory=list)
    publisher_platforms: list[str] = Field(
        default_factory=lambda: ["facebook", "instagram"]
    )


class Ad(BaseModel):
    """A single ad within an ad set."""

    ad_id: str | None = None
    ad_set_id: str
    name: str
    creative_id: str  # references GeneratedCreative.creative_id
    meta_creative_id: str | None = None  # Meta's creative object ID
    status: CampaignStatus = CampaignStatus.PAUSED
    created_at: datetime = Field(default_factory=datetime.now)


# Fix forward reference
AdSet.model_rebuild()
