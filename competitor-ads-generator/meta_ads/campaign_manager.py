"""Create and manage Meta Ads campaigns, ad sets, and ads."""

from __future__ import annotations

import logging

from facebook_business.adobjects.ad import Ad as MetaAd
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adcreative import AdCreative as MetaAdCreative
from facebook_business.adobjects.adset import AdSet as MetaAdSet
from facebook_business.adobjects.campaign import Campaign as MetaCampaign

from meta_ads.auth import MetaAuth
from models.campaign import Ad, AdSet, Campaign, CampaignStatus, TargetingSpec

logger = logging.getLogger(__name__)


class CampaignManager:
    """Manages Meta Ads campaign structure creation."""

    def __init__(self, auth: MetaAuth) -> None:
        self.auth = auth

    @property
    def account(self) -> AdAccount:
        return self.auth.ad_account

    def create_campaign(self, campaign: Campaign) -> Campaign:
        """Create a campaign in Meta Ads."""
        params = {
            "name": campaign.name,
            "objective": campaign.objective.value,
            "status": campaign.status.value,
            "special_ad_categories": [],
        }

        result = self.account.create_campaign(params=params)
        campaign.campaign_id = result["id"]
        logger.info(f"Created campaign: {campaign.name} (ID: {campaign.campaign_id})")
        return campaign

    def create_ad_set(self, ad_set: AdSet) -> AdSet:
        """Create an ad set within a campaign."""
        targeting = self._build_targeting(ad_set.targeting)

        params = {
            "name": ad_set.name,
            "campaign_id": ad_set.campaign_id,
            "daily_budget": int(ad_set.daily_budget * 100),  # cents
            "billing_event": ad_set.billing_event,
            "optimization_goal": ad_set.optimization_goal,
            "targeting": targeting,
            "status": ad_set.status.value,
        }

        result = self.account.create_ad_set(params=params)
        ad_set.ad_set_id = result["id"]
        logger.info(f"Created ad set: {ad_set.name} (ID: {ad_set.ad_set_id})")
        return ad_set

    def create_ad(
        self,
        ad: Ad,
        meta_creative_id: str,
    ) -> Ad:
        """Create an ad within an ad set."""
        params = {
            "name": ad.name,
            "adset_id": ad.ad_set_id,
            "creative": {"creative_id": meta_creative_id},
            "status": ad.status.value,
        }

        result = self.account.create_ad(params=params)
        ad.ad_id = result["id"]
        ad.meta_creative_id = meta_creative_id
        logger.info(f"Created ad: {ad.name} (ID: {ad.ad_id})")
        return ad

    def pause_ad(self, ad_id: str) -> None:
        """Pause a specific ad."""
        ad = MetaAd(ad_id)
        ad.api_update(params={"status": CampaignStatus.PAUSED.value})
        logger.info(f"Paused ad: {ad_id}")

    def activate_ad(self, ad_id: str) -> None:
        """Activate a paused ad."""
        ad = MetaAd(ad_id)
        ad.api_update(params={"status": CampaignStatus.ACTIVE.value})
        logger.info(f"Activated ad: {ad_id}")

    def update_ad_set_budget(self, ad_set_id: str, daily_budget: float) -> None:
        """Update the daily budget for an ad set."""
        ad_set = MetaAdSet(ad_set_id)
        ad_set.api_update(params={"daily_budget": int(daily_budget * 100)})
        logger.info(f"Updated ad set {ad_set_id} budget to ${daily_budget:.2f}/day")

    def get_campaign_ads(self, campaign_id: str) -> list[dict]:
        """Get all ads in a campaign."""
        campaign = MetaCampaign(campaign_id)
        ads = campaign.get_ads(fields=["id", "name", "status", "creative"])
        return [dict(ad) for ad in ads]

    def _build_targeting(self, spec: TargetingSpec) -> dict:
        """Convert our targeting spec to Meta's format."""
        targeting = {
            "age_min": spec.age_min,
            "age_max": spec.age_max,
            "genders": spec.genders,
            "geo_locations": spec.geo_locations,
            "publisher_platforms": spec.publisher_platforms,
        }
        if spec.interests:
            targeting["flexible_spec"] = [{"interests": spec.interests}]
        if spec.custom_audiences:
            targeting["custom_audiences"] = spec.custom_audiences
        return targeting
