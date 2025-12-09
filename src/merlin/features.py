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
    Prefers Harmonic fields but falls back to RawCompany where helpful.
    """

    # --- Defaults ---
    description: str = raw.description or ""
    stage: str = raw.stage or ""
    funding_total: int = 0
    location: str = ""
    headcount: int = 0
    customer_type: str = ""
    market_verticals: List[str] = []
    market_sub_verticals: List[str] = []

    # ---Founder highlight flags (all default False) ---
    base_flags: dict[str, bool] = {
        "ten_m_club": False,
        "twenty_m_club": False,
        "fifty_m_plus_club": False,
        "five_m_club": False,
        "current_student": False,
        "deep_technical_background": False,
        "elite_industry_experience": False,
        "founder_turned_operator": False,
        "hbcu_alum": False,
        "jack_of_all_trades": False,
        "legacy_tech_company_experience": False,
        "major_research_institution_experience": False,
        "major_tech_company_experience": False,
        "prior_exit": False,
        "prior_vc_backed_executive": False,
        "prior_vc_backed_founder": False,
        "seasoned_adviser": False,     
        "seasoned_executive": False,
        "seasoned_founder": False,
        "seasoned_operator": False,
        "top_ai_experience": False,
        "top_company_alum": False,
        "top_university": False,
        "top_web3_experience": False,
        "yc_backed_founder": False,
    }

    employee_flags = dict(base_flags)  # all employees
    founder_flags = dict(base_flags)   # founder-only

    # --- ENrichment ---
    if enrichment is not None:
        # Description: combine raw + harmonic so SMB signals are not lost
        if enrichment.description:
            description = " ".join([raw.description or "", enrichment.description]).strip()
        else:
            description = raw.description or ""
        
        # Headcount
        if enrichment.headcount is not None:
            headcount = enrichment.headcount

        # Funding / Stage
        if enrichment.stage or enrichment.funding_stage:
            stage = enrichment.stage or enrichment.funding_stage or stage
        if enrichment.funding_total is not None:
            funding_total = int(enrichment.funding_total)

        # Geography
        if enrichment.location:
            location = enrichment.location.get("location") or location

        # Sector fit
        market_verticals = enrichment.market_verticals or []
        market_sub_verticals = enrichment.market_sub_verticals or []
        customer_type = enrichment.customer_type or ""

        # --- Employee/advisor highlights → flags (only used for seasoned_adviser) ---
        if enrichment.employee_highlights:
            employee_flags.update(
                _employee_highlights_to_flags(enrichment.employee_highlights)
            )

        # --- Founder-only highlights → flags ---
        if getattr(enrichment, "founder_employee_highlights", None):
            founder_flags.update(
                _employee_highlights_to_flags(enrichment.founder_employee_highlights)
            )

    # --- Combine into final flags ---
    combined_flags: dict[str, bool] = {}
    for key in base_flags.keys():
        if key == "seasoned_adviser":
            # NOTE: Future improvement: bring in non founder season advisers
            combined_flags[key] = founder_flags[key]
        else:
            # All other signals are founder-only
            combined_flags[key] = founder_flags[key]

    # --- Build FeatureVector for scoring ---
    return FeatureVector(
        description=description,
        headcount=headcount,
        customer_type=customer_type,
        stage=stage,
        funding_total=funding_total,
        location=location,
        market_verticals=market_verticals,
        market_sub_verticals=market_sub_verticals,
        ten_m_club=combined_flags["ten_m_club"],
        twenty_m_club=combined_flags["twenty_m_club"],
        fifty_m_plus_club=combined_flags["fifty_m_plus_club"],
        five_m_club=combined_flags["five_m_club"],
        current_student=combined_flags["current_student"],
        deep_technical_background=combined_flags["deep_technical_background"],
        elite_industry_experience=combined_flags["elite_industry_experience"],
        founder_turned_operator=combined_flags["founder_turned_operator"],
        hbcu_alum=combined_flags["hbcu_alum"],
        jack_of_all_trades=combined_flags["jack_of_all_trades"],
        legacy_tech_company_experience=combined_flags["legacy_tech_company_experience"],
        major_research_institution_experience=combined_flags["major_research_institution_experience"],
        major_tech_company_experience=combined_flags["major_tech_company_experience"],
        prior_exit=combined_flags["prior_exit"],
        prior_vc_backed_executive=combined_flags["prior_vc_backed_executive"],
        prior_vc_backed_founder=combined_flags["prior_vc_backed_founder"],
        seasoned_adviser=combined_flags["seasoned_adviser"],
        seasoned_executive=combined_flags["seasoned_executive"],
        seasoned_founder=combined_flags["seasoned_founder"],
        seasoned_operator=combined_flags["seasoned_operator"],
        top_ai_experience=combined_flags["top_ai_experience"],
        top_company_alum=combined_flags["top_company_alum"],
        top_university=combined_flags["top_university"],
        top_web3_experience=combined_flags["top_web3_experience"],
        yc_backed_founder=combined_flags["yc_backed_founder"],
    )



# --- Helper Functions ---
# maps Harmonic highlight category → FeatureVector boolean field
HIGHLIGHT_CATEGORY_TO_FLAG: dict[str, str] = {
    "$10M Club": "ten_m_club",
    "$20M Club": "twenty_m_club",
    "$50M+ Club": "fifty_m_plus_club",
    "$5M Club": "five_m_club",
    "Current Student": "current_student",
    "Deep Technical Background": "deep_technical_background",
    "Elite Industry Experience": "elite_industry_experience",
    "Founder Turned Operator": "founder_turned_operator",
    "HBCU Alum": "hbcu_alum",
    "Jack of All Trades": "jack_of_all_trades",
    "Legacy Tech Company Experience": "legacy_tech_company_experience",
    "Major Research Institution Experience": "major_research_institution_experience",
    "Major Tech Company Experience": "major_tech_company_experience",
    "Prior Exit": "prior_exit",
    "Prior VC Backed Executive": "prior_vc_backed_executive",
    "Prior VC Backed Founder": "prior_vc_backed_founder",
    "Seasoned Adviser": "seasoned_adviser",
    "Seasoned Executive": "seasoned_executive",
    "Seasoned Founder": "seasoned_founder",
    "Seasoned Operator": "seasoned_operator",
    "Top AI Experience": "top_ai_experience",
    "Top Company Alum": "top_company_alum",
    "Top University": "top_university",
    "Top Web3 Experience": "top_web3_experience",
    "YC Backed Founder": "yc_backed_founder",
}


def _employee_highlights_to_flags(
    highlights: list[EmployeeHighlight] | list[dict],
) -> dict[str, bool]:
    """
    Takes a list of employee highlight objects or dicts and returns binary flags
    """
    flags: dict[str, bool] = {v: False for v in HIGHLIGHT_CATEGORY_TO_FLAG.values()}

    for h in highlights or []:
        # Support both dataclass and dict shapes
        if isinstance(h, EmployeeHighlight):
            cat = h.category
        else:
            cat = h.get("category")

        if not cat:
            continue

        flag_name = HIGHLIGHT_CATEGORY_TO_FLAG.get(cat)
        if flag_name:
            flags[flag_name] = True

    return flags