# Fetches raw GraphQL per company
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from src.merlin.ingestion import load_companies_from_csv
from src.merlin.enrichment.harmonic_graphql_client import HarmonicGraphQLClient


def main() -> None:
    csv_path = Path("data/case_study_data.csv")
    raw_companies = load_companies_from_csv(str(csv_path))

    # test only a few
    raw_companies = raw_companies[:3]

    client = HarmonicGraphQLClient()

    out_path = Path("outputs/harmonic_raw_graphql.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    records = []
    for rc in raw_companies:
        domain = rc.domain.strip()
        print(rc)

        try:
            payload = client.enrich_company_by_domain(domain)
        except Exception as e:
            print(f"Error enriching {domain}: {e}")
            payload = None

        records.append(
            {
                "raw_company": asdict(rc),
                "harmonic_raw": payload,  # <-- raw GraphQL response for that company
            }
        )

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)

    print(f"Wrote {len(records)} raw responses to {out_path}")


if __name__ == "__main__":
    main()
