# scoring logic
from __future__ import annotations
from typing import Optional
import re

from src.merlin.models import FeatureVector, ScoreBreakdown
from src.merlin.scoring.weights import (
    COMPOSITE_WEIGHTS,
    TEAM_WEIGHTS,
    VERTICAL_WEIGHTS,
    SUB_VERTICAL_WEIGHTS,
    SMB_ENABLEMENT_BONUS,
    STAGE_BASE_SCORES,
    FUNDING_BONUS_BRACKETS,
    MAX_SCORE,
    HEADCOUNT_BONUS
)

# TODO: Future improvement: Use an algorithm more advanced than a linear combination.
def score_company(features: FeatureVector) -> ScoreBreakdown:
    """
    Linear Combination scoring entrypoint.
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


def _score_team(fv: FeatureVector) -> float:
    """
    Team score.

    All founder/employee highlight signals are pre-encoded as booleans
    on the FeatureVector in build_features. Here we just:
      - sum weights for any True flags in TEAM_WEIGHTS
      - add a headcount bonus
      - clamp to MAX_SCORE
    """
    score = 0.0

    # founder signals
    for attr, weight in TEAM_WEIGHTS.items():
        if attr == "headcount_bonus":
            continue

        if getattr(fv, attr, False):
            score += weight

    # headcount bonus
    hc = fv.headcount or 0
    if hc > 2:
        score += HEADCOUNT_BONUS["over_two"]
    if hc >= 6:
        score += HEADCOUNT_BONUS["over_or_equal_to_6"]
    if hc >= 10:
        score += HEADCOUNT_BONUS["over_or_equal_to_10"]

    return min(score, MAX_SCORE)




# geo helpers
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

    # Direct US/Canada keywords
    if any(k in loc for k in US_COUNTRY_KEYWORDS):
        return True
    if "canada" in loc:
        return True

    # Two letter US state codes in the string
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


def _score_market(fv: FeatureVector) -> float:
    """
    Market score:
    - 0 if company is not in US/Canada.
    - Otherwise:
        - Use only the strongest market_vertical
        - Use only the strongest market_sub_vertical
        - Add SMB enablement bonus
        - Cap at 0–100
    """
    if not _is_north_america(fv.location):
        return 0.0

    # strongest vertical
    # NOTE: Had an issue where companies with a bunch of sub-verticals had strong market scores. My assumption is that Core wouldn't prefer by 2x a company with 2 familiar sub verticals vs just 1. 
    # Future improvement: Use an LLM to classify most relevant vertical + sub vertical
    vertical_scores = [
        VERTICAL_WEIGHTS.get(v, 0.0)
        for v in (fv.market_verticals or [])
    ]
    best_vertical = max(vertical_scores) if vertical_scores else 0.0

    # strongest sub-vertical
    sub_scores = [
        SUB_VERTICAL_WEIGHTS.get(sv, 0.0)
        for sv in (fv.market_sub_verticals or [])
    ]
    best_sub_vertical = max(sub_scores) if sub_scores else 0.0

    # SMB enablement bonus
    smb_bonus = (
        SMB_ENABLEMENT_BONUS
        if _is_smb_enabled(getattr(fv, "description", None))
        else 0.0
    )

    score = best_vertical + best_sub_vertical + smb_bonus

    return max(0.0, min(score, MAX_SCORE))

def _score_funding(fv: FeatureVector) -> float:
    """
    Funding score aligned with Core's increased outbound goal.
    Arjan explained while we don't want to be funding pre seed, we want to be reaching out earlier.
    Higher score for earlier stages and smaller total funding.
    """
    # normalize stage
    stage_key = (fv.stage or "").upper().replace(" ", "_")
    stage_base = STAGE_BASE_SCORES.get(stage_key, 0.0)

    # funding amount bonus (smaller = better)
    amount = fv.funding_total or 0.0
    bonus = 0.0
    for upper_bound, bracket_bonus in FUNDING_BONUS_BRACKETS:
        if amount <= upper_bound:
            bonus = bracket_bonus
            break

    score = stage_base + bonus
    return min(score, MAX_SCORE)