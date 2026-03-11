#!/usr/bin/env python3
"""Competitor Ads Generator - Research competitors and generate ad copy."""

import json
import os
import sys

import anthropic
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

RESEARCH_PROMPT = """\
You are a competitive intelligence analyst. Given a product or company name, \
research and provide a structured analysis of the competitive landscape.

Provide the following for each competitor:
1. Company/Product name
2. Key value propositions
3. Target audience
4. Pricing model (if known)
5. Strengths and weaknesses
6. Common ad messaging themes

Format your response as JSON with the following structure:
{
  "competitors": [
    {
      "name": "Competitor Name",
      "value_propositions": ["prop1", "prop2"],
      "target_audience": "description",
      "pricing_model": "description",
      "strengths": ["s1", "s2"],
      "weaknesses": ["w1", "w2"],
      "ad_themes": ["theme1", "theme2"]
    }
  ],
  "market_summary": "Brief overview of the competitive landscape"
}
"""

AD_GENERATION_PROMPT = """\
You are an expert advertising copywriter. Based on the competitive research \
provided, generate compelling ad copy that differentiates our product from \
competitors.

For each ad, provide:
1. Headline (max 30 characters)
2. Description (max 90 characters)
3. Call to action
4. Target competitor it addresses

Generate 3-5 ad variations.

Format as JSON:
{
  "ads": [
    {
      "headline": "...",
      "description": "...",
      "call_to_action": "...",
      "target_competitor": "...",
      "strategy": "Brief explanation of the approach"
    }
  ]
}
"""


def get_client() -> anthropic.Anthropic:
    """Create an Anthropic client."""
    return anthropic.Anthropic()


def research_competitors(product: str, industry: str) -> dict:
    """Use Claude to research competitors for a given product."""
    client = get_client()

    user_message = (
        f"Research the competitive landscape for: {product}\n"
        f"Industry: {industry}\n\n"
        "Identify the top 3-5 competitors and analyze their positioning."
    )

    console.print(
        Panel(
            f"Researching competitors for [bold]{product}[/bold] "
            f"in [bold]{industry}[/bold]...",
            title="Research",
            border_style="blue",
        )
    )

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        system=RESEARCH_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    response_text = message.content[0].text

    # Extract JSON from response
    try:
        # Try to parse the whole response as JSON
        return json.loads(response_text)
    except json.JSONDecodeError:
        # Try to find JSON block in the response
        start = response_text.find("{")
        end = response_text.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(response_text[start:end])
        raise click.ClickException("Failed to parse competitor research response.")


def generate_ads(product: str, research_data: dict) -> dict:
    """Generate ad copy based on competitive research."""
    client = get_client()

    user_message = (
        f"Our product: {product}\n\n"
        f"Competitive research:\n{json.dumps(research_data, indent=2)}\n\n"
        "Generate compelling ad copy that positions our product against "
        "these competitors."
    )

    console.print(
        Panel(
            f"Generating ad copy for [bold]{product}[/bold]...",
            title="Ad Generation",
            border_style="green",
        )
    )

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        system=AD_GENERATION_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    response_text = message.content[0].text

    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        start = response_text.find("{")
        end = response_text.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(response_text[start:end])
        raise click.ClickException("Failed to parse ad generation response.")


def display_research(data: dict) -> None:
    """Display research results in a formatted table."""
    table = Table(title="Competitor Analysis", show_lines=True)
    table.add_column("Competitor", style="bold cyan", width=20)
    table.add_column("Value Props", width=30)
    table.add_column("Strengths", width=25)
    table.add_column("Weaknesses", width=25)
    table.add_column("Ad Themes", width=25)

    for comp in data.get("competitors", []):
        table.add_row(
            comp.get("name", "N/A"),
            "\n".join(f"- {v}" for v in comp.get("value_propositions", [])),
            "\n".join(f"- {s}" for s in comp.get("strengths", [])),
            "\n".join(f"- {w}" for w in comp.get("weaknesses", [])),
            "\n".join(f"- {t}" for t in comp.get("ad_themes", [])),
        )

    console.print(table)

    if "market_summary" in data:
        console.print(
            Panel(data["market_summary"], title="Market Summary", border_style="yellow")
        )


def display_ads(data: dict) -> None:
    """Display generated ads in formatted panels."""
    console.print("\n[bold]Generated Ad Copy[/bold]\n")

    for i, ad in enumerate(data.get("ads", []), 1):
        content = (
            f"[bold cyan]Headline:[/bold cyan] {ad.get('headline', 'N/A')}\n"
            f"[bold]Description:[/bold] {ad.get('description', 'N/A')}\n"
            f"[bold green]CTA:[/bold green] {ad.get('call_to_action', 'N/A')}\n"
            f"[dim]Target: {ad.get('target_competitor', 'N/A')}[/dim]\n"
            f"[dim]Strategy: {ad.get('strategy', 'N/A')}[/dim]"
        )
        console.print(Panel(content, title=f"Ad #{i}", border_style="magenta"))


@click.group()
def cli():
    """Competitor Ads Generator - Research competitors and generate ad copy."""
    pass


@cli.command()
@click.option(
    "--product",
    "-p",
    prompt="Product or company name",
    help="The product or company to research competitors for.",
)
@click.option(
    "--industry",
    "-i",
    prompt="Industry or market",
    help="The industry or market segment.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Save research results to a JSON file.",
)
def research(product: str, industry: str, output: str | None) -> None:
    """Research competitors in your market."""
    try:
        data = research_competitors(product, industry)
        display_research(data)

        if output:
            with open(output, "w") as f:
                json.dump(data, f, indent=2)
            console.print(f"\nResults saved to [bold]{output}[/bold]")

    except anthropic.APIError as e:
        raise click.ClickException(f"API error: {e}")


@cli.command()
@click.option(
    "--product",
    "-p",
    prompt="Your product name",
    help="Your product name.",
)
@click.option(
    "--research-file",
    "-r",
    type=click.Path(exists=True),
    help="Path to research JSON file (from research command).",
)
@click.option(
    "--industry",
    "-i",
    help="Industry (used if no research file provided).",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Save generated ads to a JSON file.",
)
def generate(
    product: str,
    research_file: str | None,
    industry: str | None,
    output: str | None,
) -> None:
    """Generate competitive ad copy."""
    try:
        if research_file:
            with open(research_file) as f:
                research_data = json.load(f)
        elif industry:
            research_data = research_competitors(product, industry)
        else:
            industry = click.prompt("Industry or market")
            research_data = research_competitors(product, industry)

        ads = generate_ads(product, research_data)
        display_ads(ads)

        if output:
            with open(output, "w") as f:
                json.dump(ads, f, indent=2)
            console.print(f"\nAds saved to [bold]{output}[/bold]")

    except anthropic.APIError as e:
        raise click.ClickException(f"API error: {e}")


@cli.command()
@click.option(
    "--product",
    "-p",
    prompt="Your product name",
    help="Your product name.",
)
@click.option(
    "--industry",
    "-i",
    prompt="Industry or market",
    help="The industry or market segment.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default="full_report.json",
    help="Save full report to a JSON file.",
)
def full_pipeline(product: str, industry: str, output: str) -> None:
    """Run full pipeline: research competitors then generate ads."""
    try:
        research_data = research_competitors(product, industry)
        display_research(research_data)

        ads = generate_ads(product, research_data)
        display_ads(ads)

        report = {"product": product, "industry": industry, "research": research_data, "ads": ads}
        with open(output, "w") as f:
            json.dump(report, f, indent=2)
        console.print(f"\nFull report saved to [bold]{output}[/bold]")

    except anthropic.APIError as e:
        raise click.ClickException(f"API error: {e}")


if __name__ == "__main__":
    cli()
