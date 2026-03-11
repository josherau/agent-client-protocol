"""Generate ad copy using Claude API."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime

import anthropic

from config.brand_kit import BrandKit
from config.settings import ClaudeConfig, GenerationConfig
from generator.prompt_builder import PromptBuilder
from models.ad_creative import AdFormat, CarouselCard, CompetitorAd, GeneratedCreative
from research.competitor_analyzer import AdPattern, CompetitorInsights

logger = logging.getLogger(__name__)


class CopyGenerator:
    """Generates ad copy variations using Claude API."""

    def __init__(
        self,
        claude_config: ClaudeConfig,
        brand_kit: BrandKit,
        generation_config: GenerationConfig,
    ) -> None:
        self.client = anthropic.Anthropic(api_key=claude_config.api_key)
        self.model = claude_config.model
        self.max_tokens = claude_config.max_tokens
        self.brand_kit = brand_kit
        self.gen_config = generation_config
        self.prompt_builder = PromptBuilder(brand_kit)

    def generate_all(
        self,
        seed_ads: list[CompetitorAd],
        patterns: list[AdPattern],
    ) -> list[GeneratedCreative]:
        """Generate all creative variations across formats."""
        all_creatives: list[GeneratedCreative] = []

        logger.info(
            f"Generating {self.gen_config.total_creatives} creatives across 4 formats"
        )

        # Single image ads
        single_image = self._generate_format(
            AdFormat.SINGLE_IMAGE,
            seed_ads,
            patterns,
            self.gen_config.single_image_count,
        )
        all_creatives.extend(single_image)
        logger.info(f"Generated {len(single_image)} single image ads")

        # Carousel ads
        carousels = self._generate_format(
            AdFormat.CAROUSEL,
            seed_ads,
            patterns,
            self.gen_config.carousel_count,
        )
        all_creatives.extend(carousels)
        logger.info(f"Generated {len(carousels)} carousel ads")

        # Video scripts
        videos = self._generate_format(
            AdFormat.VIDEO_SCRIPT,
            seed_ads,
            patterns,
            self.gen_config.video_script_count,
        )
        all_creatives.extend(videos)
        logger.info(f"Generated {len(videos)} video script ads")

        # Story/reel ads
        stories = self._generate_format(
            AdFormat.STORY_REEL,
            seed_ads,
            patterns,
            self.gen_config.story_reel_count,
        )
        all_creatives.extend(stories)
        logger.info(f"Generated {len(stories)} story/reel ads")

        logger.info(f"Total creatives generated: {len(all_creatives)}")
        return all_creatives

    def generate_iterations(
        self,
        creative: GeneratedCreative,
        performance_context: str,
        count: int = 5,
    ) -> list[GeneratedCreative]:
        """Generate new iterations of a winning ad."""
        prompt = self.prompt_builder.build_iteration_prompt(
            original_headline=creative.headline,
            original_text=creative.primary_text,
            original_cta=creative.cta,
            performance_context=performance_context,
            variation_count=count,
        )

        raw_ads = self._call_claude(prompt)
        creatives = []
        for raw in raw_ads:
            creatives.append(
                GeneratedCreative(
                    creative_id=f"iter-{uuid.uuid4().hex[:12]}",
                    seed_ad_id=creative.seed_ad_id,
                    format=creative.format,
                    headline=raw.get("headline", ""),
                    primary_text=raw.get("primary_text", ""),
                    description=raw.get("description", ""),
                    cta=raw.get("cta", "Learn More"),
                    brand_applied=True,
                )
            )
        return creatives

    def _generate_format(
        self,
        format: AdFormat,
        seed_ads: list[CompetitorAd],
        patterns: list[AdPattern],
        count: int,
    ) -> list[GeneratedCreative]:
        """Generate creatives for a specific ad format."""
        # Generate in batches to stay within token limits
        batch_size = 10
        all_creatives: list[GeneratedCreative] = []

        for batch_start in range(0, count, batch_size):
            batch_count = min(batch_size, count - batch_start)

            prompt = self._get_prompt_for_format(
                format, seed_ads, patterns, batch_count
            )
            raw_ads = self._call_claude(prompt)

            for raw in raw_ads:
                creative = self._parse_raw_creative(raw, format, seed_ads)
                if creative:
                    all_creatives.append(creative)

        return all_creatives

    def _get_prompt_for_format(
        self,
        format: AdFormat,
        seed_ads: list[CompetitorAd],
        patterns: list[AdPattern],
        count: int,
    ) -> str:
        if format == AdFormat.SINGLE_IMAGE:
            return self.prompt_builder.build_single_image_prompt(
                seed_ads, patterns, count
            )
        elif format == AdFormat.CAROUSEL:
            return self.prompt_builder.build_carousel_prompt(
                seed_ads, patterns, count
            )
        elif format == AdFormat.VIDEO_SCRIPT:
            return self.prompt_builder.build_video_script_prompt(
                seed_ads, patterns, count
            )
        elif format == AdFormat.STORY_REEL:
            return self.prompt_builder.build_story_reel_prompt(
                seed_ads, patterns, count
            )
        else:
            raise ValueError(f"Unknown format: {format}")

    def _call_claude(self, prompt: str) -> list[dict]:
        """Call Claude API and parse the JSON response."""
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = message.content[0].text

            # Extract JSON from response
            # Handle cases where Claude wraps in markdown code blocks
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]

            result = json.loads(response_text.strip())
            if isinstance(result, list):
                return result
            return [result]

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response as JSON: {e}")
            return []
        except anthropic.APIError as e:
            logger.error(f"Claude API error: {e}")
            return []

    def _parse_raw_creative(
        self,
        raw: dict,
        format: AdFormat,
        seed_ads: list[CompetitorAd],
    ) -> GeneratedCreative | None:
        """Parse a raw JSON dict into a GeneratedCreative."""
        try:
            seed_id = seed_ads[0].ad_id if seed_ads else "unknown"

            creative = GeneratedCreative(
                creative_id=f"gen-{uuid.uuid4().hex[:12]}",
                seed_ad_id=seed_id,
                format=format,
                headline=raw.get("headline", ""),
                primary_text=raw.get("primary_text", ""),
                description=raw.get("description", ""),
                cta=raw.get("cta", "Learn More"),
                brand_applied=True,
            )

            # Handle carousel-specific fields
            if format == AdFormat.CAROUSEL and "cards" in raw:
                creative.carousel_cards = [
                    CarouselCard(
                        headline=card.get("headline", ""),
                        description=card.get("description", ""),
                    )
                    for card in raw["cards"]
                ]

            # Handle video script
            if format == AdFormat.VIDEO_SCRIPT and "script" in raw:
                creative.video_script = raw["script"]

            return creative
        except Exception as e:
            logger.warning(f"Failed to parse creative: {e}")
            return None
