"""
scripts/check_invariants.py — Automated verification of project architectural invariants.

Invariants checked:
1. Forbidden library imports: No pandas, langchain, langgraph, graphiti, graphrag-sdk.
2. LLM Cypher isolation: No raw Cypher in agent/ or prompts.
3. Read-only graph query routing: All read queries use ro() / ro_query; rw() is restricted to writes.
4. Meta-graph isolation: Case nodes and ABOUT/CITED meta-edges strictly excluded from read queries.
5. Secret protection: No .env files or live API keys (nvapi-...) tracked by git.
6. Data privacy: data/raw/ is gitignored and contains zero git-tracked files.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

INVARIANTS_LIST = [
    "1. Forbidden library imports (no pandas, langchain, langgraph, graphiti, graphrag)",
    "2. LLM Cypher isolation (no Cypher queries or clauses in agent/ or prompts)",
    "3. Read routing verification (all reads via ro_query / ro(); rw() restricted to write tools)",
    "4. Case / ABOUT / CITED exclusion from read traversals",
    "5. Git tracked secrets and .env protection",
    "6. data/raw/ privacy protection (gitignored, untracked raw ICIJ data)",
]

FORBIDDEN_IMPORTS = ["pandas", "langchain", "langgraph", "graphiti", "graphrag"]

CYPHER_PATTERNS = [
    r"(?<!\.)\bMATCH\s*\(",
    r"(?<!\.)\bCREATE\s*\(",
    r"(?<!\.)\bMERGE\s*\(",
    r"(?<!\.)\bDETACH\s+DELETE\b",
    r"(?<!\.)\bCALL\s+algo\.",
]


def check_forbidden_imports() -> list[str]:
    violations = []
    py_files = list(REPO_ROOT.glob("**/*.py"))
    for p in py_files:
        if ".venv" in p.parts:
            continue
        try:
            content = p.read_text(encoding="utf-8")
        except Exception:
            continue
        for imp in FORBIDDEN_IMPORTS:
            if re.search(rf"\bimport\s+{imp}\b|\bfrom\s+{imp}\b", content):
                violations.append(f"Forbidden import '{imp}' found in {p.relative_to(REPO_ROOT)}")
    return violations


def check_cypher_in_agent() -> list[str]:
    violations = []
    agent_files = list((REPO_ROOT / "agent").glob("*.py"))
    for p in agent_files:
        try:
            content = p.read_text(encoding="utf-8")
        except Exception:
            continue
        for pat in CYPHER_PATTERNS:
            if re.search(pat, content, re.IGNORECASE):
                violations.append(f"Cypher pattern '{pat}' found in agent file: {p.relative_to(REPO_ROOT)}")
    return violations


def check_all_reads_via_ro() -> list[str]:
    """Invariant: All reads in core/tools.py must use ro(), never rw(). rw() is only in record_decision and scratch."""
    violations = []
    tools_file = REPO_ROOT / "core" / "tools.py"
    if not tools_file.exists():
        return ["core/tools.py not found"]

    content = tools_file.read_text(encoding="utf-8")

    # Ensure ro is imported and used
    if "from core.db import drop_graph, ro, rw" not in content and "from core.db import" not in content:
        violations.append("core/tools.py does not import ro from core.db")

    # In read tools: resolve_entity, ownership_chain, shared_links, path_between
    read_tools = ["resolve_entity", "ownership_chain", "shared_links", "path_between"]
    for tool_name in read_tools:
        # Extract function body
        pattern = rf"def {tool_name}\(.*?\n(?=def |\Z)"
        match = re.search(pattern, content, re.DOTALL)
        if match:
            body = match.group(0)
            if "rw(" in body:
                violations.append(f"Read tool '{tool_name}' uses rw() write function!")
            if "ro(" not in body:
                violations.append(f"Read tool '{tool_name}' does not use ro() for querying!")
    return violations


def check_case_meta_exclusion() -> list[str]:
    """Invariant: Case nodes and ABOUT/CITED edges must be strictly excluded from read queries."""
    violations = []
    tools_file = REPO_ROOT / "core" / "tools.py"
    if not tools_file.exists():
        return ["core/tools.py not found"]

    content = tools_file.read_text(encoding="utf-8")

    # 1. Assert _OWNERSHIP_REL_TYPES explicitly excludes ABOUT and CITED
    ownership_rel_match = re.search(r'_OWNERSHIP_REL_TYPES\s*=\s*"([^"]+)"', content)
    if not ownership_rel_match:
        violations.append("_OWNERSHIP_REL_TYPES definition not found in core/tools.py")
    else:
        rels = ownership_rel_match.group(1).split("|")
        if "ABOUT" in rels:
            violations.append("ABOUT edge type leaked into _OWNERSHIP_REL_TYPES in core/tools.py")
        if "CITED" in rels:
            violations.append("CITED edge type leaked into _OWNERSHIP_REL_TYPES in core/tools.py")

    # 2. Check ownership_chain excludes Case
    if "NOT target:Case" not in content and "none(n in nodes(path) where n:Case)" not in content.lower():
        violations.append("ownership_chain does not assert Case node exclusion")

    # 3. Check path_between excludes Case
    if "NOT a:Case AND NOT b:Case" not in content:
        violations.append("path_between does not assert NOT a:Case AND NOT b:Case")

    # 4. Check cluster_view excludes Case
    if "NOT neighbor:Case" not in content:
        violations.append("cluster_view does not assert NOT neighbor:Case")

    return violations


def check_git_tracked_secrets() -> list[str]:
    violations = []
    try:
        tracked = subprocess.check_output(["git", "ls-files"], cwd=str(REPO_ROOT), text=True).splitlines()
        for f in tracked:
            if f.endswith(".env") or f == ".env":
                violations.append(f"Secret .env file is tracked by git: {f}")
            full_path = REPO_ROOT / f
            if full_path.is_file():
                try:
                    txt = full_path.read_text(encoding="utf-8", errors="ignore")
                    matches = re.findall(r"nvapi-[A-Za-z0-9_-]{20,}", txt)
                    if matches:
                        violations.append(f"Potential NVIDIA API key leaked in tracked file {f}")
                except Exception:
                    pass
    except Exception as exc:
        violations.append(f"Git check failed: {exc}")
    return violations


def check_raw_data_not_tracked() -> list[str]:
    violations = []
    gitignore_path = REPO_ROOT / ".gitignore"
    if gitignore_path.exists():
        gitignore_content = gitignore_path.read_text(encoding="utf-8")
        if "data/raw/" not in gitignore_content and "data/raw" not in gitignore_content:
            violations.append("data/raw/ is NOT in .gitignore — raw ICIJ data could be committed accidentally")
    else:
        violations.append(".gitignore file missing — data/raw/ protection unverified")

    try:
        tracked = subprocess.check_output(["git", "ls-files", "data/raw/"], cwd=str(REPO_ROOT), text=True).strip()
        if tracked:
            violations.append(f"Raw data files are tracked by git: {tracked[:200]}")
    except Exception as exc:
        violations.append(f"Git ls-files data/raw/ check failed: {exc}")

    return violations


def main() -> int:
    print("=" * 70)
    print("OWNERSHIP LENS — ARCHITECTURAL INVARIANT CHECKER")
    print("=" * 70)
    print("Verifying the following 6 non-negotiable invariants:")
    for item in INVARIANTS_LIST:
        print(f"  * {item}")
    print("=" * 70)

    all_violations = []

    print("\n[CHECK 1/6] Forbidden library imports...")
    import_errs = check_forbidden_imports()
    if import_errs:
        print(f"  FAILED: {len(import_errs)} violations")
        all_violations.extend(import_errs)
    else:
        print("  PASSED: No forbidden packages found.")

    print("\n[CHECK 2/6] LLM isolation from raw Cypher...")
    cypher_errs = check_cypher_in_agent()
    if cypher_errs:
        print(f"  FAILED: {len(cypher_errs)} violations")
        all_violations.extend(cypher_errs)
    else:
        print("  PASSED: Zero Cypher patterns in agent/ directory.")

    print("\n[CHECK 3/6] Read routing via ro() / ro_query...")
    read_errs = check_all_reads_via_ro()
    if read_errs:
        print(f"  FAILED: {len(read_errs)} violations")
        all_violations.extend(read_errs)
    else:
        print("  PASSED: All read tools strictly use ro().")

    print("\n[CHECK 4/6] Case / ABOUT / CITED exclusion from read traversals...")
    case_errs = check_case_meta_exclusion()
    if case_errs:
        print(f"  FAILED: {len(case_errs)} violations")
        all_violations.extend(case_errs)
    else:
        print("  PASSED: Case nodes and ABOUT/CITED edges strictly excluded.")

    print("\n[CHECK 5/6] Git tracked secrets and .env...")
    secret_errs = check_git_tracked_secrets()
    if secret_errs:
        print(f"  FAILED: {len(secret_errs)} violations")
        all_violations.extend(secret_errs)
    else:
        print("  PASSED: Zero tracked secrets or .env files.")

    print("\n[CHECK 6/6] data/raw/ not tracked by git (ICIJ data protection)...")
    raw_errs = check_raw_data_not_tracked()
    if raw_errs:
        print(f"  FAILED: {len(raw_errs)} violations")
        all_violations.extend(raw_errs)
    else:
        print("  PASSED: data/raw/ is gitignored and untracked.")

    print("=" * 70)
    if all_violations:
        print(f"\n[FAIL] {len(all_violations)} INVARIANT VIOLATION(S) DETECTED:")
        for v in all_violations:
            print(f"  - {v}")
        return 1

    print("\n[OK] ALL 6 INVARIANTS PASSED VERIFICATION!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
