"""Generate new iterations of winning ads."""

from __future__ import annotations

import logging

from generator.copy_generator import CopyGenerator
from meta_ads.campaign_manager import CampaignManager
from meta_ads.uploader import CreativeUploader
from models.ad_creative import GeneratedCreative
from models.campaign import Ad, AdSet, CampaignStatus
from models.performance import OptimizationDecision

logger = logging.getLogger(__name__)


class IterationGenerator:
    """Creates new ad iterations based on winning performers."""

    def __init__(
        self,
        copy_generator: CopyGenerator,
        uploader: CreativeUploader,
        campaign_manager: CampaignManager,
    ) -> None:
        self.copy_generator = copy_generator
        self.uploader = uploader
        self.campaign_manager = campaign_manager

    def iterate_winners(
        self,
        winners: list[OptimizationDecision],
        creative_map: dict[str, GeneratedCreative],
        ad_set_id: str,
        variations_per_winner: int = 5,
        dry_run: bool = False,
    ) -> list[GeneratedCreative]:
        """Generate and upload iterations of winning ads.

        Args:
            winners: Optimization decisions for winning ads
            creative_map: Mapping of creative_id -> GeneratedCreative
            ad_set_id: Ad set to place new iterations in
            variations_per_winner: How many variations to create per winner
            dry_run: If True, generate but don't upload
        """
        all_iterations: list[GeneratedCreative] = []

        for decision in winners:
            creative = creative_map.get(decision.creative_id)
            if not creative:
                logger.warning(
                    f"No creative found for {decision.creative_id}, skipping"
                )
                continue

            # Build performance context for the prompt
            perf = decision.performance
            performance_context = (
                f"This ad achieved: "
                f"CTR={perf.ctr:.2%}, "
                f"CPA=${perf.cpa:.2f}, "
                f"ROAS={perf.roas:.2f}x, "
                f"Impressions={perf.impressions:,}, "
                f"Clicks={perf.clicks:,}. "
                f"Optimization decision: {decision.reason}"
            )

            # Generate iterations
            logger.info(
                f"Generating {variations_per_winner} iterations of "
                f"winning ad {creative.creative_id}"
            )
            iterations = self.copy_generator.generate_iterations(
                creative=creative,
                performance_context=performance_context,
                count=variations_per_winner,
            )
            all_iterations.extend(iterations)

        logger.info(f"Generated {len(all_iterations)} total iterations")

        if dry_run or not all_iterations:
            return all_iterations

        # Upload iterations
        meta_ids = self.uploader.upload_batch(all_iterations)

        # Create ads for uploaded iterations
        for creative in all_iterations:
            meta_creative_id = meta_ids.get(creative.creative_id)
            if not meta_creative_id:
                continue

            ad = Ad(
                ad_set_id=ad_set_id,
                name=f"Iteration: {creative.headline[:40]}",
                creative_id=creative.creative_id,
                status=CampaignStatus.ACTIVE,
            )
            try:
                self.campaign_manager.create_ad(ad, meta_creative_id)
            except Exception as e:
                logger.error(f"Failed to create ad for iteration: {e}")

        return all_iterations
