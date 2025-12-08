# run pipeline from raw sqlgraph output to final. This avoids having to requery Harmonic API 
from __future__ import annotations

import json
from pathlib import Path
from typing import List

from src.merlin.models import (
    RawCompany,
    HarmonicEnrichment,
    CompanyEnrichment,
    ScoredCompanyRecord,
)
from src.merlin.enrichment.harmonic import map_company_to_harmonic_enrichment
from src.merlin.scoring.calculate_score import process_company
from src.merlin.save_to_db import scored_companies_to_df, save_scores_to_db
from src.merlin.notify import send_results_to_slack
from dotenv import load_dotenv

load_dotenv()


def load_raw_harmonic(path: Path) -> List[dict]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    in_path = Path("outputs/harmonic_raw_graphql.json")
    if not in_path.is_file():
        raise SystemExit(
            f"Input file not found: {in_path}. "
            "Run your Harmonic fetch step first to create harmonic_raw_graphql.json."
        )

    data = load_raw_harmonic(in_path)

    results: list[ScoredCompanyRecord] = []

    for row in data:
        raw_company_dict = row.get("raw_company") or {}
        harmonic_raw = row.get("harmonic_raw")

        # Recreate RawCompany from saved dict
        rc = RawCompany(**raw_company_dict)

        # If Harmonic found a company, map it to HarmonicEnrichment
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
    
    print("DEBUG LOCATION:", scored.location)

    # Sort by total score descending
    results.sort(key=lambda r: r.scores.total, reverse=True)

    leaderboard_lines = []
    leaderboard_lines.append("\n=== Company Leaderboard (from harmonic_raw_graphql.json) ===")

    for r in results:
        line = (
            f"{r.name:30} "
            f"Total: {r.scores.total:6.2f}  "
            f"(Team: {r.scores.team:6.2f}, Market: {r.scores.market:6.2f}, Funding: {r.scores.funding:6.2f})"
        )
        leaderboard_lines.append(line)

    leaderboard_text = "\n".join(leaderboard_lines)

    print(leaderboard_text)  # still print locally
    print("DESCRIPTION DEBUG:",results[0].description)
    send_results_to_slack(results)

    # --- NEW: save to SQLite ---
    df = scored_companies_to_df(results)
    save_scores_to_db(df)  # default path: data/merlin_scores.db, table: companies
    print("\nSaved scores to data/merlin_scores.db (table: companies)")

    # If you don't care about harmonic_mapped.json anymore,
    # you can delete everything below this comment.
    # Otherwise you can flesh it out later.


if __name__ == "__main__":
    main()
