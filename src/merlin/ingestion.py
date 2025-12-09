# csv -> raw company loading + dedupe
from dataclasses import dataclass
from typing import List, Any
import pandas as pd

from src.merlin.models import RawCompany


def _safe_str(value: Any) -> str:
    """Convert NaN/None to empty string, everything else to str."""
    if pd.isna(value):
        return ""
    return str(value)


def load_companies_from_csv(path: str) -> list[RawCompany]:
    """
    Load the case study CSV, clean header artifacts, remove duplicates,
    and return a list of RawCompany objects.
    """

    df = pd.read_csv(path, skiprows=2).iloc[:, 1:]

    # Drop fully empty rows
    df = df.dropna(how="all")

    # Require URL (drops section headers like “B2B SaaS”)
    df = df.dropna(subset=["URL"])

    # Remove rows where URL == "URL" (repeated header rows)
    df = df[df["URL"].str.strip().str.upper() != "URL"]

    # Remove duplicate URLs 
    df = df.drop_duplicates(subset=["URL"], keep="first")

    # Build RawCompany objects
    companies: list[RawCompany] = []
    for _, row in df.iterrows():
        companies.append(
            RawCompany(
                name=_safe_str(row.get("Name")),
                description=_safe_str(row.get("Description")),
                domain=_safe_str(row.get("URL")),
                industry=_safe_str(row.get("Industry")),
                stage=_safe_str(row.get("Stage")),
            )
        )

    return companies

if __name__ == "__main__":
    companies = load_companies_from_csv("data/case_study_data.csv")
    print("Total companies loaded:", len(companies))

    for c in companies[:5]:
        print(c)
