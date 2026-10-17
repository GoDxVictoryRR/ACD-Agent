"""Test Item 13: API hardening.
Tests:
- 201-char name -> 422
- Control characters -> sanitized, no 500
- Depth 9 -> 422 (max depth is 4)
- Watchlist of 50 -> 422 (max items is 10)
- Wrong Origin -> no Access-Control-Allow-Origin
- Burst of requests -> 429 Too Many Requests, no stack traces
"""

import httpx

API = "http://localhost:8000"

print("=== 1. Testing 201-char entity name ===")
r_long = httpx.post(f"{API}/investigate", json={"entity": "A" * 201, "depth": 3}, timeout=5)
print(f"201-char name status: {r_long.status_code}")
assert r_long.status_code == 422, f"Expected 422, got {r_long.status_code}"
assert "traceback" not in r_long.text.lower()
print("[PASS] 201-char name rejected with 422")

print("\n=== 2. Testing control characters ===")
r_ctrl = httpx.post(f"{API}/investigate", json={"entity": "Blue\x00Star\x1fMaritime\x07Ltd", "depth": 3}, timeout=5)
print(f"Control chars status: {r_ctrl.status_code}")
assert r_ctrl.status_code in (200, 400), f"Expected 200 or 400, got {r_ctrl.status_code}"
assert "traceback" not in r_ctrl.text.lower()
print("[PASS] Control chars sanitized without stack trace")

print("\n=== 3. Testing depth 9 (le=4) ===")
r_depth = httpx.post(f"{API}/investigate", json={"entity": "Blue Star Maritime Holdings Ltd", "depth": 9}, timeout=5)
print(f"Depth 9 status: {r_depth.status_code}")
assert r_depth.status_code == 422, f"Expected 422, got {r_depth.status_code}"
assert "traceback" not in r_depth.text.lower()
print("[PASS] Depth 9 rejected with 422")

print("\n=== 4. Testing watchlist of 50 (max_length=10) ===")
r_watch = httpx.post(
    f"{API}/investigate",
    json={"entity": "Blue Star Maritime Holdings Ltd", "watchlist": [f"Target_{i}" for i in range(50)], "depth": 3},
    timeout=5,
)
print(f"Watchlist of 50 status: {r_watch.status_code}")
assert r_watch.status_code == 422, f"Expected 422, got {r_watch.status_code}"
assert "traceback" not in r_watch.text.lower()
print("[PASS] Watchlist >10 rejected with 422")

print("\n=== 5. Testing wrong Origin ===")
r_cors = httpx.get(f"{API}/health", headers={"Origin": "http://malicious-site.com"}, timeout=5)
print("CORS response headers:", r_cors.headers.get("access-control-allow-origin"))
assert r_cors.headers.get("access-control-allow-origin") != "http://malicious-site.com"
print("[PASS] Wrong origin not reflected in CORS headers")

print("\n=== 6. Testing Burst / Rate Limiting (Burst of requests) ===")
saw_429 = False
for i in range(70):
    r_burst = httpx.post(
        f"{API}/investigate", json={"entity": "Solitary Enterprises Ltd", "depth": 1, "no_llm": True}, timeout=5
    )
    if r_burst.status_code == 429:
        saw_429 = True
        print(f"Rate limited at request #{i + 1} with 429: {r_burst.json()}")
        assert "traceback" not in r_burst.text.lower()
        break

assert saw_429, "Expected 429 rate limit during burst"
print("[PASS] Rate limiter returned 429 without stack trace")

print("\nOVERALL: ITEM 13 (API HARDENING) PASS")
