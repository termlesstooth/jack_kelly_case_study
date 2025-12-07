# src/merlin/scoring/scoring.py
from __future__ import annotations

import re
from typing import Optional

from src.merlin.models import FeatureVector, ScoreBreakdown
from src.merlin.scoring.weights import (
    COMPOSITE_WEIGHTS,
    TEAM_WEIGHTS,
    VERTICAL_WEIGHTS,
    SUB_VERTICAL_WEIGHTS,
    AI_VERTICAL_BONUS,
    SMB_ENABLEMENT_BONUS,
    STAGE_BASE_SCORES,
    FUNDING_BONUS_BRACKETS,
    MAX_SCORE,
)


def score_company(features: FeatureVector) -> ScoreBreakdown:
    """
    High-level scoring entrypoint.
    Returns per-criterion scores + composite total on a 0–100 scale.
    """
    team = _score_team(features)
    market = _score_market(features)
    funding = _score_funding(features)

    total = (
        COMPOSITE_WEIGHTS.team * team
        + COMPOSITE_WEIGHTS.market * market
        + COMPOSITE_WEIGHTS.funding * funding
    )

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
    score = 0.0

    if fv.top_university:
        score += TEAM_WEIGHTS["top_university"]
    if fv.seasoned_operator:
        score += TEAM_WEIGHTS["seasoned_operator"]
    if fv.seasoned_executive:
        score += TEAM_WEIGHTS["seasoned_executive"]
    if fv.prior_vc_backed_founder:
        score += TEAM_WEIGHTS["prior_vc_backed_founder"]
    if fv.prior_vc_backed_executive:
        score += TEAM_WEIGHTS["prior_vc_backed_executive"]
    if fv.prior_exit:
        score += TEAM_WEIGHTS["prior_exit"]
    if fv.twenty_m_club:
        score += TEAM_WEIGHTS["twenty_m_club"]
    if fv.seasoned_adviser:
        score += TEAM_WEIGHTS["seasoned_adviser"]
    if fv.elite_industry_experience:
        score += TEAM_WEIGHTS["elite_industry_experience"]
    if fv.deep_technical_background:
        score += TEAM_WEIGHTS["deep_technical_background"]
    if fv.five_m_club:
        score += TEAM_WEIGHTS["five_m_club"]

    return min(score, MAX_SCORE)


# -------------------------------------------------------------------
# Geo helpers

US_COUNTRY_KEYWORDS = [
    "united states",
    "united states of america",
    "usa",
    "us",
    "u.s.",
]

US_STATE_CODES = {
    "al","ak","az","ar","ca","co","ct","de","fl","ga","hi","id","il","in","ia","ks",
    "ky","la","me","md","ma","mi","mn","ms","mo","mt","ne","nv","nh","nj","nm","ny",
    "nc","nd","oh","ok","or","pa","ri","sc","sd","tn","tx","ut","vt","va","wa","wv",
    "wi","wy",
}


def _is_north_america(location: Optional[str]) -> bool:
    """Return True if location string looks like US or Canada."""
    if not location:
        return False

    loc = location.lower()

    # 1) Direct US/Canada keywords
    if any(k in loc for k in US_COUNTRY_KEYWORDS):
        return True
    if "canada" in loc:
        return True

    # 2) Two-letter U.S. state codes in the string
    state_matches = re.findall(r"\b([a-z]{2})\b", loc)
    return any(code in US_STATE_CODES for code in state_matches)


def _is_smb_enabled(description: Optional[str]) -> bool:
    """
    Heuristic: returns True if the description suggests SMB enablement.
    - Matches 'SMB' (case-insensitive)
    - Or both 'small' and 'business' anywhere in the text
    """
    if not description:
        return False

    text = description.lower()
    if "smb" in text:
        return True

    return "small" in text and "business" in text


# -------------------------------------------------------------------
# Market score: sector fit / location

def _score_market(fv: FeatureVector) -> float:
    """
    Market score:

    - 0 if company is not in US/Canada.
    - Otherwise:
        - Sum weights for each market_vertical
        - Sum weights for each market_sub_vertical
        - Add AI bonus if applicable
        - Add SMB enablement bonus
        - Cap at 0–100
    """
    if not _is_north_america(fv.location):
        return 0.0

    score = 0.0

    # Add vertical weights
    for v in fv.market_verticals or []:
        score += VERTICAL_WEIGHTS.get(v, 0.0)

    # Add sub-vertical weights
    for sv in fv.market_sub_verticals or []:
        score += SUB_VERTICAL_WEIGHTS.get(sv, 0.0)

    # AI bonus if any vertical clearly mentions AI / ML
    ai_keywords = ("ai", "artificial intelligence", "machine learning")
    vertical_text = " ".join(v.lower() for v in (fv.market_verticals or []))
    if any(k in vertical_text for k in ai_keywords):
        score += AI_VERTICAL_BONUS

    # SMB enablement bonus (based on description)
    if _is_smb_enabled(getattr(fv, "description", None)):
        score += SMB_ENABLEMENT_BONUS

    return max(0.0, min(score, MAX_SCORE))


# -------------------------------------------------------------------
# Funding score: stage + total raised

def _score_funding(fv: FeatureVector) -> float:
    """
    Funding score aligned with 'early-stage identification' thesis.
    Higher score for earlier stages and smaller total funding.
    """
    # Normalize stage
    stage_key = (fv.stage or "").upper().replace(" ", "_")
    stage_base = STAGE_BASE_SCORES.get(stage_key, 0.0)

    # Funding amount bonus (smaller = better)
    amount = fv.funding_total or 0.0
    bonus = 0.0
    for upper_bound, bracket_bonus in FUNDING_BONUS_BRACKETS:
        if amount <= upper_bound:
            bonus = bracket_bonus
            break

    score = stage_base + bonus
    return min(score, MAX_SCORE)
