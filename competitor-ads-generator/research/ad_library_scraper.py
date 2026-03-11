"""Meta Ad Library API client for competitor ad research."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

import httpx

from config.settings import MetaAdsConfig
from models.ad_creative import AdFormat, CompetitorAd

logger = logging.getLogger(__name__)

AD_LIBRARY_BASE_URL = "https://graph.facebook.com/{version}/ads_archive"


class AdLibraryScraper:
    """Scrapes competitor ads from the Meta Ad Library API."""

    def __init__(self, config: MetaAdsConfig) -> None:
        self.config = config
        self.base_url = AD_LIBRARY_BASE_URL.format(version=config.api_version)
        self.client = httpx.Client(timeout=30.0)

    def search_by_page(
        self,
        page_id: str,
        limit: int = 100,
        active_only: bool = True,
    ) -> list[CompetitorAd]:
        """Search ads by a specific Facebook page ID."""
        params = self._build_params(
            search_page_ids=page_id,
            limit=limit,
            active_only=active_only,
        )
        return self._fetch_ads(params)

    def search_by_keyword(
        self,
        keyword: str,
        country: str = "US",
        limit: int = 100,
        active_only: bool = True,
    ) -> list[CompetitorAd]:
        """Search ads by keyword across the Ad Library."""
        params = self._build_params(
            search_terms=keyword,
            country=country,
            limit=limit,
            active_only=active_only,
        )
        return self._fetch_ads(params)

    def search_competitors(
        self,
        competitor_page_ids: list[str],
        limit_per_competitor: int = 50,
    ) -> list[CompetitorAd]:
        """Search ads for multiple competitors and combine results."""
        all_ads: list[CompetitorAd] = []
        for page_id in competitor_page_ids:
            logger.info(f"Fetching ads for competitor page: {page_id}")
            ads = self.search_by_page(page_id, limit=limit_per_competitor)
            all_ads.extend(ads)
            logger.info(f"  Found {len(ads)} ads")
        return all_ads

    def _build_params(
        self,
        search_terms: str | None = None,
        search_page_ids: str | None = None,
        country: str = "US",
        limit: int = 100,
        active_only: bool = True,
    ) -> dict:
        params = {
            "access_token": self.config.access_token,
            "ad_reached_countries": f'["{country}"]',
            "ad_type": "POLITICAL_AND_ISSUE_ADS",  # or ALL for business ads
            "fields": ",".join([
                "id",
                "ad_creative_bodies",
                "ad_creative_link_captions",
                "ad_creative_link_titles",
                "ad_delivery_start_time",
                "ad_delivery_stop_time",
                "page_id",
                "page_name",
                "publisher_platforms",
                "estimated_audience_size",
                "impressions",
                "spend",
            ]),
            "limit": str(min(limit, 100)),
        }
        if search_terms:
            params["search_terms"] = search_terms
        if search_page_ids:
            params["search_page_ids"] = f'["{search_page_ids}"]'
        if active_only:
            params["ad_active_status"] = "ACTIVE"
        return params

    def _fetch_ads(self, params: dict) -> list[CompetitorAd]:
        """Execute the API request and parse results."""
        ads: list[CompetitorAd] = []
        url = self.base_url

        while url:
            try:
                response = self.client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
            except httpx.HTTPError as e:
                logger.error(f"Ad Library API request failed: {e}")
                break

            for raw_ad in data.get("data", []):
                ad = self._parse_ad(raw_ad)
                if ad:
                    ads.append(ad)

            # Handle pagination
            paging = data.get("paging", {})
            url = paging.get("next")
            params = {}  # next URL includes params

        return ads

    def _parse_ad(self, raw: dict) -> CompetitorAd | None:
        """Parse a raw API response into a CompetitorAd."""
        try:
            bodies = raw.get("ad_creative_bodies", [])
            ad_text = bodies[0] if bodies else ""

            titles = raw.get("ad_creative_link_titles", [])
            cta_text = titles[0] if titles else ""

            start_time = raw.get("ad_delivery_start_time")
            started = None
            longevity = 0
            if start_time:
                started = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                longevity = (datetime.now(started.tzinfo) - started).days

            stop_time = raw.get("ad_delivery_stop_time")
            is_active = stop_time is None

            platforms = raw.get("publisher_platforms", [])

            return CompetitorAd(
                ad_id=raw.get("id", ""),
                page_name=raw.get("page_name", ""),
                page_id=raw.get("page_id", ""),
                ad_text=ad_text,
                cta_text=cta_text,
                format=AdFormat.SINGLE_IMAGE,  # API doesn't directly expose format
                started_running=started,
                is_active=is_active,
                platforms=platforms,
                longevity_days=longevity,
            )
        except Exception as e:
            logger.warning(f"Failed to parse ad: {e}")
            return None

    def close(self) -> None:
        self.client.close()
