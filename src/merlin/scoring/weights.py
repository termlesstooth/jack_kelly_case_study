# Scoring weights meant to be easily adjustable
from __future__ import annotations
from dataclasses import dataclass

# --- Composite Weights ---
@dataclass(frozen=True)
class CompositeWeights:
    team: float = 0.45
    market: float = 0.35
    funding: float = 0.20


COMPOSITE_WEIGHTS = CompositeWeights()

# --- Founder signals ---
# Currently these are just founder signals.
# TODO: Future improvement, bring in non founder information.
TEAM_WEIGHTS: dict[str, float] = {
    "top_university": 6,
    "top_company_alum": 10, # Accounts for Arjan mentioning an interest in founders that are from a top company. Indicator that they are mission driven.
    "top_ai_experience": 18, # Even stronger indicator than top company that they are mission driven.
    "top_web3_experience": 10,
    "major_tech_company_experience": 15, # Even stronger indicator than top company that they are mission driven.
    "legacy_tech_company_experience": 4,
    "major_research_institution_experience": 8,
    "deep_technical_background": 10,
    "elite_industry_experience": 10, # Another indicator they are leaving a stable job and therfore mission driven
    "seasoned_operator": 8,
    "seasoned_executive": 12,
    "seasoned_founder": 20,
    "seasoned_adviser": 5,
    "prior_vc_backed_founder": 18,
    "prior_vc_backed_executive": 12,
    "prior_exit": 18,
    "yc_backed_founder": 12,
    "five_m_club": 4,
    "ten_m_club": 6,
    "twenty_m_club": 8,
    "fifty_m_plus_club": 10,
    "founder_turned_operator": 0,
    "hbcu_alum": 5,
    "jack_of_all_trades": 2,
    "current_student": 0,
}

# No limited to just founders.
HEADCOUNT_BONUS = {
    "over_two": 5.0,
    "over_or_equal_to_6": 15.0,
    "over_or_equal_to_10": 20.0,
}

# --- Sector Weights ---
# NOTE: These are derived from Harmonic. Sub verticals are children of verticals. But not all verticals have sub verticals.
VERTICAL_WEIGHTS: dict[str, float] = {
    # CoreVC sectors, based on Harmonic verticals
    "Business Services": 65.0,
    "Financial Services": 85.0, 
    "Real Estate & Construction": 65, # NOTE: Harmonic doesn't separate real estate from construction (these 2 seem very different)
    "Life Sciences & Healthcare": 65, # lower here because I didn't hear about Life Sciences specifically. Make up for it in sub vertical weights
    # Other sectors
    "Communications & Information Technology": 0,
    "Cybersecurity": 0,
    "Transportation & Logistics": 0,
    "Energy & Utilities": 0,
    "Education & Research": 0,
    "Industrial & Manufacturing": 0,
    "Media & Entertainment": 0,
    "Consumer Products & Services": 0

}

SUB_VERTICAL_WEIGHTS: dict[str, float] = {
    # Business Services
    "Legal & Compliance Services": 5.0,
    "Staffing, Recruitment & Future Of Work": 10.0,
    "Accounting & Finance Services": 10.0,
    "Sales & Customer Service": 5.0,

    # Financial Services
    "Banking & Lending Technology": 10.0,
    "Payment Processing & Infrastructure": 10.0,
    "Cryptocurrency & Blockchain": 3.0, # Not sure where Core stands on Web 3
    "Insurance Technology - Insurtech": 10,
    "Traditional Financial Services": 10.0,
    "Investor Technology": 5.0,

    # Real Estate & Construction
    "Property Technology - PropTech": 5, 
    "Real Estate & Construction": 10, # NOTE: This seems like too broad a sub-vertical. Future Improvement

    # Life Sciences & Healthcare # NOTE: higher weights since vertical is weighted lower
    "Healthcare Insurance & Benefits": 25.0,
    "Biotechnology & Pharmaceuticals": 20.0,
    "Digital Health & Telemedicine": 10.0,
    "Medical Devices & Diagnostics": 5.0,
    "Healthcare Provider Services": 25.0,
    "Healthcare Data & EHR Technology": 25.0,
    "Analytics & Business Intelligence Platforms": 5,

    # Communications & Information Technology
    "Advertising & Marketing Technology": 0,
    "Enterprise Productivity & Automation": 0,
    "Chatbots, Assistants, & AI Search": 0,
    "Developer Operations & AI Building Tools": 0,
    "Personal Productivity - Prosumer": 0,
    "Data Infrastructure & Cloud Services": 0,

    # Consumer Products & Services
    "Consumer Goods & Retail": 0,
    "Home Services": 25, # Higher because it's vertical has a weight of 0
    "Personal Services": 0,
    "E-Commerce & Marketplaces": 0,
    "Consumer Software & Apps": 0,

    # Cybersecurity
    "Identity & Access Management": 0,
    "Security Software & Services": 0,

    # Transportation & Logistics
    "Logistics & Supply Chain Technology": 0,

    # Energy & Utilities
    "Climate Tech & Carbon Solutions": 0,
    "Renewable Energy Technology": 0,

    # Education & Research
    "Educational Technology - Edtech": 0,

    # Industrial & Manufacturing
    "Electric Vehicles & Mobility Tech": 0,

    # Media & Entertainment
    "Gaming & Interactive Entertainment": 0,
}

AI_VERTICAL_BONUS: float = 0 # NOTE: Website specifically mentions Core doesn't chase hype.

SMB_ENABLEMENT_BONUS: float = 15.0


# --- Funding Weights ---
STAGE_BASE_SCORES: dict[str, float] = {
    "PRE_SEED": 65.0, # I have learned that Core wants more outbound, this means investing in relationships earlier.
    "SEED": 45.0,
    "SERIES_A": 25.0,
    "SERIES_B": 0.0,
    "SERIES_C": 0.0,
    "SERIES_D": 0.0,
    "SERIES_E": 0.0,
}

# upper_bound_inclusive, bonus_score
FUNDING_BONUS_BRACKETS: list[tuple[float, float]] = [
    (1_000_000, 25.0),
    (5_000_000, 15.0),
    (10_000_000, 10.0),
]

MAX_SCORE: float = 100.0
