# Competitor Ads Generator & Optimizer

## Overview
An automated pipeline that:
1. Researches competitor ad creatives (Meta Ad Library)
2. Generates new ad variations using your brand kit
3. Uploads to Meta Ads Manager
4. Monitors performance analytics
5. Auto-kills underperformers and iterates on winners

## Architecture

```
competitor-ads-generator/
├── config/
│   ├── settings.py          # App config, API keys, thresholds
│   └── brand_kit.py         # Brand colors, fonts, logos, tone of voice
├── research/
│   ├── ad_library_scraper.py    # Meta Ad Library API client
│   ├── competitor_analyzer.py   # Analyze top-performing patterns
│   └── trend_detector.py        # Detect hooks, CTAs, formats that work
├── generator/
│   ├── prompt_builder.py        # Build generation prompts from seed ads
│   ├── copy_generator.py        # Generate ad copy variations (Claude API)
│   ├── image_generator.py       # Generate/adapt visuals (placeholder for image API)
│   └── creative_assembler.py    # Combine copy + visuals into final creatives
├── meta_ads/
│   ├── auth.py                  # Meta Marketing API OAuth flow
│   ├── campaign_manager.py      # Create campaigns, ad sets, ads
│   ├── uploader.py              # Upload creatives to Meta
│   └── ad_builder.py            # Build ad objects with targeting
├── analytics/
│   ├── performance_tracker.py   # Poll Meta Insights API
│   ├── scorer.py                # Score ads (CTR, CPA, ROAS, etc.)
│   └── reporter.py              # Generate performance reports
├── optimizer/
│   ├── decision_engine.py       # Kill/scale/iterate decisions
│   ├── iteration_generator.py   # Create new versions of winners
│   └── scheduler.py             # Run optimization loops on schedule
├── models/
│   ├── ad_creative.py           # Data models for ad creatives
│   ├── campaign.py              # Campaign/ad set models
│   └── performance.py           # Performance metrics models
├── main.py                      # CLI entrypoint
├── requirements.txt             # Dependencies
└── README.md                    # Setup & usage docs
```

## Phase 1: Competitor Research
- Connect to Meta Ad Library API
- Search competitors by page name, keyword, or category
- Extract: ad copy, CTA, format (image/video/carousel), estimated spend
- Rank by estimated performance signals (longevity, engagement)
- Store top N seed ads for generation

## Phase 2: Creative Generation (100 variations)
- Parse seed ads into structured components (hook, body, CTA, visual style)
- Use Claude API to generate copy variations with brand voice
- Apply brand kit (colors, logo placement, font) to visual templates
- Generate 100 unique creatives across formats:
  - 40 single image ads
  - 30 carousel ads
  - 20 video script ads
  - 10 story/reel format ads

## Phase 3: Meta Ads Upload
- Authenticate via Meta Marketing API (OAuth 2.0)
- Create campaign structure (campaign → ad sets → ads)
- Upload creatives with A/B test structure
- Set initial budgets and targeting
- Enable Meta's auto-placement

## Phase 4: Performance Analytics
- Poll Meta Insights API on schedule (hourly/daily)
- Track: CTR, CPC, CPM, CPA, ROAS, frequency, relevance score
- Store historical performance data
- Generate dashboards/reports

## Phase 5: Auto-Optimization Loop
- Define kill thresholds (e.g., CPA > 2x target after 1000 impressions)
- Auto-pause underperformers
- Identify top 10% performers
- Generate new iterations of winners (modify hook, CTA, or visual)
- Upload new iterations and restart the cycle

## Key Metrics for Decision Engine
| Metric | Kill Threshold | Scale Threshold |
|--------|---------------|-----------------|
| CTR    | < 0.5%        | > 2.0%          |
| CPA    | > 2x target   | < 0.7x target   |
| ROAS   | < 1.0x        | > 3.0x          |
| Frequency | > 4.0      | N/A             |

## API Dependencies
- **Meta Marketing API** — Campaign management, insights
- **Meta Ad Library API** — Competitor research
- **Claude API** — Copy generation and iteration
- **Image generation API** — Visual creation (configurable)

## Tech Stack
- Python 3.11+
- `facebook-business` SDK
- `anthropic` Python SDK
- `pydantic` for data models
- `apscheduler` for scheduling
- `rich` for CLI output
- `sqlite` for local data persistence
