# Scoring weights meant to be easily adjustable
from __future__ import annotations
from dataclasses import dataclass

# ---------------- Composite weighting ----------------

@dataclass(frozen=True)
class CompositeWeights:
    team: float = 0.4
    market: float = 0.3
    funding: float = 0.3


COMPOSITE_WEIGHTS = CompositeWeights()

# ---------------- Team weights ----------------

TEAM_WEIGHTS: dict[str, float | dict[str, float]] = {
    # Founder / Operator signals
    "top_university": 8,
    "seasoned_operator": 8,
    "seasoned_executive": 12,
    "prior_vc_backed_founder": 18,
    "prior_vc_backed_executive": 12,
    "prior_exit": 18,
    "twenty_m_club": 8,
    "seasoned_adviser": 4,
    "elite_industry_experience": 8,
    "deep_technical_background": 10,
    "five_m_club": 8,

    # Headcount bonus signals 
    "headcount_bonus": {
        "over_two": 3,                 # applies when headcount > 2
        "over_or_equal_to_6": 5,       # applies when headcount >= 6
        "over_or_equal_to_10": 8,      # applies when headcount >= 10
    }
}


# ---------------- Market weights ----------------

VERTICAL_WEIGHTS: dict[str, float] = {
    # CoreVC sectors
    "Business Services": 70.0,
    "Financial Services": 80.0,
    "Real Estate & Construction": 75.0,
    "Life Sciences & Healthcare": 80.0,
}

SUB_VERTICAL_WEIGHTS: dict[str, float] = {
    # Business Services
    "Legal & Compliance Services": 10.0,
    "Staffing, Recruitment & Future of Work": 15.0,
    "Accounting & Finance Services": 10.0,
    "Sales & Customer Service": 10.0,

    # Financial Services
    "Banking & Lending Technology": 15.0,
    "Payment Processing & Infastructure": 15.0,
    "Cryptocurrency & Blockchain": 5.0,
    "Insurance Technology - Insurtech": 15.0,
    "Traditional Financial Services": 10.0,
    "Investor Technology": 10.0,

    # Real Estate & Construction
    "Property Technology - PropTech": 15.0,
    "Traditional Real Estate & Construction": 10.0,

    # Life Sciences & Healthcare
    "Healthcare Insurance & Benefits": 10.0,
    "Biotechnology & Pharmaceuticals": 15.0,
    "Digital Health & Telemedicine": 15.0,
    "Medical Devices & Diagnostic": 15.0,
    "Healthcare Provider Services": 10.0,
    "Healthcare Data & EHR Technology": 10.0,
}

AI_VERTICAL_BONUS: float = 10.0
SMB_ENABLEMENT_BONUS: float = 10.0

# ---------------- Funding weights ----------------

STAGE_BASE_SCORES: dict[str, float] = {
    "PRE_SEED": 65.0,
    "SEED": 45.0,
    "SERIES_A": 25.0,
    "SERIES_B": 0.0,
    "SERIES_C": 0.0,
    "SERIES_D": 0.0,
    "SERIES_E": 0.0,
}

# (upper_bound_inclusive, bonus_score)
FUNDING_BONUS_BRACKETS: list[tuple[float, float]] = [
    (1_000_000, 35.0),
    (5_000_000, 30.0),
    (10_000_000, 25.0),
]

MAX_SCORE: float = 100.0
