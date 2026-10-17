"""
scripts/check_invariants.py — Automated verification of project architectural invariants.

Fails if:
1. Forbidden packages imported (pandas, langchain, langgraph, graphiti, graphrag-sdk).
2. Raw Cypher keywords appear in agent/ or prompts.py.
3. Secrets (nvapi-...) or .env files are tracked by git.
4. data/raw/ is not in .gitignore (must never commit raw ICIJ data).
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

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


def check_git_tracked_secrets() -> list[str]:
    violations = []
    try:
        tracked = subprocess.check_output(["git", "ls-files"], cwd=str(REPO_ROOT), text=True).splitlines()
        for f in tracked:
            if f.endswith(".env") or f == ".env":
                violations.append(f"Secret .env file is tracked by git: {f}")
            # Check content of tracked files for live API keys
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
    """Invariant: data/raw/ must be in .gitignore and NEVER tracked by git.
    Raw ICIJ Offshore Leaks CSVs are gitignored to prevent committing personal data.
    """
    violations = []
    gitignore_path = REPO_ROOT / ".gitignore"
    # Check data/raw/ is in .gitignore
    if gitignore_path.exists():
        gitignore_content = gitignore_path.read_text(encoding="utf-8")
        if "data/raw/" not in gitignore_content and "data/raw" not in gitignore_content:
            violations.append("data/raw/ is NOT in .gitignore — raw ICIJ data could be committed accidentally")
    else:
        violations.append(".gitignore file missing — data/raw/ protection unverified")

    # Check that no files in data/raw/ are git-tracked
    try:
        tracked = subprocess.check_output(["git", "ls-files", "data/raw/"], cwd=str(REPO_ROOT), text=True).strip()
        if tracked:
            violations.append(f"Raw data files are tracked by git: {tracked[:200]}")
    except Exception as exc:
        violations.append(f"Git ls-files data/raw/ check failed: {exc}")

    return violations


def main() -> int:
    all_violations = []

    print("Checking Invariant 1: Forbidden library imports...")
    import_errs = check_forbidden_imports()
    all_violations.extend(import_errs)

    print("Checking Invariant 2: LLM isolation from raw Cypher...")
    cypher_errs = check_cypher_in_agent()
    all_violations.extend(cypher_errs)

    print("Checking Invariant 3: Git tracked secrets and .env...")
    secret_errs = check_git_tracked_secrets()
    all_violations.extend(secret_errs)

    print("Checking Invariant 4: data/raw/ not tracked by git (ICIJ data protection)...")
    raw_errs = check_raw_data_not_tracked()
    all_violations.extend(raw_errs)

    if all_violations:
        print("\n[FAIL] INVARIANT CHECK FAILED:")
        for v in all_violations:
            print(f"  * {v}")
        return 1

    print("\n[OK] ALL INVARIANTS PASSED!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
