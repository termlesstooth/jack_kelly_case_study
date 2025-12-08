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
        enrich = r.harmonic

        rows.append(
            {
                "name": r.name,
                "website_url": r.website_url,
                "website_domain": r.website_domain,
                "description": r.description,
                "sectors": ", ".join(r.sectors or []),
                "sub_sectors": ", ".join(r.sub_sectors or []),
                "location": r.location,
                "stage": r.stage,
                "funding_total": r.funding_total,
                "founders": ", ".join(str(f) for f in (r.founders or [])),


                # scores + breakdown
                "score_total": scores.total,
                "score_breakdown": json.dumps(scores.__dict__),

                # full feature vector for debugging
                "features": json.dumps(r.features),

                # harmonic enrichment fields
                "headcount": enrich.headcount if enrich else None,
                "funding_stage": enrich.funding_stage if enrich else None,
                "num_funding_rounds": enrich.num_funding_rounds if enrich else None,
                "last_funding_at": enrich.last_funding_at if enrich else None,
                "investors": json.dumps(enrich.investors or []) if enrich else "[]",
                "tags": json.dumps(enrich.tags or []) if enrich else "[]",
                "market_verticals": json.dumps(enrich.market_verticals or []) if enrich else "[]",
                "market_sub_verticals": json.dumps(enrich.market_sub_verticals or []) if enrich else "[]",
                "employee_highlights": json.dumps(
                    [eh.__dict__ for eh in (enrich.employee_highlights or [])]
                ) if enrich else "[]",

                # Scores
                "score_total": scores.total,
                "score_breakdown": json.dumps(scores.__dict__),

                # Full feature vector for debugging
                "features": json.dumps(r.features),
            }
        )

    return pd.DataFrame(rows)


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
