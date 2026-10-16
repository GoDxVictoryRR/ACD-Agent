# Demo Cases: Depth 1 vs Depth 3 Contrast

The following candidate entities demonstrate the critical value of multi-hop graph traversal.
At depth 1, the entity appears minimal or clean. At depth 3, exposure to high-risk hubs or watchlisted entities is uncovered.

| Source Entity | D1 Links | Depth | Target / Watchlist Entity | Path |
|---|---|---|---|---|
| Blue Star Maritime Holdings Ltd | 2 | 3 | Ironclad Sanctions Entity Inc | `Blue Star Maritime Holdings Ltd -> Marcus Sterling -> Apex Nominees Ltd -> Apex Corporate Services SA -> Ironclad Sanctions Entity Inc` |
| Silverline Capital Management Ltd | 1 | 1 | John Alexander Vance (Nominee Hub) | `Silverline Capital Management Ltd -> John Alexander Vance (50 shell entities)` |
| Orion Global Logistics Corp | 1 | 1 | Suite 301, St. James Court (Address Hub) | `Orion Global Logistics Corp -> Suite 301, St. James Court (60+ resident companies)` |
| Solitary Enterprises Ltd | 1 | - | (None - Clean entity) | `Solitary Enterprises Ltd -> 12 Shirley Street, Nassau` |
