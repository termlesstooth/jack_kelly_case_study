# archive script for looking at founder highlights
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Set

INPUT_PATH = Path("outputs/harmonic_raw_graphql_final.json")
OUTPUT_PATH = Path("outputs/employee_highlights.json")


def find_employees(obj: Any) -> List[Dict]:
    """Recursively find the `employees` array in the nested harmonic_raw payload."""
    if isinstance(obj, dict):
        if "employees" in obj and isinstance(obj["employees"], list):
            return obj["employees"]
        for v in obj.values():
            res = find_employees(v)
            if res:
                return res
    elif isinstance(obj, list):
        for item in obj:
            res = find_employees(item)
            if res:
                return res
    return []


def main() -> None:
    with INPUT_PATH.open("r", encoding="utf-8") as f:
        records = json.load(f)

    out: List[Dict] = []
    all_categories: Set[str] = set()
    no_highlight_companies: List[Dict[str, str]] = []

    for rec in records:
        raw = rec.get("raw_company") or {}
        harmonic_raw = rec.get("harmonic_raw") or {}

        name = raw.get("name")
        domain = raw.get("domain")

        employees = find_employees(harmonic_raw)
        highlights_flat: List[Dict] = []

        for emp in employees:
            full_name = emp.get("fullName")
            for h in emp.get("highlights", []) or []:
                category = h.get("category")
                text = h.get("text")

                if category:
                    all_categories.add(category)

                highlights_flat.append(
                    {
                        "fullName": full_name,
                        "category": category,
                        "text": text,
                    }
                )

        if not highlights_flat:
            no_highlight_companies.append(
                {
                    "name": name,
                    "domain": domain,
                }
            )

        out.append(
            {
                "name": name,
                "domain": domain,
                "employee_highlights": highlights_flat,
            }
        )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    with_hl = sum(1 for r in out if r["employee_highlights"])

    print(f"Processed {len(out)} companies")
    print(f"{with_hl} have employee_highlights")
    print(f"{len(no_highlight_companies)} companies have NO employee/founder highlights\n")

    print("🔎 Unique employee highlight categories:")
    for cat in sorted(all_categories):
        print(f" - {cat}")

    print("\n⚠️ Companies with no highlights:")
    for c in no_highlight_companies:
        print(f" - {c['name']} ({c['domain']})")

    print(f"\nWrote detailed highlight data to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
