# simple front end for presentation
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Any

import pandas as pd
import streamlit as st

from dotenv import load_dotenv  # NEW

from src.merlin.models import (
    RawCompany,
    HarmonicEnrichment,
    ScoredCompanyRecord,
)
from src.merlin.enrichment.harmonic import map_company_to_harmonic_enrichment
from src.merlin.scoring.calculate_score import process_company
from src.merlin.save_to_db import (
    scored_companies_to_df,
    save_scores_to_db,          # NEW
)
from src.merlin.notify import send_results_to_slack  # NEW
from src.merlin.scoring.weights import (
    COMPOSITE_WEIGHTS,
    TEAM_WEIGHTS,
    VERTICAL_WEIGHTS,
    SUB_VERTICAL_WEIGHTS,
    STAGE_BASE_SCORES,
    FUNDING_BONUS_BRACKETS,
    MAX_SCORE,
)

load_dotenv()


def _extract_weight(v: Any):
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, dict) and "weight" in v:
        try:
            return float(v["weight"])
        except (TypeError, ValueError):
            return None
    return None


def load_raw_harmonic(path: Path) -> List[dict]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def run_pipeline(path: Path) -> tuple[list[ScoredCompanyRecord], pd.DataFrame]:
    if not path.is_file():
        raise FileNotFoundError(
            f"Input file not found: {path}. "
            "Run your Harmonic fetch step first to create harmonic_raw_graphql_final.json."
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
            continue

        scored = process_company(rc, he)
        results.append(scored)

    results.sort(key=lambda r: r.scores.total, reverse=True)
    df = scored_companies_to_df(results)
    return results, df


def main():
    st.set_page_config(
        page_title="Merlin Venture Scoring",
        page_icon="🧙‍♂️",
        layout="wide",
    )

    # --- CSS ---
    st.markdown(
        """
        <style>
        .stApp {
            background: radial-gradient(circle at top, #020617 0, #020617 40%, #000000 100%);
            color: #e5e7eb;
        }
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
        }
        h1, h2, h3 {
            color: #e5e7eb !important;
        }
        .merlin-card {
            background: rgba(15,23,42,0.9);
            border-radius: 0.75rem;
            padding: 1.25rem 1.5rem;
            border: 1px solid rgba(148,163,184,0.35);
        }
        .merlin-pill {
            display: inline-block;
            padding: 0.2rem 0.6rem;
            border-radius: 999px;
            background: rgba(37,99,235,0.18);
            color: #bfdbfe;
            font-size: 0.75rem;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # --- Hero Section ---
    st.markdown(
        """
        <div style="display:flex;align-items:center;gap:1rem;margin-bottom:0.75rem;">
          <div style="font-size:2.8rem;">🧙‍♂️</div>
          <div>
            <h1 style="margin-bottom:0.1rem;">Project Merlin</h1>
            <p style="margin:0;color:#9ca3af;">
              Designed and built by Jack Kelly for Core Innovation Capital.
            </p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- How To Read ---
    st.markdown(
        """
        <div class="merlin-card">
          <span class="merlin-pill">Partner View</span>
          <h3 style="margin-top:0.75rem;margin-bottom:0.35rem;">How to Read this UI</h3>
          <p><b>Merlin Score</b> ranks companies based on Core VC’s investment thesis and founder insight.</p>
          <ul>
            <li><b>Team</b> score → founder track record, YC, prior exits, major tech, domain expertise.</li>
            <li><b>Market</b> score → vertical attractiveness, SMB enablement.</li>
            <li><b>Funding</b> score → stage + total capital raised mapped to score curves.</li>
          </ul>
          <p style="color:#9ca3af;">Click <b>Run Scoring</b> to evaluate the entire dataset.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- Run Scoring ---
    st.header("Run Merlin Scoring")
    path_str = "outputs/harmonic_raw_graphql_final.json"
    run_btn = st.button("🔮 Run Scoring")
    st.markdown("---")

    if run_btn:
        path = Path(path_str)

        try:
            results, df = run_pipeline(path)
        except Exception as e:
            st.error(str(e))
            return

        try:
            send_results_to_slack(results)
            save_scores_to_db(df)
            st.success("Sent results to Slack and saved scores to the database.")
        except Exception as e:
            st.warning(f"Scoring ran, but Slack/DB step had an issue: {e}")

        # --- Build Table Rows ---
        st.subheader("Company Leaderboard")

        table_rows: list[dict[str, Any]] = []
        for r in results:
            founders = r.founders or []
            founder_names = [f.name for f in founders]
            founder_links = [f.linkedin_url for f in founders if f.linkedin_url]
            founder_emails = []
            for f in founders:
                if f.emails:
                    founder_emails.extend(f.emails)

            table_rows.append(
                {
                    "Company Name": r.name,
                    "URL": r.website_url or "",
                    "Description": (r.description or "").strip(),
                    "Founders": ", ".join(founder_names),
                    "Founder LinkedIn": ", ".join(founder_links),
                    "Founder Emails": ", ".join(founder_emails),
                    "Total Score": r.scores.total,
                    "Team Score": r.scores.team,
                    "Market Score": r.scores.market,
                    "Funding Score": r.scores.funding,
                }
            )

        slack_df = pd.DataFrame(table_rows)

        st.dataframe(
            slack_df,
            use_container_width=True,
            column_config={
                "URL": st.column_config.LinkColumn("URL"),
                "Total Score": st.column_config.NumberColumn("Total Score", format="%.2f"),
                "Team Score": st.column_config.NumberColumn("Team Score", format="%.2f"),
                "Market Score": st.column_config.NumberColumn("Market Score", format="%.2f"),
                "Funding Score": st.column_config.NumberColumn("Funding Score", format="%.2f"),
            },
        )

        # --- Partner Notes ---
        st.markdown("### Partner Notes")
        st.markdown(
            """
            <div class="merlin-card">
            <ul>
                <li>Scroll right to view the full score breakdown.</li>
                <li>See the Feature Vector section below for underlying attributes.</li>
                <li>Slack notifications contain a skim-friendly summary for partners.</li>
            </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")

        # --- Feature Vector Viewer ---
        with st.expander("🧬 Feature Vector (per company)"):
            feature_rows: list[dict[str, Any]] = []
            for r in results:
                fv = getattr(r, "features", {}) or {}
                row: dict[str, Any] = {"Company Name": r.name}
                if isinstance(fv, dict):
                    row.update(fv)
                else:
                    row["features"] = fv
                feature_rows.append(row)

            feature_df = pd.DataFrame(feature_rows)
            st.dataframe(feature_df, use_container_width=True)

        st.markdown("---")

    # ------------------------------
    # Scoring Weights Section
    # ------------------------------
    st.header("Scoring Weights")
    tab_comp, tab_team, tab_market, tab_funding = st.tabs(
        ["Composite", "Team", "Market", "Funding"]
    )

    with tab_comp:
        st.write(
            """
            ```python
            total_score = (
                team_score * team_weight
              + market_score * market_weight
              + funding_score * funding_weight
            )
            ```
            """
        )
        composite = {
            "team": COMPOSITE_WEIGHTS.team,
            "market": COMPOSITE_WEIGHTS.market,
            "funding": COMPOSITE_WEIGHTS.funding,
        }
        st.json(composite)

    with tab_team:
        rows = [
            {"feature": k, "weight": _extract_weight(v)}
            for k, v in TEAM_WEIGHTS.items()
            if _extract_weight(v) is not None
        ]
        st.dataframe(
            pd.DataFrame(rows).sort_values("weight", ascending=False),
            use_container_width=True,
        )

    with tab_market:
        vert_rows = [
            {"vertical": k, "weight": _extract_weight(v)}
            for k, v in VERTICAL_WEIGHTS.items()
        ]
        st.dataframe(pd.DataFrame(vert_rows).sort_values("weight", ascending=False))

        sub_rows = [
            {"sub_vertical": k, "weight": _extract_weight(v)}
            for k, v in SUB_VERTICAL_WEIGHTS.items()
        ]
        st.dataframe(pd.DataFrame(sub_rows).sort_values("weight", ascending=False))

    with tab_funding:
        st.dataframe(
            pd.DataFrame(
                [{"stage": k, "base_score": v} for k, v in STAGE_BASE_SCORES.items()]
            ),
            use_container_width=True,
        )
        fb_df = pd.DataFrame(
            [{"upper_bound": ub, "bonus": bonus} for (ub, bonus) in FUNDING_BONUS_BRACKETS]
        )
        st.dataframe(fb_df, use_container_width=True)
        st.write(f"**Max Score Cap:** {MAX_SCORE}")


if __name__ == "__main__":
    main()
