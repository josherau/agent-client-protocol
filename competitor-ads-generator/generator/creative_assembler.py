"""Assemble final ad creatives with brand kit applied."""

from __future__ import annotations

import logging
from pathlib import Path

from config.brand_kit import BrandKit
from models.ad_creative import AdFormat, GeneratedCreative

logger = logging.getLogger(__name__)


class CreativeAssembler:
    """Applies brand kit to generated creatives and prepares for upload."""

    def __init__(self, brand_kit: BrandKit, output_dir: str = "output") -> None:
        self.brand_kit = brand_kit
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def assemble_all(
        self, creatives: list[GeneratedCreative]
    ) -> list[GeneratedCreative]:
        """Apply brand kit to all creatives and prepare assets."""
        assembled = []
        for creative in creatives:
            result = self.assemble(creative)
            if result:
                assembled.append(result)
        logger.info(f"Assembled {len(assembled)}/{len(creatives)} creatives")
        return assembled

    def assemble(self, creative: GeneratedCreative) -> GeneratedCreative:
        """Apply brand kit to a single creative."""
        # Inject brand name where appropriate
        creative.primary_text = self._inject_brand_references(creative.primary_text)

        # Set link URLs for carousel cards
        if creative.carousel_cards:
            for card in creative.carousel_cards:
                if not card.link_url:
                    card.link_url = self.brand_kit.website_url

        creative.brand_applied = True
        return creative

    def _inject_brand_references(self, text: str) -> str:
        """Ensure brand name appears naturally in the copy."""
        if self.brand_kit.company_name.lower() not in text.lower():
            # Append a subtle brand mention if not present
            text = text.rstrip()
            if not text.endswith("."):
                text += "."
            text += f"\n\n{self.brand_kit.company_name} — {self.brand_kit.tagline}"
        return text

    def generate_image_specs(self, creative: GeneratedCreative) -> dict:
        """Generate image specifications for an image generation API.

        Returns a spec dict that can be passed to any image generation service.
        """
        specs = {
            "brand_colors": {
                "primary": self.brand_kit.colors.primary,
                "secondary": self.brand_kit.colors.secondary,
                "accent": self.brand_kit.colors.accent,
                "background": self.brand_kit.colors.background,
            },
            "logo_path": self.brand_kit.logo_path,
            "font": self.brand_kit.typography.heading_font,
            "headline_text": creative.headline,
        }

        if creative.format == AdFormat.SINGLE_IMAGE:
            specs["dimensions"] = {"width": 1080, "height": 1080}
            specs["format"] = "square"
        elif creative.format == AdFormat.CAROUSEL:
            specs["dimensions"] = {"width": 1080, "height": 1080}
            specs["format"] = "square"
            specs["card_count"] = (
                len(creative.carousel_cards) if creative.carousel_cards else 3
            )
        elif creative.format == AdFormat.STORY_REEL:
            specs["dimensions"] = {"width": 1080, "height": 1920}
            specs["format"] = "vertical"
        elif creative.format == AdFormat.VIDEO_SCRIPT:
            specs["dimensions"] = {"width": 1080, "height": 1920}
            specs["format"] = "vertical"

        return specs

    def export_brief(self, creatives: list[GeneratedCreative]) -> str:
        """Export all creatives as a human-readable brief."""
        lines = [
            f"# Creative Brief — {self.brand_kit.company_name}",
            f"Total Creatives: {len(creatives)}",
            "",
        ]

        for i, c in enumerate(creatives, 1):
            lines.append(f"## Creative {i} [{c.format.value}]")
            lines.append(f"**ID:** {c.creative_id}")
            lines.append(f"**Headline:** {c.headline}")
            lines.append(f"**Primary Text:** {c.primary_text}")
            if c.description:
                lines.append(f"**Description:** {c.description}")
            lines.append(f"**CTA:** {c.cta}")
            if c.carousel_cards:
                lines.append("**Carousel Cards:**")
                for j, card in enumerate(c.carousel_cards, 1):
                    lines.append(f"  Card {j}: {card.headline} — {card.description}")
            if c.video_script:
                lines.append(f"**Video Script:** {c.video_script[:200]}...")
            lines.append("")

        brief = "\n".join(lines)

        # Save to file
        brief_path = self.output_dir / "creative_brief.md"
        brief_path.write_text(brief)
        logger.info(f"Brief exported to {brief_path}")

        return brief
