"""Brand kit definition for Victory Performance."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BrandColors:
    """Brand color palette — Victory Performance military/athletic aesthetic."""

    primary: str = "#1B1B1B"       # Deep black — authority, strength
    secondary: str = "#C8A951"     # Gold — victory, excellence, premium
    accent: str = "#8B0000"        # Dark red — intensity, competition, warrior spirit
    background: str = "#FFFFFF"
    text_dark: str = "#1B1B1B"
    text_light: str = "#F5F5F5"


@dataclass
class BrandTypography:
    """Brand typography settings."""

    heading_font: str = "Montserrat"
    body_font: str = "Open Sans"
    heading_weight: str = "bold"
    body_weight: str = "regular"


@dataclass
class BrandVoice:
    """Brand tone of voice — military precision meets coaching empathy."""

    tone: str = (
        "commanding yet empathetic — like a coach who's been in the trenches. "
        "Confident, direct, and battle-tested. Speaks to athletes who are "
        "hungry to win but struggling with the mental side. Uses intensity "
        "and conviction without being aggressive or salesy."
    )
    personality_traits: list[str] = field(
        default_factory=lambda: [
            "battle-tested",
            "empowering",
            "no-nonsense",
            "resilient",
            "authoritative",
            "supportive",
        ]
    )
    avoid_words: list[str] = field(
        default_factory=lambda: [
            "cheap",
            "easy",
            "simple",
            "therapy",
            "mental health",
            "weakness",
            "broken",
            "fix",
            "discount",
        ]
    )
    preferred_ctas: list[str] = field(
        default_factory=lambda: [
            "Unlock Your Mental Edge",
            "Start Winning Now",
            "Book Your Free Session",
            "Get Your Competitive Edge",
            "Train Your Mind to Win",
            "Learn More",
        ]
    )


@dataclass
class BrandKit:
    """Complete brand kit for Victory Performance."""

    company_name: str = "Victory Performance"
    tagline: str = "Train Your Mind. Own Your Game."
    website_url: str = "https://victoryperformance.co"
    logo_path: str = "assets/logo.png"
    colors: BrandColors = field(default_factory=BrandColors)
    typography: BrandTypography = field(default_factory=BrandTypography)
    voice: BrandVoice = field(default_factory=BrandVoice)
    industry: str = "sports mental performance coaching"
    target_audience: str = (
        "elite high school, college, and professional athletes (and their parents) "
        "aged 14-35 who are physically talented but underperforming due to mental "
        "barriers — self-doubt, choking under pressure, fear of failure, perfectionism"
    )
    unique_selling_points: list[str] = field(
        default_factory=lambda: [
            "Founded by a Purple Heart recipient and former military leader — "
            "battlefield-tested resilience strategies applied to sport",
            "Triple board-certified physician on the team — medical precision "
            "meets mental performance coaching",
            "21+ proven Mental Edge Skills that elevate good athletes to great ones",
            "Holistic approach: mindset, sleep, nutrition, injury recovery, "
            "emotional regulation, and spiritual strength",
            "Athletes see measurable improvement within the first week to month",
            "20-30% better focus, decision-making, and emotional control vs peers",
            "Full refund guarantee if no impact after first session",
            "Weekly live sessions + workbook exercises + in-training strategies "
            "that become automatic under stress",
            "Root-cause coaching — addresses perfectionism, fear of failure, "
            "social approval, and rigid expectations, not just symptoms",
        ]
    )
    key_messaging_themes: list[str] = field(
        default_factory=lambda: [
            "Unshakable Confidence — conquer self-doubt and fear",
            "Resilient Mindset — thrive under pressure and adversity",
            "Laser-Focused Performance — sharpen concentration and execution",
            "Bounce Back Stronger — recover from setbacks with strength",
            "Gain Your Competitive Edge — achieve peak performance",
            "The mental game is the difference between good and great",
            "Your talent isn't the problem — your mindset is",
        ]
    )

    def to_prompt_context(self) -> str:
        """Convert brand kit to a prompt-friendly string for Claude."""
        return (
            f"Company: {self.company_name}\n"
            f"Tagline: {self.tagline}\n"
            f"Website: {self.website_url}\n"
            f"Industry: {self.industry}\n"
            f"Target Audience: {self.target_audience}\n"
            f"Tone of Voice: {self.voice.tone}\n"
            f"Personality: {', '.join(self.voice.personality_traits)}\n"
            f"Avoid these words: {', '.join(self.voice.avoid_words)}\n"
            f"Preferred CTAs: {', '.join(self.voice.preferred_ctas)}\n"
            f"\nKey Messaging Themes:\n"
            + "\n".join(f"  - {theme}" for theme in self.key_messaging_themes)
            + f"\n\nUnique Selling Points:\n"
            + "\n".join(f"  - {usp}" for usp in self.unique_selling_points)
            + f"\n\nFounder Credibility: Purple Heart military veteran + "
            f"triple board-certified physician. They understand performing "
            f"under extreme pressure firsthand."
        )


def load_brand_kit() -> BrandKit:
    """Load brand kit. Customize this function to load from file/env."""
    return BrandKit()
