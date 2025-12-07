# loops through all companies, enriches them, scores them, and prints/writes outputs
from __future__ import annotations

import json
from pathlib import Path

from src.merlin.models import (
    RawCompany,
    HarmonicEnrichment,
    EmployeeHighlight,
    ScoredCompanyRecord,
)
from src.merlin.calculate_score import process_company


# ---------------------------------------------------------
# Loading helpers

def load_rows(filename: str):
    """
    Load all rows from harmonic_mapped.json.

    Expected structure:
    [
      {
        "raw_company": {...},
        "harmonic_enrichment": {...}
      },
      ...
    ]
    """
    path = Path(filename)
    data = json.loads(path.read_text())
    if not isinstance(data, list):
        raise ValueError("Expected a list of rows in harmonic_mapped.json")
    return data


def make_raw_company(raw_dict: dict) -> RawCompany:
    return RawCompany(
        name=raw_dict["name"],
        domain=raw_dict.get("domain", ""),
        description=raw_dict.get("description", "") or "",
        stage=raw_dict.get("stage", "") or "",
        industry=raw_dict.get("industry", "") or "",
    )


def make_harmonic_enrichment(he: dict) -> HarmonicEnrichment:
    highlights = [
        EmployeeHighlight(**h) for h in he.get("employee_highlights", [])
    ]

    return HarmonicEnrichment(
        website_domain=he.get("website_domain"),
        harmonic_id=he.get("harmonic_id"),
        website_url=he.get("website_url"),

        description=he.get("description"),
        name=he.get("name"),
        customer_type=he.get("customer_type"),

        stage=he.get("stage"),
        funding_total=he.get("funding_total"),
        funding_stage=he.get("funding_stage"),
        num_funding_rounds=he.get("num_funding_rounds"),
        last_funding_at=he.get("last_funding_at"),
        investors=he.get("investors"),

        headcount=he.get("headcount"),
        founding_date=he.get("founding_date"),
        founding_date_granularity=he.get("founding_date_granularity"),
        location=he.get("location"),

        tags=he.get("tags"),
        tags_v2=he.get("tags_v2"),
        industries=he.get("industries"),
        market_verticals=he.get("market_verticals"),
        market_sub_verticals=he.get("market_sub_verticals"),
        technology_types=he.get("technology_types"),
        product_types=he.get("product_types"),

        highlight_categories=he.get("highlight_categories"),
        highlight_texts=he.get("highlight_texts"),
        employee_highlights=highlights,

        traction_metrics=he.get("traction_metrics"),
        advisor_headcount=he.get("advisor_headcount"),
        web_traffic=he.get("web_traffic"),
        likelihood_of_backing=he.get("likelihood_of_backing"),

        founders=he.get("founders"),
    )
# ---------------------------------------------------------



# ---------------------------------------------------------
# Main scoring entrypoint

def main() -> None:
    # Assuming you run from project root and file is: outputs/harmonic_mapped.json
    rows = load_rows("outputs/harmonic_mapped.json")

    results: list[ScoredCompanyRecord] = []

    for row in rows:
        raw = make_raw_company(row["raw_company"])
        enrichment = make_harmonic_enrichment(row["harmonic_enrichment"])

        scored = process_company(raw, enrichment)
        results.append(scored)

    # Sort by total score descending
    results.sort(key=lambda r: r.scores.total, reverse=True)

    # Print leaderboard
    print("\n=== Company Leaderboard ===")
    for r in results:
        print(
            f"{r.name:30} "
            f"Total: {r.scores.total:6.2f}  "
            f"(Team: {r.scores.team:6.2f}, Market: {r.scores.market:6.2f}, Funding: {r.scores.funding:6.2f})"
        )


if __name__ == "__main__":
    main()
# ---------------------------------------------------------
