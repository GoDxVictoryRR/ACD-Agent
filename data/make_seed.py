"""
data/make_seed.py — Filters raw ICIJ Offshore Leaks CSVs into data/seed/icij/.

Uses only stdlib csv module.
Filters by leak and jurisdiction cluster (Panama Papers: Samoa 'SAM' & Seychelles 'SEY')
to ensure graph memory <= 60MB, committed seed <= 40MB, and each file < 25MB.
Includes start_label and end_label on relationships for O(log N) indexed loading.
"""

from __future__ import annotations

import csv
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

RAW_DIR = Path(__file__).resolve().parent / "raw"
SEED_DIR = Path(__file__).resolve().parent / "seed" / "icij"

# Selected subset: Panama Papers Samoa (SAM) & Seychelles (SEY)
# Yields ~20,500 entities, ~29,500 officers, ~1,600 intermediaries, ~250 addresses, ~59,000 edges.
TARGET_SOURCE = "Panama Papers"
TARGET_JURISDICTIONS = {"SAM", "SEY"}

# Relationship normalization and weights
EDGE_WEIGHTS: dict[str, float] = {
    "OFFICER_OF": 1.0,
    "SHAREHOLDER_OF": 1.0,
    "BENEFICIARY_OF": 1.0,
    "DIRECTOR_OF": 1.0,
    "UNDERLYING": 1.5,
    "INTERMEDIARY_OF": 2.0,
    "CONNECTED_TO": 2.5,
    "RELATED_ENTITY": 2.5,
    "REGISTERED_ADDRESS": 3.0,
    "ADDRESS_OF": 3.0,
    "SAME_NAME_AS": 4.0,
    "SAME_AS": 4.0,
    "SAME_ADDRESS_AS": 4.0,
    "SIMILAR": 4.0,
    "SAME_COMPANY_AS": 4.0,
}
DEFAULT_WEIGHT = 2.5


def build_icij_seed() -> dict[str, int]:
    if not (RAW_DIR / "nodes-entities.csv").exists():
        logger.warning("No raw files found in %s", RAW_DIR)
        return {}

    SEED_DIR.mkdir(parents=True, exist_ok=True)
    kept_entity_ids: set[str] = set()
    node_labels: dict[str, str] = {}

    # 1. Filter Entities
    entity_count = 0
    with (
        open(RAW_DIR / "nodes-entities.csv", encoding="utf-8", errors="replace") as fin,
        open(SEED_DIR / "nodes-entities.csv", "w", newline="", encoding="utf-8") as fout,
    ):
        reader = csv.DictReader(fin)
        fieldnames = ["node_id", "name", "jurisdiction", "status", "sourceID"]
        writer = csv.DictWriter(fout, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            source = row.get("sourceID", "")
            jurisdiction = row.get("jurisdiction", "")
            node_id = row.get("node_id", "")

            if source == TARGET_SOURCE and jurisdiction in TARGET_JURISDICTIONS:
                writer.writerow(
                    {
                        "node_id": node_id,
                        "name": row.get("name", "Unnamed Entity").strip(),
                        "jurisdiction": jurisdiction,
                        "status": row.get("status", "").strip(),
                        "sourceID": source,
                    }
                )
                kept_entity_ids.add(node_id)
                node_labels[node_id] = "Entity"
                entity_count += 1

    logger.info("Filtered %d entities", entity_count)

    # 2. First pass over relationships to identify touching nodes
    kept_other_node_ids: set[str] = set()
    raw_rels: list[dict[str, str]] = []
    with open(RAW_DIR / "relationships.csv", encoding="utf-8", errors="replace") as fin:
        reader = csv.DictReader(fin)
        for row in reader:
            start_id = row.get("node_id_start", "")
            end_id = row.get("node_id_end", "")
            if start_id in kept_entity_ids or end_id in kept_entity_ids:
                raw_rels.append(
                    {
                        "start_id": start_id,
                        "end_id": end_id,
                        "rel_type": row.get("rel_type", "CONNECTED_TO"),
                        "link": row.get("link", "").strip(),
                    }
                )
                if start_id not in kept_entity_ids:
                    kept_other_node_ids.add(start_id)
                if end_id not in kept_entity_ids:
                    kept_other_node_ids.add(end_id)

    logger.info("Identified %d relationships and %d other connected nodes", len(raw_rels), len(kept_other_node_ids))

    # 3. Filter Officers, Intermediaries, Addresses, Others & record their labels
    node_files = [
        (
            "nodes-officers.csv",
            "nodes-officers.csv",
            "Officer",
            ["node_id", "name", "country", "sourceID"],
            lambda r: {
                "node_id": r.get("node_id", ""),
                "name": r.get("name", "").strip(),
                "country": r.get("countries", "").strip(),
                "sourceID": r.get("sourceID", ""),
            },
        ),
        (
            "nodes-intermediaries.csv",
            "nodes-intermediaries.csv",
            "Intermediary",
            ["node_id", "name", "country", "status", "sourceID"],
            lambda r: {
                "node_id": r.get("node_id", ""),
                "name": r.get("name", "").strip(),
                "country": r.get("countries", "").strip(),
                "status": r.get("status", "").strip(),
                "sourceID": r.get("sourceID", ""),
            },
        ),
        (
            "nodes-addresses.csv",
            "nodes-addresses.csv",
            "Address",
            ["node_id", "address", "country", "sourceID"],
            lambda r: {
                "node_id": r.get("node_id", ""),
                "address": r.get("address", "").strip(),
                "country": r.get("countries", "").strip(),
                "sourceID": r.get("sourceID", ""),
            },
        ),
        (
            "nodes-others.csv",
            "nodes-others.csv",
            "Other",
            ["node_id", "name", "type", "sourceID"],
            lambda r: {
                "node_id": r.get("node_id", ""),
                "name": r.get("name", "").strip(),
                "type": r.get("type", "").strip(),
                "sourceID": r.get("sourceID", ""),
            },
        ),
    ]

    counts: dict[str, int] = {"entities": entity_count}

    for in_name, out_name, label, fieldnames, mapper in node_files:
        in_path = RAW_DIR / in_name
        if not in_path.exists():
            continue

        c = 0
        with (
            open(in_path, encoding="utf-8", errors="replace") as fin,
            open(SEED_DIR / out_name, "w", newline="", encoding="utf-8") as fout,
        ):
            reader = csv.DictReader(fin)
            writer = csv.DictWriter(fout, fieldnames=fieldnames)
            writer.writeheader()

            for row in reader:
                nid = row.get("node_id", "")
                if nid in kept_other_node_ids:
                    writer.writerow(mapper(row))
                    node_labels[nid] = label
                    c += 1

        counts[out_name] = c
        logger.info("Filtered %d rows for %s (%s)", c, out_name, label)

    # 4. Write relationships with start_label and end_label
    rel_count = 0
    with open(SEED_DIR / "relationships.csv", "w", newline="", encoding="utf-8") as fout:
        fieldnames = ["start_id", "end_id", "rel_type", "link", "weight", "start_label", "end_label"]
        writer = csv.DictWriter(fout, fieldnames=fieldnames)
        writer.writeheader()

        for r in raw_rels:
            start_id = r["start_id"]
            end_id = r["end_id"]
            start_lbl = node_labels.get(start_id, "Entity")
            end_lbl = node_labels.get(end_id, "Entity")

            norm_rel = r["rel_type"].upper().replace(" ", "_").replace("-", "_")
            weight = EDGE_WEIGHTS.get(norm_rel, DEFAULT_WEIGHT)

            writer.writerow(
                {
                    "start_id": start_id,
                    "end_id": end_id,
                    "rel_type": norm_rel,
                    "link": r["link"],
                    "weight": weight,
                    "start_label": start_lbl,
                    "end_label": end_lbl,
                }
            )
            rel_count += 1

    counts["relationships"] = rel_count
    logger.info("Wrote %d relationships with endpoint labels", rel_count)

    # 5. Write ATTRIBUTION.md
    attr_path = SEED_DIR / "ATTRIBUTION.md"
    attr_content = """# Data Attribution: ICIJ Offshore Leaks Database

This dataset is a filtered subset of the Offshore Leaks Database published by the International Consortium of Investigative Journalists (ICIJ).

- **Source**: [ICIJ Offshore Leaks Database](https://offshoreleaks.icij.org/)
- **License**: Open Data Commons Open Database License (ODbL) / Creative Commons Attribution-ShareAlike (CC BY-SA)
- **Scope**: Filtered subset (Panama Papers: Samoa and Seychelles jurisdictions) for educational, demonstration, and investigation research purposes.
- **Disclaimer**: There are legitimate uses for offshore companies and trusts. We do not intend to suggest or imply that any persons, companies or other entities included in the ICIJ Offshore Leaks Database have broken the law or otherwise acted improperly. Inclusion in ICIJ data is not evidence of wrongdoing.
"""
    attr_path.write_text(attr_content, encoding="utf-8")
    logger.info("Wrote %s", attr_path)

    return counts


if __name__ == "__main__":
    res = build_icij_seed()
    print("Seed generation complete:", res)
