# takes raw + enrichment -> returns scoring ready features
from __future__ import annotations
from typing import Optional, Dict, List

from src.merlin.models import (
    RawCompany,
    HarmonicEnrichment,
    EmployeeHighlight,
    FeatureVector,
)


def build_features(
    raw: RawCompany,
    enrichment: Optional[HarmonicEnrichment],
) -> FeatureVector:
    """
    Create a FeatureVector from RawCompany + HarmonicEnrichment.
    Uses ONLY the fields available on HarmonicEnrichment.
    """

    # Defaults: In case we don't get a response back from Harmonic
    stage = None
    funding_total = None
    location = None
    description = None
    market_verticals: List[str] = []
    market_sub_verticals: List[str] = []

    founder_flags = {
        "top_university": False,
        "seasoned_operator": False,
        "seasoned_executive": False,
        "prior_vc_backed_founder": False,
        "prior_vc_backed_executive": False,
        "prior_exit": False,
        "twenty_m_club": False,
        "seasoned_adviser": False,
        "elite_industry_experience": False,
        "deep_technical_background": False,
        "five_m_club": False,
    }


    # Pull from Harmonic enrichment (if available)
    # -----------------------------
    if enrichment is not None:


        #Description
        description = enrichment.description #TODO: Do we want to fall back to raw description?

        # Funding
        stage = enrichment.stage or enrichment.funding_stage
        funding_total = enrichment.funding_total

        # Geography
        if enrichment.location:
            location = enrichment.location.get("location")

        # Sector Fit
        market_verticals = enrichment.market_verticals or []
        market_sub_verticals = enrichment.market_sub_verticals or []

        # Founder Quality Flags
        founder_flags.update(
            _employee_highlights_to_flags(enrichment.employee_highlights or [])
        )
    # -----------------------------

    
    # Build the FeatureVector
    # -----------------------------
    return FeatureVector(
        stage=stage,
        funding_total=funding_total,
        location=location,
        description=description,
        market_verticals=market_verticals,
        market_sub_verticals=market_sub_verticals,
        top_university=founder_flags["top_university"],
        seasoned_operator=founder_flags["seasoned_operator"],
        seasoned_executive=founder_flags["seasoned_executive"],
        prior_vc_backed_founder=founder_flags["prior_vc_backed_founder"],
        prior_vc_backed_executive=founder_flags["prior_vc_backed_executive"],
        prior_exit=founder_flags["prior_exit"],
        twenty_m_club=founder_flags["twenty_m_club"],
        seasoned_adviser=founder_flags["seasoned_adviser"],
        elite_industry_experience=founder_flags["elite_industry_experience"],
        deep_technical_background=founder_flags["deep_technical_background"],
        five_m_club=founder_flags["five_m_club"],
    )
    # -----------------------------



# Helper Functions
# -------------------------------------------------------------------

def _employee_highlights_to_flags(highlights: List[EmployeeHighlight]) -> Dict[str, bool]:
    flags = {
        "top_university": False,
        "seasoned_operator": False,
        "seasoned_executive": False,
        "prior_vc_backed_founder": False,
        "prior_vc_backed_executive": False,
        "prior_exit": False,
        "twenty_m_club": False,
        "seasoned_adviser": False,
        "elite_industry_experience": False,
        "deep_technical_background": False,
        "five_m_club": False,
    }

    for h in highlights:
        cat = (h.category or "").upper()


        # TODO: Harmonic doesn't clearly state in API docs how many of these tags there are. Review
        if cat == "TOP_UNIVERSITY":
            flags["top_university"] = True
        elif cat == "SEASONED_OPERATOR":
            flags["seasoned_operator"] = True
        elif cat == "SEASONED_EXECUTIVE":
            flags["seasoned_executive"] = True
        elif cat == "PRIOR_VC_BACKED_FOUNDER":
            flags["prior_vc_backed_founder"] = True
        elif cat == "PRIOR_VC_BACKED_EXECUTIVE":
            flags["prior_vc_backed_executive"] = True
        elif cat == "PRIOR_EXIT":
            flags["prior_exit"] = True
        elif cat in ("20_M_CLUB", "TWENTY_M_CLUB"):
            flags["twenty_m_club"] = True
        elif cat == "SEASONED_ADVISER":
            flags["seasoned_adviser"] = True
        elif cat == "ELITE_INDUSTRY_EXPERIENCE":
            flags["elite_industry_experience"] = True
        elif cat == "DEEP_TECHNICAL_BACKGROUND":
            flags["deep_technical_background"] = True
        elif cat in ("5_M_CLUB", "FIVE_M_CLUB"):
            flags["five_m_club"] = True

    return flags
# -------------------------------------------------------------------
