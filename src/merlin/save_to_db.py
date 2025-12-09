# script to save to sqlite database
from typing import List
import sqlite3
import json

import pandas as pd

from src.merlin.models import ScoredCompanyRecord, ScoreBreakdown


def scored_companies_to_df(records: List[ScoredCompanyRecord]) -> pd.DataFrame:
    rows = []

    for r in records:
        scores: ScoreBreakdown = r.scores
        enrich = r.harmonic  # may be None

        # --- founders ---
        founders = r.founders or []
        founder_names = [f.name for f in founders if getattr(f, "name", None)]
        founder_linkedins = [
            f.linkedin_url for f in founders if getattr(f, "linkedin_url", None)
        ]

        # flatten founder emails into a single list
        all_emails: list[str] = []
        for f in founders:
            emails = getattr(f, "emails", None)
            if emails:
                all_emails.extend(emails)

        row = {
            # --- primary company info (requested order) ---
            "company_name": r.name,
            "website_url": r.website_url,
            "sectors": ", ".join(r.sectors or []),
            "location": r.location,
            "funding_total": r.funding_total,

            # from Harmonic
            "customer_type": enrich.customer_type if enrich else None,

            # --- founders (all as JSON lists) ---
            "founder_name": json.dumps(founder_names),
            "founder_linkedin": json.dumps(founder_linkedins),
            "founder_email": json.dumps(all_emails),

            # --- individual criteria scores + total ---
            "score_team": scores.team,
            "score_market": scores.market,
            "score_funding": scores.funding,
            "score_total": scores.total,

            # --- Harmonic enrichment fields ---
            "harmonic_id": enrich.harmonic_id if enrich else None,
            "website_domain": enrich.website_domain if enrich else r.website_domain,
            "harmonic_website_url": enrich.website_url if enrich else None,

            "harmonic_stage": enrich.stage if enrich else None,
            "harmonic_funding_total": enrich.funding_total if enrich else None,
            "harmonic_num_funding_rounds": enrich.num_funding_rounds if enrich else None,
            "harmonic_last_funding_at": enrich.last_funding_at if enrich else None,
            "harmonic_investors": json.dumps(enrich.investors or []) if enrich else "[]",

            "harmonic_headcount": enrich.headcount if enrich else None,
            "founding_date": enrich.founding_date if enrich else None,
            "founding_date_granularity": (
                enrich.founding_date_granularity if enrich else None
            ),
            "location_raw": json.dumps(enrich.location) if (enrich and enrich.location) else None,

            "tags": json.dumps(enrich.tags or []) if enrich else "[]",
            "tags_v2": json.dumps(enrich.tags_v2 or []) if enrich else "[]",
            "industries": json.dumps(enrich.industries or []) if enrich else "[]",
            "market_verticals": json.dumps(enrich.market_verticals or []) if enrich else "[]",
            "market_sub_verticals": json.dumps(enrich.market_sub_verticals or []) if enrich else "[]",
            "technology_types": json.dumps(enrich.technology_types or []) if enrich else "[]",
            "product_types": json.dumps(enrich.product_types or []) if enrich else "[]",

            "highlight_categories": json.dumps(enrich.highlight_categories or []) if enrich else "[]",
            "highlight_texts": json.dumps(enrich.highlight_texts or []) if enrich else "[]",
            "founder_highlights": json.dumps(
                [eh.__dict__ for eh in (enrich.employee_highlights or [])]
            ) if enrich else "[]",

            "traction_metrics": json.dumps(enrich.traction_metrics or {}) if enrich else "{}",
            "advisor_headcount": enrich.advisor_headcount if enrich else None,
            "web_traffic": json.dumps(enrich.web_traffic or {}) if enrich else "{}",
            "likelihood_of_backing": enrich.likelihood_of_backing if enrich else None,

            # --- everything else (non-Harmonic, for debugging) ---
            "description": r.description,
            "sub_sectors": ", ".join(r.sub_sectors or []),
            "features": json.dumps(r.features),
        }

        rows.append(row)

    df = pd.DataFrame(rows)

    core_cols = [
        "company_name",
        "website_url",
        "sectors",
        "location",
        "funding_total",
        "customer_type",
        "founder_name",
        "founder_linkedin",
        "founder_email",
        "score_team",
        "score_market",
        "score_funding",
        "score_total",
    ]

    harmonic_cols = [
        "harmonic_id",
        "website_domain",
        "harmonic_website_url",
        "harmonic_stage",
        "harmonic_funding_total",
        "harmonic_num_funding_rounds",
        "harmonic_last_funding_at",
        "harmonic_investors",
        "harmonic_headcount",
        "founding_date",
        "founding_date_granularity",
        "location_raw",
        "tags",
        "tags_v2",
        "industries",
        "market_verticals",
        "market_sub_verticals",
        "technology_types",
        "product_types",
        "highlight_categories",
        "highlight_texts",
        "founder_highlights",
        "traction_metrics",
        "advisor_headcount",
        "web_traffic",
        "likelihood_of_backing",
    ]

    ordered_cols = core_cols + harmonic_cols
    other_cols = [c for c in df.columns if c not in ordered_cols]
    df = df[ordered_cols + other_cols]

    return df


def save_scores_to_db(
    df: pd.DataFrame,
    db_path: str = "data/merlin_scores.db",
    table_name: str = "companies",
) -> None:
    conn = sqlite3.connect(db_path)
    try:
        df.to_sql(table_name, conn, if_exists="replace", index=False)
    finally:
        conn.close()
