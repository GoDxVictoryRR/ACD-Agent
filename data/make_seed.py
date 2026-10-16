"""
data/make_seed.py — Filters raw ICIJ Offshore Leaks CSVs into committed data/seed/ files.

Reads from data/raw/ and filters by target jurisdiction/leak to keep in-memory size
comfortably under FalkorDB Cloud's 100MB free RAM limit.
Keeps only: node_id, name, jurisdiction/country, status, sourceID.
Drops verbose text columns.
"""
from __future__ import annotations

import csv
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

RAW_DIR = Path(__file__).resolve().parent / "raw"
SEED_DIR = Path(__file__).resolve().parent / "seed"

# Target subset: high density jurisdictions in Panama & Paradise Papers
TARGET_JURISDICTIONS = {"BVI", "PAN", "BAH", "SAM", "SEY", "CYP", "MLT"}
TARGET_SOURCES = {"Panama Papers", "Paradise Papers - Appleby", "Bahamas Leaks"}


def filter_subset() -> dict[str, int]:
    if not (RAW_DIR / "nodes-entities.csv").exists():
        logger.warning("No raw files found in %s. Please download ICIJ full-oldb zip first.", RAW_DIR)
        return {}

    SEED_DIR.mkdir(parents=True, exist_ok=True)
    kept_entity_ids: set[str] = set()

    # 1. Filter Entities
    entity_count = 0
    with open(RAW_DIR / "nodes-entities.csv", encoding="utf-8", errors="replace") as fin, \
         open(SEED_DIR / "nodes-entities.csv", "w", newline="", encoding="utf-8") as fout:
        reader = csv.DictReader(fin)
        fieldnames = ["node_id", "name", "jurisdiction", "status", "sourceID"]
        writer = csv.DictWriter(fout, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            node_id = row.get("node_id", "")
            jurisdiction = row.get("jurisdiction", "")
            source = row.get("sourceID", "")

            # Filter criterion
            if jurisdiction in TARGET_JURISDICTIONS or source in TARGET_SOURCES:
                writer.writerow({
                    "node_id": node_id,
                    "name": row.get("name", "Unnamed Entity"),
                    "jurisdiction": jurisdiction,
                    "status": row.get("status", ""),
                    "sourceID": source,
                })
                kept_entity_ids.add(node_id)
                entity_count += 1
                if entity_count >= 50000:  # Cap to fit in 60MB RAM
                    break

    logger.info("Filtered %d entities", entity_count)

    # 2. Filter Relationships touching kept entities
    kept_related_ids: set[str] = set()
    rel_count = 0
    with open(RAW_DIR / "relationships.csv", encoding="utf-8", errors="replace") as fin, \
         open(SEED_DIR / "relationships.csv", "w", newline="", encoding="utf-8") as fout:
        reader = csv.DictReader(fin)
        fieldnames = ["start_id", "end_id", "rel_type", "link", "weight"]
        writer = csv.DictWriter(fout, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            start_id = row.get("node_id_start", row.get("start_id", ""))
            end_id = row.get("node_id_end", row.get("end_id", ""))

            if start_id in kept_entity_ids or end_id in kept_entity_ids:
                rel_type = row.get("rel_type", "CONNECTED_TO").upper().replace(" ", "_")
                writer.writerow({
                    "start_id": start_id,
                    "end_id": end_id,
                    "rel_type": rel_type,
                    "link": row.get("link", ""),
                    "weight": 2.0,
                })
                kept_related_ids.add(start_id)
                kept_related_ids.add(end_id)
                rel_count += 1

    logger.info("Filtered %d relationships", rel_count)

    # 3. Filter Officers, Intermediaries, Addresses
    node_files = [
        ("nodes-officers.csv", "nodes-officers.csv", ["node_id", "name", "country", "sourceID"]),
        ("nodes-intermediaries.csv", "nodes-intermediaries.csv", ["node_id", "name", "country", "status", "sourceID"]),
        ("nodes-addresses.csv", "nodes-addresses.csv", ["node_id", "address", "country", "sourceID"]),
    ]

    counts: dict[str, int] = {"entities": entity_count, "relationships": rel_count}

    for in_name, out_name, fields in node_files:
        in_path = RAW_DIR / in_name
        if not in_path.exists():
            continue

        c = 0
        with open(in_path, encoding="utf-8", errors="replace") as fin, \
             open(SEED_DIR / out_name, "w", newline="", encoding="utf-8") as fout:
            reader = csv.DictReader(fin)
            writer = csv.DictWriter(fout, fieldnames=fields)
            writer.writeheader()

            for row in reader:
                nid = row.get("node_id", "")
                if nid in kept_related_ids:
                    filtered_row = {f: row.get(f, "") for f in fields}
                    writer.writerow(filtered_row)
                    c += 1

        counts[out_name] = c
        logger.info("Filtered %d rows for %s", c, out_name)

    return counts


if __name__ == "__main__":
    filter_subset()
