"""
scripts/inspect_csvs.py — Inspects raw ICIJ Offshore Leaks CSVs and writes docs/data_notes.md.
"""

import csv
from collections import Counter
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
DOCS_DIR = Path(__file__).resolve().parent.parent / "docs"
OUT_FILE = DOCS_DIR / "data_notes.md"

FILES = [
    "nodes-addresses.csv",
    "nodes-entities.csv",
    "nodes-intermediaries.csv",
    "nodes-officers.csv",
    "nodes-others.csv",
    "relationships.csv",
]


def inspect() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    summary_lines = [
        "# ICIJ Offshore Leaks Data Notes",
        "",
        "Analysis of raw CSV files in `data/raw/` extracted from ICIJ full-oldb database.",
        "",
        "## 1. Raw Files Overview",
        "",
        "| File | Row Count | Column Count | Columns |",
        "|---|---|---|---|",
    ]

    file_details = {}

    for fname in FILES:
        fpath = RAW_DIR / fname
        if not fpath.exists():
            print(f"MISSING: {fname}")
            continue

        with open(fpath, encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            header = next(reader)
            samples = []
            for i, row in enumerate(reader):
                if i < 3:
                    samples.append(row)
                else:
                    break

        with open(fpath, "rb") as f:
            row_count = sum(1 for _ in f) - 1

        file_details[fname] = {
            "header": header,
            "row_count": row_count,
            "samples": samples,
        }
        cols_preview = ", ".join(header[:5]) + ("..." if len(header) > 5 else "")
        summary_lines.append(f"| `{fname}` | {row_count:,} | {len(header)} | {cols_preview} |")

    summary_lines.append("")
    summary_lines.append("## 2. File Schemas and Sample Rows")
    summary_lines.append("")

    for fname, details in file_details.items():
        summary_lines.append(f"### `{fname}` ({details['row_count']:,} rows)")
        summary_lines.append("")
        summary_lines.append(f"**Columns ({len(details['header'])}):** `{'`, `'.join(details['header'])}`")
        summary_lines.append("")
        summary_lines.append("**Sample Rows:**")
        summary_lines.append("```json")
        import json

        samples_formatted = [dict(zip(details["header"], s)) for s in details["samples"]]
        summary_lines.append(json.dumps(samples_formatted, indent=2))
        summary_lines.append("```")
        summary_lines.append("")

    # 3. Relationships rel_type and sourceID
    rel_types = Counter()
    rel_sources = Counter()
    rel_path = RAW_DIR / "relationships.csv"
    with open(rel_path, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rel_types[row["rel_type"]] += 1
            rel_sources[row.get("sourceID", "")] += 1

    summary_lines.append("## 3. Relationship Types (`rel_type`) in `relationships.csv`")
    summary_lines.append("")
    summary_lines.append(f"Total relationship rows: {sum(rel_types.values()):,}")
    summary_lines.append("")
    summary_lines.append("| rel_type | Count | Normalized / Allowlist Target | Proposed Edge Weight |")
    summary_lines.append("|---|---|---|---|")

    # Map proposed weights
    weight_map = {
        "officer_of": ("OFFICER_OF", 1.0),
        "registered_address": ("REGISTERED_ADDRESS", 3.0),
        "intermediary_of": ("INTERMEDIARY_OF", 2.0),
        "same_name_as": ("SAME_NAME_AS", 4.0),
        "similar": ("SIMILAR", 4.0),
        "same_company_as": ("SAME_COMPANY_AS", 4.0),
        "connected_to": ("CONNECTED_TO", 2.5),
        "same_as": ("SAME_AS", 4.0),
        "same_id_as": ("SAME_ID_AS", 4.0),
        "underlying": ("UNDERLYING", 1.5),
        "similar_company_as": ("SIMILAR_COMPANY_AS", 4.0),
        "probably_same_officer_as": ("PROBABLY_SAME_OFFICER_AS", 4.0),
        "same_address_as": ("SAME_ADDRESS_AS", 4.0),
        "same_intermediary_as": ("SAME_INTERMEDIARY_AS", 4.0),
    }

    for rt, cnt in rel_types.most_common():
        target_name, w = weight_map.get(rt, (rt.upper(), 2.5))
        summary_lines.append(f"| `{rt}` | {cnt:,} | `{target_name}` | {w} |")

    summary_lines.append("")
    summary_lines.append("## 4. Distinct `sourceID` with Node and Relationship Counts")
    summary_lines.append("")

    node_sources_by_file = {}
    for fname in [
        "nodes-entities.csv",
        "nodes-officers.csv",
        "nodes-intermediaries.csv",
        "nodes-addresses.csv",
        "nodes-others.csv",
    ]:
        c = Counter()
        with open(RAW_DIR / fname, encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                c[row.get("sourceID", "")] += 1
        node_sources_by_file[fname] = c

    all_sources = set(rel_sources.keys())
    for c in node_sources_by_file.values():
        all_sources.update(c.keys())

    summary_lines.append("| sourceID | Entities | Officers | Intermediaries | Addresses | Others | Relationships |")
    summary_lines.append("|---|---|---|---|---|---|---|")

    # Sort sources by total occurrences
    def total_count(s: str) -> int:
        return (
            node_sources_by_file["nodes-entities.csv"].get(s, 0)
            + node_sources_by_file["nodes-officers.csv"].get(s, 0)
            + node_sources_by_file["nodes-intermediaries.csv"].get(s, 0)
            + node_sources_by_file["nodes-addresses.csv"].get(s, 0)
            + node_sources_by_file["nodes-others.csv"].get(s, 0)
            + rel_sources.get(s, 0)
        )

    for s in sorted(all_sources, key=total_count, reverse=True):
        s_display = f"`{s}`" if s else "*(blank)*"
        e_cnt = node_sources_by_file["nodes-entities.csv"].get(s, 0)
        o_cnt = node_sources_by_file["nodes-officers.csv"].get(s, 0)
        i_cnt = node_sources_by_file["nodes-intermediaries.csv"].get(s, 0)
        a_cnt = node_sources_by_file["nodes-addresses.csv"].get(s, 0)
        oth_cnt = node_sources_by_file["nodes-others.csv"].get(s, 0)
        r_cnt = rel_sources.get(s, 0)
        summary_lines.append(
            f"| {s_display} | {e_cnt:,} | {o_cnt:,} | {i_cnt:,} | {a_cnt:,} | {oth_cnt:,} | {r_cnt:,} |"
        )

    summary_lines.append("")
    summary_lines.append("## 5. Status Values")
    summary_lines.append("")

    entity_status = Counter()
    with open(RAW_DIR / "nodes-entities.csv", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            entity_status[row.get("status", "")] += 1

    summary_lines.append("### Entity Status (Top 25)")
    summary_lines.append("")
    summary_lines.append("| Status | Count |")
    summary_lines.append("|---|---|")
    for st, cnt in entity_status.most_common(25):
        st_display = f"`{st}`" if st else "*(blank)*"
        summary_lines.append(f"| {st_display} | {cnt:,} |")

    interm_status = Counter()
    with open(RAW_DIR / "nodes-intermediaries.csv", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            interm_status[row.get("status", "")] += 1

    summary_lines.append("")
    summary_lines.append("### Intermediary Status")
    summary_lines.append("")
    summary_lines.append("| Status | Count |")
    summary_lines.append("|---|---|")
    for st, cnt in interm_status.most_common():
        st_display = f"`{st}`" if st else "*(blank)*"
        summary_lines.append(f"| {st_display} | {cnt:,} |")

    OUT_FILE.write_text("\n".join(summary_lines), encoding="utf-8")
    print(f"Successfully generated {OUT_FILE} ({OUT_FILE.stat().st_size:,} bytes)")


if __name__ == "__main__":
    inspect()
