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

    

    client = HarmonicGraphQLClient()

    out_path = Path("outputs/harmonic_raw_graphql_final.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    records = []
    missing_domains = []       
    failed_queries = []    

    for rc in raw_companies:
        domain = rc.domain.strip().lower()

        print(f"\n🔍 Querying Harmonic for: {domain}")

        if not domain:
            print("⚠️ Skipping — empty domain.")
            missing_domains.append((rc.name, rc.domain))
            continue

        try:
            payload = client.enrich_company_by_domain(domain)

            # Harmonic returns "None" if domain not found — we treat that explicitly
            if payload is None:
                print(f"Not found in Harmonic: {domain}")
                missing_domains.append((rc.name, rc.domain))

        except Exception as e:
            print(f"Error enriching {domain}: {e}")
            failed_queries.append((rc.name, rc.domain, str(e)))
            payload = None

        records.append(
            {
                "raw_company": asdict(rc),
                "harmonic_raw": payload,
            }
        )

    # Save all results
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)

    # Summary logs
    print("\n=========================================")
    print(f"Finished querying {len(raw_companies)} companies")
    print(f"Wrote {len(records)} raw responses to {out_path}")

    print("\nMissing from Harmonic:", len(missing_domains))
    for name, domain in missing_domains:
        print(f"  - {name} ({domain})")

    print("\nFailed API calls:", len(failed_queries))
    for name, domain, err in failed_queries:
        print(f"  - {domain}: {err}")


if __name__ == "__main__":
    main()
