# ICIJ Offshore Leaks Data Notes

Analysis of raw CSV files in `data/raw/` extracted from ICIJ full-oldb database.

## 1. Raw Files Overview

| File | Row Count | Column Count | Columns |
|---|---|---|---|
| `nodes-addresses.csv` | 402,320 | 8 | node_id, address, name, countries, country_codes... |
| `nodes-entities.csv` | 814,616 | 21 | node_id, name, original_name, former_name, jurisdiction... |
| `nodes-intermediaries.csv` | 26,774 | 10 | node_id, name, status, internal_id, address... |
| `nodes-officers.csv` | 771,368 | 7 | node_id, name, countries, country_codes, sourceID... |
| `nodes-others.csv` | 2,989 | 13 | node_id, name, type, incorporation_date, struck_off_date... |
| `relationships.csv` | 3,339,271 | 8 | node_id_start, node_id_end, rel_type, link, status... |

## 2. File Schemas and Sample Rows

### `nodes-addresses.csv` (402,320 rows)

**Columns (8):** `node_id`, `address`, `name`, `countries`, `country_codes`, `sourceID`, `valid_until`, `note`

**Sample Rows:**
```json
[
  {
    "node_id": "24000001",
    "address": "ANNEX FREDERICK & SHIRLEY STS, P.O. BOX N-4805, NASSAU, BAHAMAS",
    "name": "",
    "countries": "Bahamas",
    "country_codes": "BHS",
    "sourceID": "Bahamas Leaks",
    "valid_until": "The Bahamas Leaks data is current through early 2016.",
    "note": ""
  },
  {
    "node_id": "24000002",
    "address": "SUITE E-2,UNION COURT BUILDING, P.O. BOX N-8188, NASSAU, BAHAMAS",
    "name": "",
    "countries": "Bahamas",
    "country_codes": "BHS",
    "sourceID": "Bahamas Leaks",
    "valid_until": "The Bahamas Leaks data is current through early 2016.",
    "note": ""
  },
  {
    "node_id": "24000003",
    "address": "LYFORD CAY HOUSE, LYFORD CAY, P.O. BOX N-7785, NASSAU, BAHAMAS",
    "name": "",
    "countries": "Bahamas",
    "country_codes": "BHS",
    "sourceID": "Bahamas Leaks",
    "valid_until": "The Bahamas Leaks data is current through early 2016.",
    "note": ""
  }
]
```

### `nodes-entities.csv` (814,616 rows)

**Columns (21):** `node_id`, `name`, `original_name`, `former_name`, `jurisdiction`, `jurisdiction_description`, `company_type`, `address`, `internal_id`, `incorporation_date`, `inactivation_date`, `struck_off_date`, `dorm_date`, `status`, `service_provider`, `ibcRUC`, `country_codes`, `countries`, `sourceID`, `valid_until`, `note`

**Sample Rows:**
```json
[
  {
    "node_id": "10000001",
    "name": "TIANSHENG INDUSTRY AND TRADING CO., LTD.",
    "original_name": "TIANSHENG INDUSTRY AND TRADING CO., LTD.",
    "former_name": "",
    "jurisdiction": "SAM",
    "jurisdiction_description": "Samoa",
    "company_type": "",
    "address": "ORION HOUSE SERVICES (HK) LIMITED ROOM 1401; 14/F.; WORLD COMMERCE  CENTRE; HARBOUR CITY; 7-11 CANTON ROAD; TSIM SHA TSUI; KOWLOON; HONG KONG",
    "internal_id": "1001256",
    "incorporation_date": "23-MAR-2006",
    "inactivation_date": "18-FEB-2013",
    "struck_off_date": "15-FEB-2013",
    "dorm_date": "",
    "status": "Defaulted",
    "service_provider": "Mossack Fonseca",
    "ibcRUC": "25221",
    "country_codes": "HKG",
    "countries": "Hong Kong",
    "sourceID": "Panama Papers",
    "valid_until": "The Panama Papers data is current through 2015",
    "note": ""
  },
  {
    "node_id": "10000002",
    "name": "NINGBO SUNRISE ENTERPRISES UNITED CO., LTD.",
    "original_name": "NINGBO SUNRISE ENTERPRISES UNITED CO., LTD.",
    "former_name": "",
    "jurisdiction": "SAM",
    "jurisdiction_description": "Samoa",
    "company_type": "",
    "address": "ORION HOUSE SERVICES (HK) LIMITED ROOM 1401; 14/F.; WORLD COMMERCE  CENTRE; HARBOUR CITY; 7-11 CANTON ROAD; TSIM SHA TSUI; KOWLOON; HONG KONG",
    "internal_id": "1001263",
    "incorporation_date": "27-MAR-2006",
    "inactivation_date": "27-FEB-2014",
    "struck_off_date": "15-FEB-2014",
    "dorm_date": "",
    "status": "Defaulted",
    "service_provider": "Mossack Fonseca",
    "ibcRUC": "25249",
    "country_codes": "HKG",
    "countries": "Hong Kong",
    "sourceID": "Panama Papers",
    "valid_until": "The Panama Papers data is current through 2015",
    "note": ""
  },
  {
    "node_id": "10000003",
    "name": "HOTFOCUS CO., LTD.",
    "original_name": "HOTFOCUS CO., LTD.",
    "former_name": "",
    "jurisdiction": "SAM",
    "jurisdiction_description": "Samoa",
    "company_type": "",
    "address": "ORION HOUSE SERVICES (HK) LIMITED ROOM 1401; 14/F.; WORLD COMMERCE  CENTRE; HARBOUR CITY; 7-11 CANTON ROAD; TSIM SHA TSUI; KOWLOON; HONG KONG",
    "internal_id": "1000896",
    "incorporation_date": "10-JAN-2006",
    "inactivation_date": "15-FEB-2012",
    "struck_off_date": "15-FEB-2012",
    "dorm_date": "",
    "status": "Defaulted",
    "service_provider": "Mossack Fonseca",
    "ibcRUC": "24138",
    "country_codes": "HKG",
    "countries": "Hong Kong",
    "sourceID": "Panama Papers",
    "valid_until": "The Panama Papers data is current through 2015",
    "note": ""
  }
]
```

### `nodes-intermediaries.csv` (26,774 rows)

**Columns (10):** `node_id`, `name`, `status`, `internal_id`, `address`, `countries`, `country_codes`, `sourceID`, `valid_until`, `note`

**Sample Rows:**
```json
[
  {
    "node_id": "11000001",
    "name": "MICHAEL PAPAGEORGE, MR.",
    "status": "ACTIVE",
    "internal_id": "10001",
    "address": "MICHAEL PAPAGEORGE; MR. 106 NICHOLSON STREET BROOKLYN PRETORIA 0002; GAUTENG (PWV) SOUTH AFRICA",
    "countries": "South Africa",
    "country_codes": "ZAF",
    "sourceID": "Panama Papers",
    "valid_until": "The Panama Papers  data is current through 2015",
    "note": ""
  },
  {
    "node_id": "11000002",
    "name": "CORFIDUCIA ANSTALT",
    "status": "ACTIVE",
    "internal_id": "10004",
    "address": "",
    "countries": "Liechtenstein",
    "country_codes": "LIE",
    "sourceID": "Panama Papers",
    "valid_until": "The Panama Papers  data is current through 2015",
    "note": ""
  },
  {
    "node_id": "11000003",
    "name": "DAVID, RONALD",
    "status": "SUSPENDED",
    "internal_id": "10014",
    "address": "",
    "countries": "Monaco",
    "country_codes": "MCO",
    "sourceID": "Panama Papers",
    "valid_until": "The Panama Papers  data is current through 2015",
    "note": ""
  }
]
```

### `nodes-officers.csv` (771,368 rows)

**Columns (7):** `node_id`, `name`, `countries`, `country_codes`, `sourceID`, `valid_until`, `note`

**Sample Rows:**
```json
[
  {
    "node_id": "12000001",
    "name": "KIM SOO IN",
    "countries": "South Korea",
    "country_codes": "KOR",
    "sourceID": "Panama Papers",
    "valid_until": "The Panama Papers data is current through 2015",
    "note": ""
  },
  {
    "node_id": "12000002",
    "name": "Tian Yuan",
    "countries": "China",
    "country_codes": "CHN",
    "sourceID": "Panama Papers",
    "valid_until": "The Panama Papers data is current through 2015",
    "note": ""
  },
  {
    "node_id": "12000003",
    "name": "GREGORY JOHN SOLOMON",
    "countries": "Australia",
    "country_codes": "AUS",
    "sourceID": "Panama Papers",
    "valid_until": "The Panama Papers data is current through 2015",
    "note": ""
  }
]
```

### `nodes-others.csv` (2,989 rows)

**Columns (13):** `node_id`, `name`, `type`, `incorporation_date`, `struck_off_date`, `closed_date`, `jurisdiction`, `jurisdiction_description`, `countries`, `country_codes`, `sourceID`, `valid_until`, `note`

**Sample Rows:**
```json
[
  {
    "node_id": "85004929",
    "name": "ANTAM ENTERPRISES N.V.",
    "type": "LIMITED LIABILITY COMPANY",
    "incorporation_date": "18-MAY-1983",
    "struck_off_date": "",
    "closed_date": "28-NOV-2012",
    "jurisdiction": "AW",
    "jurisdiction_description": "Aruba",
    "countries": "",
    "country_codes": "",
    "sourceID": "Paradise Papers - Aruba corporate registry",
    "valid_until": "Aruba corporate registry data is current through 2016",
    "note": "Closed date stands for Cancelled date."
  },
  {
    "node_id": "85008443",
    "name": "DEVIATION N.V.",
    "type": "LIMITED LIABILITY COMPANY",
    "incorporation_date": "28-JUN-1989",
    "struck_off_date": "31-DEC-2002",
    "closed_date": "",
    "jurisdiction": "AW",
    "jurisdiction_description": "Aruba",
    "countries": "",
    "country_codes": "",
    "sourceID": "Paradise Papers - Aruba corporate registry",
    "valid_until": "Aruba corporate registry data is current through 2016",
    "note": ""
  },
  {
    "node_id": "85008517",
    "name": "ARIAZI N.V.",
    "type": "LIMITED LIABILITY COMPANY",
    "incorporation_date": "19-JUL-1989",
    "struck_off_date": "",
    "closed_date": "19-MAY-2004",
    "jurisdiction": "AW",
    "jurisdiction_description": "Aruba",
    "countries": "",
    "country_codes": "",
    "sourceID": "Paradise Papers - Aruba corporate registry",
    "valid_until": "Aruba corporate registry data is current through 2016",
    "note": "Closed date stands for Cancelled date."
  }
]
```

### `relationships.csv` (3,339,271 rows)

**Columns (8):** `node_id_start`, `node_id_end`, `rel_type`, `link`, `status`, `start_date`, `end_date`, `sourceID`

**Sample Rows:**
```json
[
  {
    "node_id_start": "10000035",
    "node_id_end": "14095990",
    "rel_type": "registered_address",
    "link": "registered address",
    "status": "",
    "start_date": "",
    "end_date": "",
    "sourceID": "Panama Papers"
  },
  {
    "node_id_start": "10000044",
    "node_id_end": "14091035",
    "rel_type": "registered_address",
    "link": "registered address",
    "status": "",
    "start_date": "",
    "end_date": "",
    "sourceID": "Panama Papers"
  },
  {
    "node_id_start": "10000055",
    "node_id_end": "14095990",
    "rel_type": "registered_address",
    "link": "registered address",
    "status": "",
    "start_date": "",
    "end_date": "",
    "sourceID": "Panama Papers"
  }
]
```

## 3. Relationship Types (`rel_type`) in `relationships.csv`

Total relationship rows: 3,339,267

| rel_type | Count | Normalized / Allowlist Target | Proposed Edge Weight |
|---|---|---|---|
| `officer_of` | 1,720,357 | `OFFICER_OF` | 1.0 |
| `registered_address` | 832,721 | `REGISTERED_ADDRESS` | 3.0 |
| `intermediary_of` | 598,546 | `INTERMEDIARY_OF` | 2.0 |
| `same_name_as` | 104,170 | `SAME_NAME_AS` | 4.0 |
| `similar` | 46,761 | `SIMILAR` | 4.0 |
| `same_company_as` | 15,523 | `SAME_COMPANY_AS` | 4.0 |
| `connected_to` | 12,145 | `CONNECTED_TO` | 2.5 |
| `same_as` | 4,272 | `SAME_AS` | 4.0 |
| `same_id_as` | 3,120 | `SAME_ID_AS` | 4.0 |
| `underlying` | 1,308 | `UNDERLYING` | 1.5 |
| `similar_company_as` | 203 | `SIMILAR_COMPANY_AS` | 4.0 |
| `probably_same_officer_as` | 132 | `PROBABLY_SAME_OFFICER_AS` | 4.0 |
| `same_address_as` | 5 | `SAME_ADDRESS_AS` | 4.0 |
| `same_intermediary_as` | 4 | `SAME_INTERMEDIARY_AS` | 4.0 |

## 4. Distinct `sourceID` with Node and Relationship Counts

| sourceID | Entities | Officers | Intermediaries | Addresses | Others | Relationships |
|---|---|---|---|---|---|---|
| `Panama Papers` | 213,634 | 238,402 | 14,110 | 93,454 | 0 | 674,102 |
| `Paradise Papers - Malta corporate registry` | 83,896 | 107,210 | 0 | 123,269 | 0 | 776,335 |
| `Offshore Leaks` | 105,516 | 107,190 | 9,526 | 57,600 | 0 | 561,393 |
| `Paradise Papers - Appleby` | 24,936 | 76,915 | 185 | 59,200 | 2,031 | 390,966 |
| *(blank)* | 0 | 0 | 0 | 0 | 0 | 518,982 |
| `Bahamas Leaks` | 175,888 | 25,262 | 541 | 551 | 0 | 249,190 |
| `Paradise Papers - Aruba corporate registry` | 49,047 | 31,286 | 74 | 17,901 | 888 | 129,715 |
| `Paradise Papers - Barbados corporate registry` | 40,838 | 127,912 | 974 | 20,768 | 0 | 62 |
| `Paradise Papers - Nevis corporate registry` | 70,501 | 202 | 96 | 187 | 0 | 0 |
| `Pandora Papers - Alemán, Cordero, Galindo & Lee (Alcogal)` | 16,077 | 23,895 | 1,023 | 13,100 | 5 | 0 |
| `Paradise Papers - Bahamas corporate registry` | 17,800 | 11 | 239 | 333 | 0 | 19,968 |
| `Paradise Papers - Samoa corporate registry` | 1,595 | 5,828 | 0 | 1,695 | 0 | 15,338 |
| `Pandora Papers - SFM Corporate Services` | 2,930 | 8,236 | 0 | 1,883 | 0 | 0 |
| `Pandora Papers - Trident Trust` | 1,729 | 5,465 | 0 | 2,395 | 49 | 0 |
| `Pandora Papers - Commence Overseas` | 2,427 | 4,021 | 0 | 1,813 | 0 | 0 |
| `Pandora Papers - Alpha Consulting` | 2,116 | 2,746 | 0 | 2,660 | 0 | 0 |
| `Pandora Papers - Fidelity Corporate Services` | 1,883 | 2,482 | 0 | 2,940 | 2 | 0 |
| `Paradise Papers - Cook Islands corporate registry` | 1,469 | 644 | 0 | 0 | 0 | 3,212 |
| `Pandora Papers - CILTrust International` | 1,355 | 2,079 | 0 | 1,706 | 3 | 0 |
| `Pandora Papers - Il Shin Corporate Consulting Limited` | 292 | 869 | 0 | 508 | 0 | 0 |
| `Pandora Papers - Overseas Management Company (OMC)` | 277 | 439 | 0 | 256 | 11 | 0 |
| `Pandora Papers - Asiaciti Trust` | 134 | 220 | 0 | 27 | 0 | 0 |
| `Paradise Papers - Lebanon corporate registry` | 4 | 1 | 0 | 0 | 0 | 4 |

## 5. Status Values

### Entity Status (Top 25)

| Status | Count |
|---|---|
| *(blank)* | 456,308 |
| `Active` | 116,022 |
| `Defaulted` | 100,090 |
| `Dissolved` | 24,082 |
| `Dead` | 23,095 |
| `Struck / Defunct / Deregistered` | 19,486 |
| `Struck Off` | 16,521 |
| `Changed agent` | 16,043 |
| `Inactivated` | 7,640 |
| `In Dissolution` | 6,687 |
| `Resigned as agent` | 3,174 |
| `Struck Off as Defunct` | 2,879 |
| `Transferred OUT` | 2,637 |
| `Shelf company` | 2,576 |
| `Transferred Out` | 1,808 |
| `Dissolved shelf company` | 1,573 |
| `Struck Off Following Merger` | 1,447 |
| `Bad debt account` | 1,416 |
| `Registered` | 1,014 |
| `Inactive` | 987 |
| `Trash company` | 878 |
| `Liquidated` | 849 |
| `In Penalty` | 802 |
| `In transition` | 776 |
| `Company liquidated` | 742 |

### Intermediary Status

| Status | Count |
|---|---|
| *(blank)* | 14,147 |
| `ACTIVE` | 7,062 |
| `SUSPENDED` | 4,756 |
| `UNRECOVERABLE ACCOUNTS` | 382 |
| `INACTIVE` | 270 |
| `PROSPECT` | 90 |
| `CLIENT IN REPRESENTATIVE TERRITORY` | 23 |
| `DELINQUENT` | 21 |
| `ACTIVE LEGAL` | 14 |
| `SUSPENDED LEGAL` | 3 |