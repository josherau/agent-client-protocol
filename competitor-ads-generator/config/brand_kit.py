"""Brand kit definition — customize with your company's branding."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BrandColors:
    """Brand color palette."""

    primary: str = "#2563EB"
    secondary: str = "#7C3AED"
    accent: str = "#F59E0B"
    background: str = "#FFFFFF"
    text_dark: str = "#1F2937"
    text_light: str = "#F9FAFB"


@dataclass
class BrandTypography:
    """Brand typography settings."""

    heading_font: str = "Inter"
    body_font: str = "Inter"
    heading_weight: str = "bold"
    body_weight: str = "regular"


@dataclass
class BrandVoice:
    """Brand tone of voice for copy generation."""

    tone: str = "professional yet approachable"
    personality_traits: list[str] = field(
        default_factory=lambda: [
            "confident",
            "helpful",
            "innovative",
            "trustworthy",
        ]
    )
    avoid_words: list[str] = field(
        default_factory=lambda: [
            "cheap",
            "basic",
            "simple",
        ]
    )
    preferred_ctas: list[str] = field(
        default_factory=lambda: [
            "Get Started",
            "Learn More",
            "Try Free",
            "See How It Works",
            "Start Your Trial",
        ]
    )


@dataclass
class BrandKit:
    """Complete brand kit for creative generation."""

    company_name: str = "Your Company"
    tagline: str = "Your tagline here"
    website_url: str = "https://yourcompany.com"
    logo_path: str = "assets/logo.png"
    colors: BrandColors = field(default_factory=BrandColors)
    typography: BrandTypography = field(default_factory=BrandTypography)
    voice: BrandVoice = field(default_factory=BrandVoice)
    industry: str = "technology"
    target_audience: str = "business professionals aged 25-55"
    unique_selling_points: list[str] = field(
        default_factory=lambda: [
            "Feature 1",
            "Feature 2",
            "Feature 3",
        ]
    )

    def to_prompt_context(self) -> str:
        """Convert brand kit to a prompt-friendly string for Claude."""
        return (
            f"Company: {self.company_name}\n"
            f"Tagline: {self.tagline}\n"
            f"Industry: {self.industry}\n"
            f"Target Audience: {self.target_audience}\n"
            f"Tone of Voice: {self.voice.tone}\n"
            f"Personality: {', '.join(self.voice.personality_traits)}\n"
            f"Avoid these words: {', '.join(self.voice.avoid_words)}\n"
            f"Preferred CTAs: {', '.join(self.voice.preferred_ctas)}\n"
            f"Unique Selling Points:\n"
            + "\n".join(f"  - {usp}" for usp in self.unique_selling_points)
        )


def load_brand_kit() -> BrandKit:
    """Load brand kit. Customize this function to load from file/env."""
    return BrandKit()
