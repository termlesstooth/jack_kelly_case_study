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
