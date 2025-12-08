# takes a rawcomapny + harmonicenrichment and returns a scoredCompanyRecord
from __future__ import annotations

from typing import Tuple, Optional, Dict, Any

from src.merlin.models import (
    RawCompany,
    HarmonicEnrichment,
    FeatureVector,
    ScoreBreakdown,
    ScoredCompanyRecord,
)
from src.merlin.features import build_features
from src.merlin.scoring.scoring import score_company


def process_company(
    raw: RawCompany,
    enrichment: HarmonicEnrichment,
) -> ScoredCompanyRecord:
    """
    Full pipeline for a single company:
    RawCompany + HarmonicEnrichment -> FeatureVector -> ScoreBreakdown -> ScoredCompanyRecord
    """

    features: FeatureVector = build_features(raw, enrichment)
    print(features)
    scores: ScoreBreakdown = score_company(features)

    website_url = enrichment.website_url or f"https://{enrichment.website_domain}" if enrichment.website_domain else raw.url
    website_domain = enrichment.website_domain or raw.url

    # Sectors = market_verticals from enrichment/FeatureVector
    sectors = enrichment.market_verticals or features.market_verticals or []
    sub_sectors = enrichment.market_sub_verticals or features.market_sub_verticals

    # TODO: clean up enrichment vs features
    return ScoredCompanyRecord(
        name=raw.name,
        headcount = enrichment.headcount,
        customer_type = enrichment.customer_type,
        website_url=website_url,
        website_domain=website_domain,
        description=enrichment.description,
        sectors=sectors,
        sub_sectors = sub_sectors,
        location = features.location,
        stage=features.stage,
        funding_total=features.funding_total,
        founders=enrichment.founders or [],
        scores=scores,
        features=features.__dict__,  # easy JSON/debug view'
        harmonic = enrichment # TODO: REMOVE THIS LATER. TERRIBLE PRACTICE. ONLY ADDING BERCAUSE THE ASK WAS TO ADD ENRICHMENT INFO IN WITH SCORE INTO ONE TABLE
    )


# -------------------------------------------------------------------
# Helpers
def _extract_country_state(location: Optional[Dict[str, Any]]) -> Tuple[Optional[str], Optional[str]]:
    """
    Very naive parser that expects location["location"] like:
        "San Francisco, California, United States"
    Returns (country, state) -> ("United States", "California") in that case.
    """
    if not location:
        return None, None

    loc_str = (location.get("location") or "").strip()
    if not loc_str:
        return None, None

    parts = [p.strip() for p in loc_str.split(",") if p.strip()]
    if len(parts) >= 2:
        country = parts[-1]
        state = parts[-2]
        return country, state

    # Fallback: only one part, treat as country
    return parts[0], None
# -------------------------------------------------------------------
