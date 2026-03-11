"""Meta Marketing API authentication."""

from __future__ import annotations

import logging

from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount

from config.settings import MetaAdsConfig

logger = logging.getLogger(__name__)


class MetaAuth:
    """Handles Meta Marketing API authentication and session setup."""

    def __init__(self, config: MetaAdsConfig) -> None:
        self.config = config
        self._api: FacebookAdsApi | None = None
        self._ad_account: AdAccount | None = None

    def initialize(self) -> None:
        """Initialize the Meta Ads API session."""
        if not self.config.access_token:
            raise ValueError(
                "META_ACCESS_TOKEN environment variable is required. "
                "Generate a token at https://developers.facebook.com/tools/explorer/"
            )

        self._api = FacebookAdsApi.init(
            app_id=self.config.app_id,
            app_secret=self.config.app_secret,
            access_token=self.config.access_token,
            api_version=self.config.api_version,
        )

        account_id = self.config.ad_account_id
        if not account_id.startswith("act_"):
            account_id = f"act_{account_id}"

        self._ad_account = AdAccount(account_id)
        logger.info(f"Meta Ads API initialized for account {account_id}")

    @property
    def api(self) -> FacebookAdsApi:
        if self._api is None:
            self.initialize()
        return self._api

    @property
    def ad_account(self) -> AdAccount:
        if self._ad_account is None:
            self.initialize()
        return self._ad_account

    def validate_connection(self) -> bool:
        """Test the API connection."""
        try:
            account = self.ad_account
            account.api_get(fields=["name", "account_status"])
            name = account.get("name", "Unknown")
            logger.info(f"Connected to ad account: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Meta Ads API: {e}")
            return False
