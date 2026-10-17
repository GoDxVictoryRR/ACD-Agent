import sys


def get_process_rss_mb() -> float:
    # Cross-platform RSS retrieval without psutil
    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes

            class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
                _fields_ = [
                    ("cb", wintypes.DWORD),
                    ("PageFaultCount", wintypes.DWORD),
                    ("PeakWorkingSetSize", ctypes.c_size_t),
                    ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t),
                    ("PeakPagefileUsage", ctypes.c_size_t),
                ]

            pmc = PROCESS_MEMORY_COUNTERS()
            pmc.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
            handle = ctypes.windll.kernel32.GetCurrentProcess()
            if ctypes.windll.psapi.GetProcessMemoryInfo(handle, ctypes.byref(pmc), pmc.cb):
                return round(pmc.WorkingSetSize / (1024 * 1024), 2)
        except Exception as e:
            print("win32 mem info error:", e)
    else:
        try:
            import resource

            return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 2)
        except Exception:
            pass
    return 0.0


from agent.loop import run_investigation

rss_before = get_process_rss_mb()
print(f"Process RSS before investigation: {rss_before:.2f} MB")

res = run_investigation(
    entity_name="MOSSACK FONSECA & CO. (SAMOA) LIMITED.",
    watchlist=["TIANSHENG INDUSTRY AND TRADING CO., LTD."],
    depth=2,
    force_fallback=True,
)

rss_after = get_process_rss_mb()
print(f"Process RSS after investigation: {rss_after:.2f} MB")
print(f"Verdict: {res['verdict']}")
print("Trace tools and via tags:")
for t in res.get("trace", []):
    print(f"  - {t['tool']}: status={t['status']}, elapsed={t['elapsed_ms']}ms, via={t.get('via')}")

all_mcp = all(t.get("via") == "mcp" for t in res.get("trace", []))
print(f"All tools routed via MCP: {all_mcp}")
assert all_mcp, "All tools must route via MCP!"
print("MCP in live path verified successfully!")
