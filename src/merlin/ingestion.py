# csv -> raw company loading + dedupe
from dataclasses import dataclass
from typing import List, Any
from src.merlin.models import RawCompany

import pandas as pd


def _safe_str(value: Any) -> str:
    """Convert NaN/None to empty string, everything else to str."""
    if pd.isna(value):
        return ""
    return str(value)


def load_companies_from_csv(path: str) -> list[RawCompany]:
    df = pd.read_csv(path,skiprows=2).iloc[:, 1:] # TODO: Think about normalzing here so we can feed in different CSVs
    df = df.dropna(how="all")
    companies = []
    for _, row in df.iterrows():
        companies.append(
            RawCompany(
                name=_safe_str(row["Name"]),
                description = _safe_str(row["Description"]),
                domain = _safe_str(row["URL"]), # called url in sample data, really is domain
                industry=_safe_str(row["Industry"]),
                stage = _safe_str(row["Stage"])
            )
        )
    return companies


raw_companies = load_companies_from_csv("data/case_study_data.csv")
print(len(raw_companies))
print(raw_companies[0])