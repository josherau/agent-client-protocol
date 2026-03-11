"""Upload creatives to Meta Ads."""

from __future__ import annotations

import logging

from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adcreative import AdCreative as MetaAdCreative
from facebook_business.adobjects.adimage import AdImage

from config.settings import MetaAdsConfig
from meta_ads.auth import MetaAuth
from models.ad_creative import AdFormat, GeneratedCreative

logger = logging.getLogger(__name__)


class CreativeUploader:
    """Uploads generated creatives to Meta Ads as ad creative objects."""

    def __init__(self, auth: MetaAuth, config: MetaAdsConfig) -> None:
        self.auth = auth
        self.config = config

    @property
    def account(self) -> AdAccount:
        return self.auth.ad_account

    def upload_creative(self, creative: GeneratedCreative) -> str:
        """Upload a single creative to Meta and return the creative object ID."""
        if creative.format == AdFormat.CAROUSEL:
            return self._upload_carousel(creative)
        else:
            return self._upload_standard(creative)

    def upload_batch(
        self, creatives: list[GeneratedCreative]
    ) -> dict[str, str]:
        """Upload multiple creatives. Returns mapping of creative_id -> meta_creative_id."""
        results: dict[str, str] = {}
        for creative in creatives:
            try:
                meta_id = self.upload_creative(creative)
                results[creative.creative_id] = meta_id
                logger.info(
                    f"Uploaded {creative.creative_id} -> Meta ID {meta_id}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to upload {creative.creative_id}: {e}"
                )
        logger.info(
            f"Uploaded {len(results)}/{len(creatives)} creatives successfully"
        )
        return results

    def _upload_standard(self, creative: GeneratedCreative) -> str:
        """Upload a standard (single image/video) creative."""
        # Upload image if available
        image_hash = None
        if creative.image_path:
            image_hash = self._upload_image(creative.image_path)

        params = {
            "name": f"Creative: {creative.headline[:50]}",
            "object_story_spec": {
                "page_id": self.config.page_id,
                "link_data": {
                    "message": creative.primary_text,
                    "name": creative.headline,
                    "description": creative.description,
                    "link": "https://victoryperformance.co",
                    "call_to_action": {
                        "type": self._map_cta(creative.cta),
                    },
                },
            },
        }

        if image_hash:
            params["object_story_spec"]["link_data"]["image_hash"] = image_hash

        result = self.account.create_ad_creative(params=params)
        return result["id"]

    def _upload_carousel(self, creative: GeneratedCreative) -> str:
        """Upload a carousel creative."""
        child_attachments = []

        if creative.carousel_cards:
            for card in creative.carousel_cards:
                attachment = {
                    "name": card.headline,
                    "description": card.description,
                    "link": card.link_url or "https://victoryperformance.co",
                    "call_to_action": {
                        "type": self._map_cta(creative.cta),
                    },
                }
                if card.image_path:
                    image_hash = self._upload_image(card.image_path)
                    attachment["image_hash"] = image_hash
                child_attachments.append(attachment)

        params = {
            "name": f"Carousel: {creative.headline[:50]}",
            "object_story_spec": {
                "page_id": self.config.page_id,
                "link_data": {
                    "message": creative.primary_text,
                    "child_attachments": child_attachments,
                    "link": "https://victoryperformance.co",
                },
            },
        }

        result = self.account.create_ad_creative(params=params)
        return result["id"]

    def _upload_image(self, image_path: str) -> str:
        """Upload an image and return its hash."""
        image = AdImage(parent_id=self.account.get_id())
        image[AdImage.Field.filename] = image_path
        image.remote_create()
        return image[AdImage.Field.hash]

    def _map_cta(self, cta_text: str) -> str:
        """Map human-readable CTA to Meta's CTA type enum."""
        mapping = {
            "learn more": "LEARN_MORE",
            "sign up": "SIGN_UP",
            "shop now": "SHOP_NOW",
            "get started": "GET_STARTED",
            "book now": "BOOK_NOW",
            "download": "DOWNLOAD",
            "get offer": "GET_OFFER",
            "try free": "SIGN_UP",
            "see how it works": "LEARN_MORE",
            "start your trial": "SIGN_UP",
            # Victory Performance custom CTAs
            "unlock your mental edge": "LEARN_MORE",
            "start winning now": "SIGN_UP",
            "book your free session": "BOOK_NOW",
            "get your competitive edge": "LEARN_MORE",
            "train your mind to win": "LEARN_MORE",
        }
        return mapping.get(cta_text.lower(), "LEARN_MORE")
