# utility script to check verticals
import json
from pathlib import Path

PATH = Path("outputs/harmonic_raw_graphql_final.json")

def main() -> None:
    with PATH.open("r", encoding="utf-8") as f:
        rows = json.load(f)

    verticals: set[str] = set()
    sub_verticals: set[str] = set()

    for row in rows:
        harmonic_raw = row.get("harmonic_raw") or {}
        company = harmonic_raw.get("company") or {}
        tags = company.get("tagsV2") or []

        for t in tags:
            t_type = t.get("type")
            value = t.get("displayValue")
            if not value:
                continue

            if t_type == "MARKET_VERTICAL":
                verticals.add(value)
            elif t_type == "MARKET_SUB_VERTICAL":
                sub_verticals.add(value)

    print("=== MARKET_VERTICAL values ===")
    for v in sorted(verticals):
        print(f"- {v}")

    print("\n=== MARKET_SUB_VERTICAL values ===")
    for sv in sorted(sub_verticals):
        print(f"- {sv}")

if __name__ == "__main__":
    main()
