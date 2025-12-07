# Compute numerical scores from a FeatureVector, nothign else.
from __future__ import annotations

from src.merlin.models import FeatureVector, ScoreBreakdown


def score_company(features: FeatureVector) -> ScoreBreakdown:
    """
    High-level scoring entrypoint.
    Returns per-criterion scores + composite total on a 0–100 scale.
    """
    team = _score_team(features)
    market = _score_market(features)
    funding = _score_funding(features)

    # Weighted composite: tweak weights as you like
    total = 0.4 * team + 0.3 * market + 0.3 * funding

    return ScoreBreakdown(
        team=round(team, 2),
        market=round(market, 2),
        funding=round(funding, 2),
        total=round(total, 2),
    )


# -------------------------------------------------------------------
# Team score: founder / operator quality
def _score_team(fv: FeatureVector) -> float:
    """Score founder/operator quality from EMPLOYEE HIGHLIGHTS."""

    weights = {
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
    }

    score = 0.0

    if fv.top_university:
        score += weights["top_university"]
    if fv.seasoned_operator:
        score += weights["seasoned_operator"]
    if fv.seasoned_executive:
        score += weights["seasoned_executive"]
    if fv.prior_vc_backed_founder:
        score += weights["prior_vc_backed_founder"]
    if fv.prior_vc_backed_executive:
        score += weights["prior_vc_backed_executive"]
    if fv.prior_exit:
        score += weights["prior_exit"]
    if fv.twenty_m_club:
        score += weights["twenty_m_club"]
    if fv.seasoned_adviser:
        score += weights["seasoned_adviser"]
    if fv.elite_industry_experience:
        score += weights["elite_industry_experience"]
    if fv.deep_technical_background:
        score += weights["deep_technical_background"]
    if fv.five_m_club:
        score += weights["five_m_club"]

    # Cap at 100
    return min(score, 100.0)
# -------------------------------------------------------------------


# -------------------------------------------------------------------
# Market score: sector fit / location
def _score_market(fv: FeatureVector) -> float:
    """
    Very simple v1:
    - reward having any market_verticals
    - small bonus if clearly AI-related
    - we could later refine by geography, vertical quality, etc.
    """
    score = 0.0

    num_verticals = len(fv.market_verticals or [])

    if num_verticals == 0:
        base = 10.0  # almost no sector signal
    elif num_verticals == 1:
        base = 70.0
    elif num_verticals == 2:
        base = 80.0
    else:
        base = 85.0

    score += base

    # AI bonus if any vertical clearly mentions AI / ML
    ai_keywords = ("ai", "artificial intelligence", "machine learning")
    vertical_text = " ".join(v.lower() for v in fv.market_verticals or [])

    if any(k in vertical_text for k in ai_keywords):
        score += 10.0

    # Cap at 100
    return min(score, 100.0)
# -------------------------------------------------------------------



# -------------------------------------------------------------------
# Funding score: stage + total raised

def _score_funding(fv: FeatureVector) -> float:
    """
    Simple mapping from stage + amount to a 0–100 score.
    """

    stage_key = (fv.stage or "").upper().replace(" ", "_")

    stage_base = {
        "PRE_SEED": 30.0,
        "SEED": 50.0,
        "SERIES_A": 70.0,
        "SERIES_B": 80.0,
        "SERIES_C": 90.0,
    }.get(stage_key, 20.0 if fv.stage else 10.0)  # unknown/none stage

    amount = fv.funding_total or 0.0

    # Very rough bonuses based on amount raised
    bonus = 0.0
    if amount >= 20_000_000:
        bonus = 25.0
    elif amount >= 5_000_000:
        bonus = 15.0
    elif amount >= 1_000_000:
        bonus = 5.0

    score = stage_base + bonus

    return min(score, 100.0)
# -------------------------------------------------------------------