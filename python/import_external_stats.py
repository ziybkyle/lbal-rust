"""Extract the user's local aggregate report without executing its JavaScript."""
import argparse
import hashlib
import json
from pathlib import Path


def export(source: Path, destination: Path):
    raw = source.read_bytes()
    text = raw.decode("utf-8")
    payload = text.split("const DATASETS = ", 1)[1]
    data = json.JSONDecoder().raw_decode(payload)[0]["asc20"]
    if not data.get("rows") or not data.get("buckets"):
        raise ValueError("No floor-20 rows or stages in the report")
    rows = {}
    for row in data["rows"]:
        if row["kind"] not in ("symbol", "item", "essence"):
            continue
        key = row["name"]
        if key in rows:
            raise ValueError(f"Duplicate report name: {key}")
        rows[key] = {"kind": row["kind"], "rarity": row["rarity"],
                     "first_offer_n": row.get("first_offer_n", 0),
                     "first_pick_n": row.get("first_pick_n", 0),
                     "buckets": {str(k): {"offers": v.get("offers", 0), "picks": v.get("picks", 0)}
                                 for k, v in row.get("buckets", {}).items()}}
    result = {"schema": 1, "source_sha256": hashlib.sha256(raw).hexdigest(),
              "dataset": data["tag"], "runs": data["runs"], "wins": data["wins"],
              "rents": [b["rent"] for b in data["buckets"]],
              "item_bucket_shift": data.get("bucket_shift", {}).get("item", 0), "rows": rows}
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Imported {len(rows)} aggregate rows from {data['tag']}; SHA-256 {result['source_sha256']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    export(args.source, args.destination)
