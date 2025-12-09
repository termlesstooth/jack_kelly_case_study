# utility script for examining feature vectors
from __future__ import annotations

import json
from pathlib import Path
from typing import List

from src.merlin.models import (
    RawCompany,
    HarmonicEnrichment,
    ScoredCompanyRecord,
)
from src.merlin.enrichment.harmonic import map_company_to_harmonic_enrichment
from src.merlin.scoring.calculate_score import process_company
from src.merlin.run_from_raw import load_raw_harmonic  # reuse the loader

INPUT_PATH = Path("outputs/harmonic_raw_graphql_final.json")
OUTPUT_PATH = Path("outputs/top_feature_vectors.json")


def build_scored_records() -> List[ScoredCompanyRecord]:
    """Reproduce the exact scoring logic from run_from_raw, but return the list."""
    if not INPUT_PATH.is_file():
        raise SystemExit(
            f"Input file not found: {INPUT_PATH}. "
            "Run your Harmonic fetch step first."
        )

    data = load_raw_harmonic(INPUT_PATH)
    results: list[ScoredCompanyRecord] = []

    for row in data:
        raw_company_dict = row.get("raw_company") or {}
        harmonic_raw = row.get("harmonic_raw")

        # Recreate RawCompany from saved dict
        rc = RawCompany(**raw_company_dict)

        # Same guard as run_from_raw
        if (
            harmonic_raw
            and harmonic_raw.get("companyFound")
            and harmonic_raw.get("company") is not None
        ):
            company_json = harmonic_raw["company"]
            he: HarmonicEnrichment = map_company_to_harmonic_enrichment(company_json)
        else:
            # No enrichment; skip companies without Harmonic data
            continue

        scored = process_company(rc, he)
        results.append(scored)

    return results


def export_top_feature_vectors(top_n: int = 10) -> None:
    records = build_scored_records()

    # Sort by total score descending
    records.sort(key=lambda r: r.scores.total, reverse=True)
    top = records[:top_n]

    payload = []
    for r in top:
        payload.append(
            {
                "name": r.name,
                "website_url": r.website_url,
                "scores": {
                    "team": r.scores.team,
                    "market": r.scores.market,
                    "funding": r.scores.funding,
                    "total": r.scores.total,
                },
                # features is already a dict in ScoredCompanyRecord
                "feature_vector": r.features,
            }
        )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"\nWrote top {len(top)} feature vectors to {OUTPUT_PATH}\n")
    for rec in payload:
        print(
            f"{rec['name']:30} "
            f"Total: {rec['scores']['total']:6.2f}  "
            f"(Team: {rec['scores']['team']:6.2f}, "
            f"Market: {rec['scores']['market']:6.2f}, "
            f"Funding: {rec['scores']['funding']:6.2f})"
        )


def main() -> None:
    export_top_feature_vectors(top_n=10)


if __name__ == "__main__":
    main()
