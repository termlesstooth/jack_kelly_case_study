# streamlit_app.py
from __future__ import annotations

import json
from pathlib import Path
from typing import List

import pandas as pd
import streamlit as st

from src.merlin.models import (
    RawCompany,
    HarmonicEnrichment,
    CompanyEnrichment,
    ScoredCompanyRecord,
)
from src.merlin.enrichment.harmonic import map_company_to_harmonic_enrichment
from src.merlin.scoring.calculate_score import process_company
from src.merlin.save_to_db import scored_companies_to_df
from src.merlin.scoring.weights import (
    COMPOSITE_WEIGHTS,
    TEAM_WEIGHTS,
    VERTICAL_WEIGHTS,
    SUB_VERTICAL_WEIGHTS,
    AI_VERTICAL_BONUS,
    SMB_ENABLEMENT_BONUS,
    STAGE_BASE_SCORES,
    FUNDING_BONUS_BRACKETS,
    MAX_SCORE,
)

def load_docs():
    doc_path = Path("docs/weight_documentation.md")
    if doc_path.exists():
        return doc_path.read_text(encoding="utf-8")
    return "Documentation not found."

DOCUMENTATION_TEXT = load_docs()



def load_raw_harmonic(path: Path) -> List[dict]:
    """Local copy of your JSON loader to avoid importing run_from_raw."""
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


# mirror src.merlin.run_from_raw
def run_pipeline_to_df(path: Path) -> pd.DataFrame:
    """
    Mirror src/merlin/run_from_raw.main, but:
    - no Slack
    - no DB writes
    - returns a leaderboard DataFrame
    """
    if not path.is_file():
        raise FileNotFoundError(
            f"Input file not found: {path}. "
            "Run your Harmonic fetch step first to create harmonic_raw_graphql.json."
        )

    data = load_raw_harmonic(path)

    results: list[ScoredCompanyRecord] = []

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
        else:
            # No enrichment; skip companies without Harmonic data
            continue

        scored = process_company(rc, he)
        results.append(scored)

    # Sort by total descending (same as in main)
    results.sort(key=lambda r: r.scores.total, reverse=True)

    # Use our existing helper to get a DataFrame
    df = scored_companies_to_df(results)
    return df


# Streamlit UI
def main():
    st.set_page_config(page_title="Merlin Venture Scoring", layout="wide")

    st.title("Project Merlin")
    st.caption("Designed and Developed by Jack Kelly")
    st.caption("Runs the same pipeline as run_from_raw.py and displays scoring weights.")

    # sidebar: input file + run button
    st.sidebar.header("Input")
    default_path = Path("outputs/harmonic_raw_graphql.json")

    path_str = st.sidebar.text_input(
        "Path to harmonic_raw_graphql.json",
        value=str(default_path),
        help="Relative to repo root",
    )
    run_btn = st.sidebar.button("Run scoring")

    # main
    # weights first
    st.header("Scoring Weights")
    st.write("These are the weights used to compute a company's score.")

    tab_comp, tab_team, tab_market, tab_funding = st.tabs(
        ["Composite", "Team", "Market", "Funding"]
    )

    # Composite weights (dataclass -> dict)
    with tab_comp:
        st.write(
        """
        A company's **total score** is calculated as:

        ```
        total_score = (team_score * team_weight)
                    + (market_score * market_weight)
                    + (funding_score * funding_weight)
        ```

        Where each score is scaled 0–100 before weighting.
        """
        )
        composite = {
            "team": getattr(COMPOSITE_WEIGHTS, "team", None),
            "market": getattr(COMPOSITE_WEIGHTS, "market", None),
            "funding": getattr(COMPOSITE_WEIGHTS, "funding", None),
        }
        st.write("**Composite weights (how team / market / funding are combined):**")
        st.json(composite)


    # Team weights
    with tab_team:
        st.write("**Team feature weights (from employee highlights):**")
        st.dataframe(
            pd.DataFrame(
                [{"feature": k, "weight": v} for k, v in TEAM_WEIGHTS.items()]
            ).sort_values("weight", ascending=False),
            use_container_width=True,
        )

    # Market weights + bonuses
    with tab_market:
        st.write("**Market vertical weights:**")
        st.dataframe(
            pd.DataFrame(
                [{"vertical": k, "weight": v} for k, v in VERTICAL_WEIGHTS.items()]
            ).sort_values("weight", ascending=False),
            use_container_width=True,
        )

        st.write("**Market sub-vertical weights:**")
        st.dataframe(
            pd.DataFrame(
                [{"sub_vertical": k, "weight": v} for k, v in SUB_VERTICAL_WEIGHTS.items()]
            ).sort_values("weight", ascending=False),
            use_container_width=True,
        )

        st.markdown(
            f"- **AI vertical bonus:** `{AI_VERTICAL_BONUS}`\n"
            f"- **SMB enablement bonus:** `{SMB_ENABLEMENT_BONUS}`"
        )

    # Funding weights / brackets
    with tab_funding:
        st.write("**Stage base scores:**")
        st.dataframe(
            pd.DataFrame(
                [{"stage": k, "base_score": v} for k, v in STAGE_BASE_SCORES.items()]
            ).sort_values("base_score", ascending=False),
            use_container_width=True,
        )

        st.write("**Funding bonus brackets (amount ≤ upper_bound → bonus):**")
        fb_df = pd.DataFrame(
            [
                {"upper_bound": ub, "bonus": bonus}
                for (ub, bonus) in FUNDING_BONUS_BRACKETS
            ]
        )
        st.dataframe(fb_df, use_container_width=True)

        st.markdown(f"- **Max score cap:** `{MAX_SCORE}`")

    st.markdown("---")

    # run the pipeline and show leaderboard
    if run_btn:
        path = Path(path_str)
        try:
            df = run_pipeline_to_df(path)
        except FileNotFoundError as e:
            st.error(str(e))
            return

        st.subheader("Company leaderboard (from scored_companies_to_df)")
        # Just show whatever columns our helper produces (name, scores, stage, location, description, etc.)
        numeric_cols = [c for c in df.columns if c in {"team", "market", "funding", "total"}]
        st.dataframe(
            df.style.format({col: "{:.2f}" for col in numeric_cols}),
            use_container_width=True,
        )

        if "name" in df.columns and "total" in df.columns:
            st.markdown("**Top 5 companies:**")
            top_cols = [c for c in ["name", "total", "team", "market", "funding", "stage", "location"] if c in df.columns]
            st.table(df.sort_values("total", ascending=False).head(5)[top_cols])
    
    with st.expander("📘 Scoring Weight Documentation"):
        st.markdown(DOCUMENTATION_TEXT)



if __name__ == "__main__":
    main()
