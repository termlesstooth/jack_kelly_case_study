# feature debugging script
import json
from pathlib import Path

from src.merlin.models import RawCompany, HarmonicEnrichment, EmployeeHighlight, FeatureVector
from src.merlin.features import build_features


def load_rows(filename: str):
    path = Path(filename)
    print("Loading:", path.resolve())
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


def main() -> None:
    rows = load_rows("outputs/harmonic_mapped.json")

    for i, row in enumerate(rows, start=1):
        raw = make_raw_company(row["raw_company"])
        enrichment = make_harmonic_enrichment(row["harmonic_enrichment"])

        fv: FeatureVector = build_features(raw, enrichment)

        print("=" * 80)
        print(f"[{i}] {raw.name} ({raw.stage}, {raw.industry})")
        print("FeatureVector:", fv)



if __name__ == "__main__":
    main()
