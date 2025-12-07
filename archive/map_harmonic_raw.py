# legacy script
# takes raw harmonic graphQL output and maps to our Python objects
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import List, Tuple

from src.merlin.models import RawCompany, HarmonicEnrichment, CompanyEnrichment
from src.merlin.enrichment.harmonic import map_company_to_harmonic_enrichment


def load_raw_harmonic(path: Path) -> List[dict]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    in_path = Path("outputs/harmonic_raw_graphql.json")
    if not in_path.is_file():
        raise SystemExit(f"Input file not found: {in_path}. Run fetch_harmonic_raw first.")

    data = load_raw_harmonic(in_path)

    out_path = Path("outputs/harmonic_mapped.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    records = []

    for row in data:
        raw_company_dict = row.get("raw_company") or {}
        harmonic_raw = row.get("harmonic_raw")

        rc = RawCompany(**raw_company_dict)

        if (
            harmonic_raw
            and harmonic_raw.get("companyFound")
            and harmonic_raw.get("company") is not None
        ):
            company_json = harmonic_raw["company"]
            he: HarmonicEnrichment = map_company_to_harmonic_enrichment(company_json)
            ce = CompanyEnrichment(harmonic=he)
        else:
            ce = CompanyEnrichment(harmonic=None)

        records.append(
            {
                "raw_company": asdict(rc),
                "harmonic_enrichment": (
                    asdict(ce.harmonic) if ce.harmonic else None
                ),
            }
        )

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)

    print(f"Wrote {len(records)} mapped companies to {out_path}")


if __name__ == "__main__":
    main()
