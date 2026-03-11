"""CLI entrypoint for the Competitor Ads Generator & Optimizer."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from analytics.performance_tracker import PerformanceTracker
from analytics.reporter import PerformanceReporter
from analytics.scorer import AdScorer
from config.brand_kit import BrandKit, load_brand_kit
from config.settings import AppConfig, load_config
from generator.copy_generator import CopyGenerator
from generator.creative_assembler import CreativeAssembler
from meta_ads.auth import MetaAuth
from meta_ads.campaign_manager import CampaignManager
from meta_ads.uploader import CreativeUploader
from models.ad_creative import GeneratedCreative
from models.campaign import Ad, AdSet, Campaign, CampaignStatus, TargetingSpec
from optimizer.decision_engine import DecisionEngine
from optimizer.iteration_generator import IterationGenerator
from optimizer.scheduler import OptimizationScheduler
from research.ad_library_scraper import AdLibraryScraper
from research.competitor_analyzer import CompetitorAnalyzer

console = Console()


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[RichHandler(console=console, rich_tracebacks=True)],
    )


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.pass_context
def cli(ctx: click.Context, verbose: bool) -> None:
    """Competitor Ads Generator & Optimizer.

    Research competitor ads, generate branded creatives,
    upload to Meta, and auto-optimize performance.
    """
    setup_logging(verbose)
    ctx.ensure_object(dict)
    ctx.obj["config"] = load_config()
    ctx.obj["brand_kit"] = load_brand_kit()


@cli.command()
@click.option(
    "--competitor-pages",
    "-c",
    multiple=True,
    help="Competitor Facebook page IDs/slugs (defaults to configured competitors)",
)
@click.option("--keyword", "-k", multiple=True, help="Search keywords for Ad Library")
@click.option("--use-config-keywords", is_flag=True, help="Also search configured keywords")
@click.option("--limit", "-l", default=50, help="Max ads per competitor")
@click.option("--output", "-o", default="research_results.json", help="Output file")
@click.pass_context
def research(
    ctx: click.Context,
    competitor_pages: tuple[str, ...],
    keyword: tuple[str, ...],
    use_config_keywords: bool,
    limit: int,
    output: str,
) -> None:
    """Phase 1: Research competitor ads from Meta Ad Library."""
    config: AppConfig = ctx.obj["config"]

    console.print(Panel("[bold blue]Phase 1: Competitor Research[/bold blue]"))

    # Use configured competitors if none specified on CLI
    pages = list(competitor_pages)
    if not pages:
        pages = [c.page_slug for c in config.competitors.competitors if c.page_slug]
        console.print(
            f"Using {len(pages)} configured competitors: "
            + ", ".join(c.name for c in config.competitors.competitors if c.page_slug)
        )

    # Collect keywords from CLI args and/or config
    keywords = list(keyword)
    if use_config_keywords:
        keywords.extend(config.competitors.search_keywords)

    scraper = AdLibraryScraper(config.meta)
    analyzer = CompetitorAnalyzer()

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Scrape competitor ads
        task = progress.add_task("Scraping competitor ads...", total=None)
        all_ads = scraper.search_competitors(pages, limit)

        for kw in keywords:
            progress.update(task, description=f"Searching keyword: {kw}")
            keyword_ads = scraper.search_by_keyword(kw, limit=limit)
            all_ads.extend(keyword_ads)

        progress.update(task, description="Analyzing patterns...")
        insights = analyzer.analyze(all_ads)
        seed_ads = analyzer.get_seed_ads(insights)

    # Display results
    table = Table(title="Research Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Total ads found", str(insights.total_ads_analyzed))
    table.add_row("Top performers", str(len(insights.top_performers)))
    table.add_row("Patterns detected", str(len(insights.patterns)))
    table.add_row("Seed ads selected", str(len(seed_ads)))
    table.add_row("Avg text length", f"{insights.avg_text_length} chars")
    console.print(table)

    # Save results
    output_path = Path(output)
    results = {
        "total_ads": insights.total_ads_analyzed,
        "seed_ads": [ad.model_dump(mode="json") for ad in seed_ads],
        "patterns": [
            {
                "hook_style": p.hook_style,
                "tone": p.tone,
                "avg_text_length": p.avg_text_length,
            }
            for p in insights.patterns
        ],
        "common_hooks": insights.common_hooks,
        "common_ctas": insights.common_ctas,
    }
    output_path.write_text(json.dumps(results, indent=2, default=str))
    console.print(f"\nResults saved to [bold]{output_path}[/bold]")

    scraper.close()


@cli.command()
@click.option(
    "--research-file",
    "-r",
    default="research_results.json",
    help="Research results from Phase 1",
)
@click.option("--count", "-n", default=100, help="Number of creatives to generate")
@click.option("--output-dir", "-o", default="output", help="Output directory")
@click.pass_context
def generate(
    ctx: click.Context,
    research_file: str,
    count: int,
    output_dir: str,
) -> None:
    """Phase 2: Generate ad creatives using Claude API."""
    config: AppConfig = ctx.obj["config"]
    brand_kit: BrandKit = ctx.obj["brand_kit"]

    console.print(Panel("[bold green]Phase 2: Creative Generation[/bold green]"))

    # Load research results
    research_path = Path(research_file)
    if not research_path.exists():
        console.print(f"[red]Research file not found: {research_file}[/red]")
        console.print("Run 'research' command first.")
        sys.exit(1)

    data = json.loads(research_path.read_text())

    from models.ad_creative import CompetitorAd
    from research.competitor_analyzer import AdPattern

    seed_ads = [CompetitorAd(**ad) for ad in data["seed_ads"]]
    patterns = [AdPattern(**p, cta_style="", common_phrases=[], example_ad_ids=[]) for p in data["patterns"]]

    # Update generation config
    config.generation.total_creatives = count

    # Generate
    generator = CopyGenerator(config.claude, brand_kit, config.generation)
    assembler = CreativeAssembler(brand_kit, output_dir)

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Generating {count} creatives...", total=None)
        creatives = generator.generate_all(seed_ads, patterns)

        progress.update(task, description="Applying brand kit...")
        creatives = assembler.assemble_all(creatives)

    # Display summary
    format_counts: dict[str, int] = {}
    for c in creatives:
        format_counts[c.format.value] = format_counts.get(c.format.value, 0) + 1

    table = Table(title="Generation Summary")
    table.add_column("Format", style="cyan")
    table.add_column("Count", style="green")
    for fmt, cnt in format_counts.items():
        table.add_row(fmt, str(cnt))
    table.add_row("[bold]Total[/bold]", f"[bold]{len(creatives)}[/bold]")
    console.print(table)

    # Export brief
    brief = assembler.export_brief(creatives)
    console.print(f"\nCreative brief saved to [bold]{output_dir}/creative_brief.md[/bold]")

    # Save creatives as JSON for upload phase
    creatives_path = Path(output_dir) / "creatives.json"
    creatives_data = [c.model_dump(mode="json") for c in creatives]
    creatives_path.write_text(json.dumps(creatives_data, indent=2, default=str))
    console.print(f"Creatives data saved to [bold]{creatives_path}[/bold]")


@cli.command()
@click.option(
    "--creatives-file",
    "-c",
    default="output/creatives.json",
    help="Creatives JSON from Phase 2",
)
@click.option("--campaign-name", "-n", required=True, help="Name for the campaign")
@click.option("--daily-budget", "-b", default=50.0, help="Daily budget in dollars")
@click.option("--dry-run", is_flag=True, help="Validate without uploading")
@click.pass_context
def upload(
    ctx: click.Context,
    creatives_file: str,
    campaign_name: str,
    daily_budget: float,
    dry_run: bool,
) -> None:
    """Phase 3: Upload creatives to Meta Ads account."""
    config: AppConfig = ctx.obj["config"]

    console.print(Panel("[bold yellow]Phase 3: Upload to Meta Ads[/bold yellow]"))

    # Load creatives
    creatives_path = Path(creatives_file)
    if not creatives_path.exists():
        console.print(f"[red]Creatives file not found: {creatives_file}[/red]")
        sys.exit(1)

    data = json.loads(creatives_path.read_text())
    creatives = [GeneratedCreative(**c) for c in data]
    console.print(f"Loaded {len(creatives)} creatives")

    if dry_run:
        console.print("[yellow]DRY RUN — no changes will be made[/yellow]")
        return

    # Initialize Meta API
    auth = MetaAuth(config.meta)
    if not auth.validate_connection():
        console.print("[red]Failed to connect to Meta Ads API[/red]")
        sys.exit(1)

    campaign_mgr = CampaignManager(auth)
    uploader = CreativeUploader(auth, config.meta)

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Create campaign
        task = progress.add_task("Creating campaign...", total=None)
        campaign = Campaign(name=campaign_name, daily_budget=daily_budget)
        campaign = campaign_mgr.create_campaign(campaign)

        # Create ad set
        progress.update(task, description="Creating ad set...")
        ad_set = AdSet(
            campaign_id=campaign.campaign_id,
            name=f"{campaign_name} — Test Set",
            daily_budget=daily_budget,
        )
        ad_set = campaign_mgr.create_ad_set(ad_set)

        # Upload creatives and create ads
        progress.update(task, description="Uploading creatives...")
        meta_ids = uploader.upload_batch(creatives)

        progress.update(task, description="Creating ads...")
        created_count = 0
        for creative in creatives:
            meta_creative_id = meta_ids.get(creative.creative_id)
            if not meta_creative_id:
                continue

            ad = Ad(
                ad_set_id=ad_set.ad_set_id,
                name=f"Ad: {creative.headline[:40]}",
                creative_id=creative.creative_id,
                status=CampaignStatus.PAUSED,
            )
            campaign_mgr.create_ad(ad, meta_creative_id)
            created_count += 1

    console.print(f"\n[green]Campaign created: {campaign.campaign_id}[/green]")
    console.print(f"[green]Ad set created: {ad_set.ad_set_id}[/green]")
    console.print(f"[green]Ads created: {created_count}[/green]")
    console.print(
        "\n[yellow]Ads are PAUSED. Activate them in Meta Ads Manager "
        "or run the 'optimize' command.[/yellow]"
    )


@cli.command()
@click.option("--campaign-id", "-c", required=True, help="Meta campaign ID")
@click.option("--days", "-d", default=7, help="Days of data to analyze")
@click.pass_context
def analytics(ctx: click.Context, campaign_id: str, days: int) -> None:
    """Phase 4: View campaign performance analytics."""
    config: AppConfig = ctx.obj["config"]

    console.print(Panel("[bold magenta]Phase 4: Performance Analytics[/bold magenta]"))

    auth = MetaAuth(config.meta)
    tracker = PerformanceTracker(auth)
    reporter = PerformanceReporter()

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Fetching performance data...", total=None)
        report = tracker.get_campaign_performance(campaign_id, days)

    summary = reporter.generate_summary(report)
    console.print(summary)


@cli.command()
@click.option("--campaign-id", "-c", required=True, help="Meta campaign ID to optimize")
@click.option("--days", "-d", default=7, help="Days of data to analyze")
@click.option("--iterate/--no-iterate", default=True, help="Generate iterations of winners")
@click.option("--dry-run", is_flag=True, help="Show decisions without executing")
@click.pass_context
def optimize(
    ctx: click.Context,
    campaign_id: str,
    days: int,
    iterate: bool,
    dry_run: bool,
) -> None:
    """Phase 5: Auto-optimize — kill losers, iterate winners."""
    config: AppConfig = ctx.obj["config"]
    brand_kit: BrandKit = ctx.obj["brand_kit"]

    console.print(
        Panel("[bold red]Phase 5: Auto-Optimization[/bold red]")
    )

    # Initialize components
    auth = MetaAuth(config.meta)
    tracker = PerformanceTracker(auth)
    scorer = AdScorer(config.thresholds)
    campaign_mgr = CampaignManager(auth)
    reporter = PerformanceReporter()
    engine = DecisionEngine(tracker, scorer, campaign_mgr, reporter)

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Running optimization cycle...", total=None)
        decisions = engine.run_optimization_cycle(campaign_id, days, dry_run)

    # Display decisions
    decision_report = reporter.generate_decision_report(decisions)
    console.print(decision_report)

    winners = engine.get_winners(decisions)
    losers = engine.get_losers(decisions)

    console.print(f"\n[green]Winners to iterate: {len(winners)}[/green]")
    console.print(f"[red]Losers paused: {len(losers)}[/red]")

    # Generate iterations of winners
    if iterate and winners and not dry_run:
        console.print("\n[bold]Generating iterations of top performers...[/bold]")

        copy_gen = CopyGenerator(config.claude, brand_kit, config.generation)
        uploader = CreativeUploader(auth, config.meta)
        iter_gen = IterationGenerator(copy_gen, uploader, campaign_mgr)

        # Load creative map (you'd persist this from the generate phase)
        creative_map: dict[str, GeneratedCreative] = {}

        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Creating iterations...", total=None)
            iterations = iter_gen.iterate_winners(
                winners=winners,
                creative_map=creative_map,
                ad_set_id="",  # Would come from the campaign structure
                variations_per_winner=5,
            )

        console.print(f"[green]Created {len(iterations)} new iterations[/green]")


@cli.command()
@click.option("--campaign-id", "-c", required=True, help="Meta campaign ID")
@click.option("--analytics-hours", default=6, help="Hours between analytics polls")
@click.option("--optimize-hours", default=24, help="Hours between optimization cycles")
@click.pass_context
def autopilot(
    ctx: click.Context,
    campaign_id: str,
    analytics_hours: int,
    optimize_hours: int,
) -> None:
    """Run continuous auto-optimization loop."""
    config: AppConfig = ctx.obj["config"]
    brand_kit: BrandKit = ctx.obj["brand_kit"]

    console.print(
        Panel("[bold cyan]Autopilot Mode[/bold cyan]\n"
              f"Campaign: {campaign_id}\n"
              f"Analytics every {analytics_hours}h\n"
              f"Optimization every {optimize_hours}h")
    )

    # Initialize all components
    auth = MetaAuth(config.meta)
    tracker = PerformanceTracker(auth)
    scorer = AdScorer(config.thresholds)
    campaign_mgr = CampaignManager(auth)
    reporter = PerformanceReporter()
    engine = DecisionEngine(tracker, scorer, campaign_mgr, reporter)

    config.scheduler.analytics_poll_interval_hours = analytics_hours
    config.scheduler.optimization_check_interval_hours = optimize_hours
    scheduler = OptimizationScheduler(config.scheduler)

    def run_analytics() -> None:
        report = tracker.get_campaign_performance(campaign_id)
        summary = reporter.generate_summary(report)
        console.print(summary)

    def run_optimization() -> None:
        decisions = engine.run_optimization_cycle(campaign_id)
        decision_report = reporter.generate_decision_report(decisions)
        console.print(decision_report)

    scheduler.schedule_analytics(run_analytics)
    scheduler.schedule_optimization(run_optimization)

    console.print("[green]Autopilot started. Press Ctrl+C to stop.[/green]")
    scheduler.start()


if __name__ == "__main__":
    cli()
