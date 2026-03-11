"""Build prompts for Claude API to generate ad copy variations."""

from __future__ import annotations

from config.brand_kit import BrandKit
from models.ad_creative import AdFormat, CompetitorAd
from research.competitor_analyzer import AdPattern, CompetitorInsights


class PromptBuilder:
    """Constructs prompts for ad copy generation using competitor insights."""

    def __init__(self, brand_kit: BrandKit) -> None:
        self.brand_kit = brand_kit

    def build_single_image_prompt(
        self,
        seed_ads: list[CompetitorAd],
        patterns: list[AdPattern],
        count: int = 10,
    ) -> str:
        """Build a prompt to generate single image ad copy variations."""
        seed_examples = self._format_seed_ads(seed_ads)
        pattern_desc = self._format_patterns(patterns)
        brand_context = self.brand_kit.to_prompt_context()

        return f"""You are an expert direct-response copywriter specializing in Meta (Facebook/Instagram) ads.

## Your Task
Generate {count} unique single-image ad creatives for the following brand. Each ad should have a different hook and angle but maintain brand consistency.

## Brand Information
{brand_context}

## Competitor Ad Patterns That Are Working
{pattern_desc}

## Seed Ads (Top Performers from Competitors)
{seed_examples}

## Requirements for Each Ad
- **Headline**: 5-10 words, attention-grabbing, benefit-focused
- **Primary Text**: 50-150 words, includes a hook, value proposition, and CTA
- **Description**: 1-2 sentences for the link description
- **CTA Button**: Choose from: Learn More, Sign Up, Shop Now, Get Started, Book Now, Download, Get Offer

## Output Format
Return exactly {count} ads as a JSON array. Each element should have:
- "headline": string
- "primary_text": string
- "description": string
- "cta": string
- "hook_style": string (question/statistic/benefit/urgency/story/social_proof)

## Guidelines
- Vary the hook styles across the {count} ads
- Never copy competitor text directly — use their patterns as inspiration
- Include specific numbers/stats where possible (can be approximate)
- Write for a {self.brand_kit.voice.tone} tone
- Avoid: {', '.join(self.brand_kit.voice.avoid_words)}
- Target audience: {self.brand_kit.target_audience}

Return ONLY the JSON array, no other text."""

    def build_carousel_prompt(
        self,
        seed_ads: list[CompetitorAd],
        patterns: list[AdPattern],
        count: int = 10,
    ) -> str:
        """Build a prompt to generate carousel ad copy."""
        seed_examples = self._format_seed_ads(seed_ads)
        brand_context = self.brand_kit.to_prompt_context()

        return f"""You are an expert direct-response copywriter specializing in carousel ads for Meta platforms.

## Your Task
Generate {count} unique carousel ad concepts. Each carousel should have 3-5 cards that tell a cohesive story or walk through key benefits.

## Brand Information
{brand_context}

## Seed Ads for Inspiration
{seed_examples}

## Requirements
For each carousel ad, provide:
- **Primary Text**: The main post text (50-150 words)
- **Cards**: 3-5 cards, each with:
  - headline (5-8 words)
  - description (1-2 sentences)
  - image_description (brief description of what the card image should show)
- **CTA**: The button CTA for the final card

## Output Format
Return exactly {count} carousel ads as a JSON array. Each element:
- "primary_text": string
- "cta": string
- "cards": [{{"headline": str, "description": str, "image_description": str}}, ...]

Return ONLY the JSON array, no other text."""

    def build_video_script_prompt(
        self,
        seed_ads: list[CompetitorAd],
        patterns: list[AdPattern],
        count: int = 10,
    ) -> str:
        """Build a prompt to generate video ad scripts."""
        seed_examples = self._format_seed_ads(seed_ads)
        brand_context = self.brand_kit.to_prompt_context()

        return f"""You are an expert video ad scriptwriter for social media platforms.

## Your Task
Write {count} unique 15-30 second video ad scripts for Meta platforms (Facebook/Instagram Reels/Stories).

## Brand Information
{brand_context}

## Seed Ads for Inspiration
{seed_examples}

## Requirements
Each script should include:
- **Hook** (first 3 seconds): Must stop the scroll
- **Problem/Agitation** (seconds 3-10): Identify the pain point
- **Solution** (seconds 10-20): Present the product/service
- **CTA** (final 5 seconds): Clear next step
- **On-screen text**: Key text overlays for each section
- **Visual direction**: Brief description of what should be shown

## Output Format
Return exactly {count} scripts as a JSON array. Each element:
- "headline": string (for the ad listing)
- "primary_text": string (post caption)
- "script": string (the full script with timing notes)
- "on_screen_text": [string, ...]
- "cta": string

Return ONLY the JSON array, no other text."""

    def build_story_reel_prompt(
        self,
        seed_ads: list[CompetitorAd],
        patterns: list[AdPattern],
        count: int = 10,
    ) -> str:
        """Build a prompt for story/reel format ads."""
        seed_examples = self._format_seed_ads(seed_ads)
        brand_context = self.brand_kit.to_prompt_context()

        return f"""You are an expert at creating viral-style story and reel ad content for Instagram and Facebook.

## Your Task
Create {count} unique story/reel ad concepts optimized for vertical full-screen format.

## Brand Information
{brand_context}

## Seed Ads for Inspiration
{seed_examples}

## Requirements
Each ad should be designed for 9:16 vertical format and include:
- **Hook Text**: Large bold text overlay for the first frame (max 8 words)
- **Primary Text**: Caption text
- **Sequence**: 3-5 frame descriptions with text overlays
- **CTA**: Swipe-up or button CTA

## Output Format
Return exactly {count} ads as a JSON array. Each element:
- "headline": string (hook text for first frame)
- "primary_text": string (caption)
- "frames": [{{"text_overlay": str, "visual_description": str}}, ...]
- "cta": string

Return ONLY the JSON array, no other text."""

    def build_iteration_prompt(
        self,
        original_headline: str,
        original_text: str,
        original_cta: str,
        performance_context: str,
        variation_count: int = 5,
    ) -> str:
        """Build a prompt to iterate on a winning ad."""
        brand_context = self.brand_kit.to_prompt_context()

        return f"""You are an expert at iterating on winning ad creatives to find even better variations.

## Brand Information
{brand_context}

## Original Winning Ad
Headline: {original_headline}
Primary Text: {original_text}
CTA: {original_cta}

## Performance Context
{performance_context}

## Your Task
Create {variation_count} variations of this winning ad. For each variation, change ONE key element:
1. Different hook angle (keep the same core message)
2. Different emotional trigger
3. Different CTA approach
4. Shorter/punchier version
5. Longer, more detailed version

## Output Format
Return exactly {variation_count} variations as a JSON array. Each element:
- "headline": string
- "primary_text": string
- "description": string
- "cta": string
- "variation_type": string (what was changed)

Return ONLY the JSON array, no other text."""

    def _format_seed_ads(self, ads: list[CompetitorAd]) -> str:
        lines = []
        for i, ad in enumerate(ads[:10], 1):
            lines.append(f"### Ad {i} (from {ad.page_name})")
            lines.append(f"Text: {ad.ad_text[:300]}")
            lines.append(f"CTA: {ad.cta_text}")
            lines.append(f"Running for: {ad.longevity_days} days")
            lines.append("")
        return "\n".join(lines)

    def _format_patterns(self, patterns: list[AdPattern]) -> str:
        lines = []
        for p in patterns:
            lines.append(
                f"- **{p.hook_style.title()}** hooks with {p.tone} tone "
                f"(avg {p.avg_text_length} chars)"
            )
        return "\n".join(lines) if lines else "No clear patterns detected."
