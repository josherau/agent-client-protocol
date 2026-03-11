"""Meta Ad Library API client for competitor ad research."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta

import httpx

from config.settings import MetaAdsConfig
from models.ad_creative import AdFormat, CompetitorAd

logger = logging.getLogger(__name__)

AD_LIBRARY_BASE_URL = "https://graph.facebook.com/{version}/ads_archive"

# Default fields to request from the Ad Library API
AD_LIBRARY_FIELDS = [
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
    "languages",
    "currency",
]


class AdLibraryScraper:
    """Scrapes competitor ads from the Meta Ad Library API."""

    def __init__(self, config: MetaAdsConfig, max_retries: int = 3) -> None:
        self.config = config
        self.base_url = AD_LIBRARY_BASE_URL.format(version=config.api_version)
        self.client = httpx.Client(timeout=30.0)
        self.max_retries = max_retries

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
        """Search ads for multiple competitors and combine results.

        Accepts numerical page IDs or page slugs. For slugs, attempts
        a Graph API lookup to resolve the numerical ID first.
        """
        all_ads: list[CompetitorAd] = []
        for page_id in competitor_page_ids:
            if not page_id:
                continue
            resolved_id = self._resolve_page_id(page_id)
            logger.info(f"Fetching ads for competitor page: {page_id} (ID: {resolved_id})")
            ads = self.search_by_page(resolved_id, limit=limit_per_competitor)
            all_ads.extend(ads)
            logger.info(f"  Found {len(ads)} ads")
        return all_ads

    def _resolve_page_id(self, page_id_or_slug: str) -> str:
        """Resolve a page slug to its numerical ID via Graph API.

        If already numerical, returns as-is. If lookup fails, returns
        the original value (the Ad Library API may still accept it).
        """
        if page_id_or_slug.isdigit():
            return page_id_or_slug
        try:
            url = f"https://graph.facebook.com/{self.config.api_version}/{page_id_or_slug}"
            response = self.client.get(
                url,
                params={"access_token": self.config.access_token, "fields": "id,name"},
            )
            response.raise_for_status()
            data = response.json()
            resolved = data.get("id", page_id_or_slug)
            logger.info(f"Resolved page slug '{page_id_or_slug}' -> ID {resolved}")
            return resolved
        except httpx.HTTPError as e:
            logger.warning(
                f"Could not resolve page slug '{page_id_or_slug}': {e}. "
                "Using slug directly."
            )
            return page_id_or_slug

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
            "ad_type": "ALL",
            "fields": ",".join(AD_LIBRARY_FIELDS),
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
        """Execute the API request with retry and pagination."""
        ads: list[CompetitorAd] = []
        url = self.base_url

        while url:
            data = self._request_with_retry(url, params)
            if data is None:
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

    def _request_with_retry(self, url: str, params: dict) -> dict | None:
        """Make an API request with exponential backoff on rate limits."""
        for attempt in range(self.max_retries):
            try:
                response = self.client.get(url, params=params)

                if response.status_code == 429:
                    wait = 2 ** (attempt + 1)
                    logger.warning(f"Rate limited, waiting {wait}s (attempt {attempt + 1})")
                    time.sleep(wait)
                    continue

                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as e:
                error_data = {}
                try:
                    error_data = e.response.json()
                except Exception:
                    pass
                error_msg = error_data.get("error", {}).get("message", str(e))
                logger.error(f"Ad Library API error: {error_msg}")
                return None

            except httpx.HTTPError as e:
                if attempt < self.max_retries - 1:
                    wait = 2 ** (attempt + 1)
                    logger.warning(f"Request failed, retrying in {wait}s: {e}")
                    time.sleep(wait)
                else:
                    logger.error(f"Ad Library API request failed after {self.max_retries} attempts: {e}")
                    return None

        return None

    def _parse_ad(self, raw: dict) -> CompetitorAd | None:
        """Parse a raw API response into a CompetitorAd."""
        try:
            bodies = raw.get("ad_creative_bodies", [])
            ad_text = bodies[0] if bodies else ""

            # Skip ads with no text content
            if not ad_text.strip():
                return None

            titles = raw.get("ad_creative_link_titles", [])
            cta_text = titles[0] if titles else ""

            start_time = raw.get("ad_delivery_start_time")
            started = None
            longevity = 0
            if start_time:
                started = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                longevity = max(0, (datetime.now(started.tzinfo) - started).days)

            stop_time = raw.get("ad_delivery_stop_time")
            is_active = stop_time is None

            platforms = raw.get("publisher_platforms", [])

            # Estimate reach from audience size if available
            audience = raw.get("estimated_audience_size", {})
            estimated_reach = ""
            if isinstance(audience, dict) and audience:
                lower = audience.get("lower_bound", "")
                upper = audience.get("upper_bound", "")
                if lower and upper:
                    estimated_reach = f"{lower}-{upper}"

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
                estimated_reach=estimated_reach,
            )
        except Exception as e:
            logger.warning(f"Failed to parse ad {raw.get('id', '?')}: {e}")
            return None

    def close(self) -> None:
        self.client.close()
