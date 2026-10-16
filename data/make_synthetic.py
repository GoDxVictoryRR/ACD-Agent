"""
data/make_synthetic.py — Generates a deterministic synthetic offshore graph.

Schema matches ICIJ Offshore Leaks:
  Nodes: Entity, Officer, Intermediary, Address, Other
  Edges: OFFICER_OF, INTERMEDIARY_OF, REGISTERED_ADDRESS, SHAREHOLDER_OF, CONNECTED_TO

Planted structures:
  1. Blue Star Maritime Holdings Ltd (clean depth 1, 3-hop path to Ironclad Sanctions Entity Inc)
  2. Silverline Capital Management Ltd (connected to high-degree nominee officer John Alexander Vance)
  3. Orion Global Logistics Corp (registered at address hub with 50+ companies)
  4. Solitary Enterprises Ltd (clean, single isolated connection)
"""
from __future__ import annotations

import csv
import random
from pathlib import Path

SEED = 42
TARGET_DIR = Path(__file__).resolve().parent / "seed"


def generate_synthetic_dataset(output_dir: Path | None = None, scale_nodes: int = 5000) -> dict[str, int]:
    out = output_dir or TARGET_DIR
    out.mkdir(parents=True, exist_ok=True)

    rng = random.Random(SEED)

    jurisdictions = ["BVI", "Panama", "Bahamas", "Seychelles", "Cayman Islands", "Cyprus", "Malta", "Belize", "Jersey"]
    countries = ["United Kingdom", "United States", "Cyprus", "Russia", "Switzerland", "United Arab Emirates", "Singapore", "Hong Kong", "China"]
    company_suffixes = ["Ltd", "Inc", "Holdings Corp", "Investments SA", "Trading Co", "Group Ltd", "Capital LLC", "Ventures Ltd"]
    company_roots = ["Apex", "Beacon", "Crest", "Delta", "Echo", "Frontier", "Global", "Horizon", "Imperial", "Jupiter",
                     "Keystone", "Legacy", "Monarch", "Nova", "Olympus", "Pacific", "Quantum", "Radiant", "Summit", "Titan",
                     "Vanguard", "Zephyr", "Atlas", "Boreal", "Cobalt", "Dynamic", "Equinox", "Falcon", "Helios", "Meridian"]
    first_names = ["James", "Alexander", "Elena", "Dmitry", "Michael", "Sergei", "David", "Anna", "Robert", "Maria",
                   "William", "Olga", "Richard", "Tatiana", "Thomas", "Natalia", "Charles", "Irina", "Daniel", "Svetlana"]
    last_names = ["Smith", "Ivanov", "Johnson", "Petrov", "Williams", "Smirnov", "Brown", "Kuznetsov", "Jones", "Popov",
                  "Vance", "Kovalev", "Miller", "Morozov", "Davis", "Volkov", "Wilson", "Alekseev", "Taylor", "Lebedev"]
    streets = ["Wickhams Cay 1", "P.O. Box 146", "St. James Court", "Marina Bay Road", "Coastal Highway 45", "Calle 50",
               "Main Street Suite 200", "Geneva Business Center", "Deira Creek Tower", "Raffles Place"]

    entities: list[dict[str, str]] = []
    officers: list[dict[str, str]] = []
    intermediaries: list[dict[str, str]] = []
    addresses: list[dict[str, str]] = []
    relationships: list[dict[str, str]] = []

    # ── Planted Structure 1: Depth 1 vs Depth 3 Contrast ──────────────────────
    # Blue Star Maritime Holdings Ltd (Depth 1: one officer + one address, no indicators)
    # 3-hop path (ownership edges only):
    #   Blue Star -[OFFICER_OF]-> Marcus Sterling -[OFFICER_OF]-> Apex Nominees Ltd
    #             -[INTERMEDIARY_OF]-> Ironclad Sanctions Entity Inc
    # Depth 1: sees only Marcus Sterling + address → clear
    # Depth 2: also sees Apex Nominees Ltd — but Apex is watchlist itself → escalate at d=2
    # NOTE: to show d=1 clean / d=3 escalate with d=2 also escalate, we want the path
    # Blue Star → Sterling → [nominee cluster] → Apex Nominees → Ironclad
    # So insert a buffer hop: Sterling directors many shells, one of them links to Apex
    # Path: Blue Star -OFFICER_OF-> Sterling -OFFICER_OF-> Vance Shell 001 -OFFICER_OF-> Apex Nominees -INTERMEDIARY_OF-> Ironclad
    # d=1: Blue Star sees {Marcus Sterling, Quayside address} → clear
    # d=2: Blue Star sees {Sterling, Vance Shell 001, address} → clear (no hub rules fire for these)
    # d=3: Blue Star sees Apex Nominees Ltd (watchlist!) → escalate via WATCHLIST_PATH
    e_bluestar = {"node_id": "ENT_BLUESTAR_01", "name": "Blue Star Maritime Holdings Ltd", "jurisdiction": "BVI", "status": "Active", "sourceID": "Panama Papers"}
    o_sterling = {"node_id": "OFF_STERLING_01", "name": "Marcus Sterling", "country": "United Kingdom", "sourceID": "Panama Papers"}
    a_bluestar = {"node_id": "ADDR_BLUESTAR_01", "address": "Quayside House, Road Town, Tortola", "country": "BVI", "sourceID": "Panama Papers"}
    # Buffer entity between Sterling and Apex Nominees (ensures 3 ownership hops from Blue Star)
    e_buffer = {"node_id": "ENT_STERLING_BUFFER_01", "name": "Sterling Bridge Holdings Ltd", "jurisdiction": "Panama", "status": "Active", "sourceID": "Panama Papers"}
    e_apex = {"node_id": "ENT_APEX_NOMINEES", "name": "Apex Nominees Ltd", "jurisdiction": "Panama", "status": "Active", "sourceID": "Panama Papers"}
    e_ironclad = {"node_id": "ENT_IRONCLAD_SANCTIONS", "name": "Ironclad Sanctions Entity Inc", "jurisdiction": "Seychelles", "status": "Active", "sourceID": "Panama Papers"}

    entities.extend([e_bluestar, e_buffer, e_apex, e_ironclad])
    officers.append(o_sterling)
    addresses.append(a_bluestar)

    # Hop 1: Blue Star -> Marcus Sterling (officer)
    relationships.append({"start_id": o_sterling["node_id"], "end_id": e_bluestar["node_id"], "rel_type": "OFFICER_OF", "link": "Director", "weight": "1.0"})
    # Blue Star registered address (depth 1 context, not a path to watchlist)
    relationships.append({"start_id": e_bluestar["node_id"], "end_id": a_bluestar["node_id"], "rel_type": "REGISTERED_ADDRESS", "link": "Registered office", "weight": "3.0"})
    # Hop 2: Marcus Sterling is also officer of Sterling Bridge Holdings Ltd
    relationships.append({"start_id": o_sterling["node_id"], "end_id": e_buffer["node_id"], "rel_type": "OFFICER_OF", "link": "Director", "weight": "1.0"})
    # Hop 3: Sterling Bridge Holdings Ltd is officer of Apex Nominees Ltd (watchlist entity)
    relationships.append({"start_id": e_buffer["node_id"], "end_id": e_apex["node_id"], "rel_type": "SHAREHOLDER_OF", "link": "Beneficial Owner", "weight": "1.0"})
    # Apex Nominees is intermediary for Ironclad Sanctions Entity (confirms escalation target)
    relationships.append({"start_id": e_apex["node_id"], "end_id": e_ironclad["node_id"], "rel_type": "INTERMEDIARY_OF", "link": "Managing agent", "weight": "2.0"})

    # ── Planted Structure 2: Nominee Officer Hub ──────────────────────────────
    # John Alexander Vance is an officer in 50 entities
    e_silverline = {"node_id": "ENT_SILVERLINE_01", "name": "Silverline Capital Management Ltd", "jurisdiction": "Cayman Islands", "status": "Active", "sourceID": "Paradise Papers"}
    o_vance = {"node_id": "OFF_VANCE_NOMINEE", "name": "John Alexander Vance", "country": "Cyprus", "sourceID": "Paradise Papers"}
    entities.append(e_silverline)
    officers.append(o_vance)
    relationships.append({"start_id": o_vance["node_id"], "end_id": e_silverline["node_id"], "rel_type": "OFFICER_OF", "link": "Director", "weight": "1.0"})

    for k in range(1, 51):
        hub_ent_id = f"ENT_VANCE_HUB_{k:03d}"
        hub_ent = {
            "node_id": hub_ent_id,
            "name": f"Vance Shell Entity {k:03d} Ltd",
            "jurisdiction": rng.choice(jurisdictions),
            "status": "Active",
            "sourceID": "Paradise Papers",
        }
        entities.append(hub_ent)
        relationships.append({"start_id": o_vance["node_id"], "end_id": hub_ent_id, "rel_type": "OFFICER_OF", "link": "Nominee Director", "weight": "1.0"})

    # ── Planted Structure 3: Address Hub Cluster ──────────────────────────────
    # Orion Global Logistics Corp registered at a mass incorporation address
    e_orion = {"node_id": "ENT_ORION_01", "name": "Orion Global Logistics Corp", "jurisdiction": "BVI", "status": "Active", "sourceID": "Panama Papers"}
    a_hub = {"node_id": "ADDR_MASS_HUB_01", "address": "Suite 301, St. James Court, Road Town, Tortola", "country": "BVI", "sourceID": "Panama Papers"}
    entities.append(e_orion)
    addresses.append(a_hub)
    relationships.append({"start_id": e_orion["node_id"], "end_id": a_hub["node_id"], "rel_type": "REGISTERED_ADDRESS", "link": "Registered office", "weight": "3.0"})

    for k in range(1, 61):
        addr_ent_id = f"ENT_ADDR_HUB_{k:03d}"
        addr_ent = {
            "node_id": addr_ent_id,
            "name": f"St James Resident {k:03d} Corp",
            "jurisdiction": "BVI",
            "status": "Active",
            "sourceID": "Panama Papers",
        }
        entities.append(addr_ent)
        relationships.append({"start_id": addr_ent_id, "end_id": a_hub["node_id"], "rel_type": "REGISTERED_ADDRESS", "link": "Registered office", "weight": "3.0"})

    # ── Planted Structure 4: Clean / Solitary Entity ──────────────────────────
    e_solitary = {"node_id": "ENT_SOLITARY_01", "name": "Solitary Enterprises Ltd", "jurisdiction": "Bahamas", "status": "Active", "sourceID": "Bahamas Leaks"}
    a_solitary = {"node_id": "ADDR_SOLITARY_01", "address": "12 Shirley Street, Nassau", "country": "Bahamas", "sourceID": "Bahamas Leaks"}
    entities.append(e_solitary)
    addresses.append(a_solitary)
    relationships.append({"start_id": e_solitary["node_id"], "end_id": a_solitary["node_id"], "rel_type": "REGISTERED_ADDRESS", "link": "Registered office", "weight": "3.0"})

    # ── Background Graph Noise (Power-law distributed) ────────────────────────
    # Create background officers, intermediaries, addresses, entities
    bg_entity_count = scale_nodes
    bg_officer_count = int(scale_nodes * 0.6)
    bg_intermediary_count = int(scale_nodes * 0.1)
    bg_address_count = int(scale_nodes * 0.3)

    bg_entities = [
        {
            "node_id": f"ENT_BG_{i:06d}",
            "name": f"{rng.choice(company_roots)} {rng.choice(company_roots)} {rng.choice(company_suffixes)}",
            "jurisdiction": rng.choice(jurisdictions),
            "status": rng.choice(["Active", "Dissolved", "Defaulted", "Struck off"]),
            "sourceID": rng.choice(["Panama Papers", "Pandora Papers", "Paradise Papers", "Bahamas Leaks"]),
        }
        for i in range(1, bg_entity_count + 1)
    ]
    entities.extend(bg_entities)

    bg_officers = [
        {
            "node_id": f"OFF_BG_{i:06d}",
            "name": f"{rng.choice(first_names)} {rng.choice(last_names)}",
            "country": rng.choice(countries),
            "sourceID": rng.choice(["Panama Papers", "Pandora Papers", "Paradise Papers"]),
        }
        for i in range(1, bg_officer_count + 1)
    ]
    officers.extend(bg_officers)

    bg_intermediaries = [
        {
            "node_id": f"INT_BG_{i:06d}",
            "name": f"{rng.choice(company_roots)} Legal & Trust Services",
            "country": rng.choice(countries),
            "status": "Active",
            "sourceID": "Panama Papers",
        }
        for i in range(1, bg_intermediary_count + 1)
    ]
    intermediaries.extend(bg_intermediaries)

    bg_addresses = [
        {
            "node_id": f"ADDR_BG_{i:06d}",
            "address": f"{rng.randint(1, 999)} {rng.choice(streets)}",
            "country": rng.choice(jurisdictions),
            "sourceID": "Panama Papers",
        }
        for i in range(1, bg_address_count + 1)
    ]
    addresses.extend(bg_addresses)

    # Connect background nodes with realistic degree distribution
    for e in bg_entities:
        # Each entity gets 1-2 officers
        for _ in range(rng.choices([1, 2, 3], weights=[0.7, 0.25, 0.05])[0]):
            off = rng.choice(bg_officers)
            role = rng.choice(["Director", "Shareholder", "Beneficial Owner", "Secretary"])
            rel_type = "SHAREHOLDER_OF" if role == "Shareholder" else "OFFICER_OF"
            relationships.append({
                "start_id": off["node_id"],
                "end_id": e["node_id"],
                "rel_type": rel_type,
                "link": role,
                "weight": "1.0",
            })

        # Most entities get an address (preferential attachment to top 10% addresses)
        if rng.random() < 0.85:
            if rng.random() < 0.35:
                addr = rng.choice(bg_addresses[:max(5, len(bg_addresses) // 20)])
            else:
                addr = rng.choice(bg_addresses)
            relationships.append({
                "start_id": e["node_id"],
                "end_id": addr["node_id"],
                "rel_type": "REGISTERED_ADDRESS",
                "link": "Registered address",
                "weight": "3.0",
            })

        # Some entities have an intermediary
        if rng.random() < 0.40:
            inter = rng.choice(bg_intermediaries)
            relationships.append({
                "start_id": inter["node_id"],
                "end_id": e["node_id"],
                "rel_type": "INTERMEDIARY_OF",
                "link": "Incorporation agent",
                "weight": "2.0",
            })

    # Write files
    def write_csv(path: Path, data: list[dict[str, str]], fieldnames: list[str]) -> None:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

    write_csv(out / "nodes-entities.csv", entities, ["node_id", "name", "jurisdiction", "status", "sourceID"])
    write_csv(out / "nodes-officers.csv", officers, ["node_id", "name", "country", "sourceID"])
    write_csv(out / "nodes-intermediaries.csv", intermediaries, ["node_id", "name", "country", "status", "sourceID"])
    write_csv(out / "nodes-addresses.csv", addresses, ["node_id", "address", "country", "sourceID"])
    write_csv(out / "relationships.csv", relationships, ["start_id", "end_id", "rel_type", "link", "weight"])

    # Attribution file
    attrib_path = out / "ATTRIBUTION.md"
    with open(attrib_path, "w", encoding="utf-8") as f:
        f.write(
            "# Synthetic Graph Dataset\n\n"
            "This seed dataset was generated by `data/make_synthetic.py` using seeded random generation.\n"
            "Schema strictly mirrors the ICIJ Offshore Leaks database schema.\n"
            "All entity and officer names in this synthetic seed are fictitious.\n"
            "Used for local development, CI tests, and fallback demonstration.\n"
        )

    return {
        "entities": len(entities),
        "officers": len(officers),
        "intermediaries": len(intermediaries),
        "addresses": len(addresses),
        "relationships": len(relationships),
    }


if __name__ == "__main__":
    counts = generate_synthetic_dataset()
    print("Synthetic dataset generated in data/seed/:")
    for k, v in counts.items():
        print(f"  {k}: {v}")
