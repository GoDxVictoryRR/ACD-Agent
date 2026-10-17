"""
scripts/test_clean_clone.py — Test clean clone in a fresh temp directory:
1. Export tracked git files into a clean temporary directory.
2. Verify untracked data/raw/ is NOT present.
3. Verify seed loads from committed data/seed/icij/ files.
4. Run smoke test on the clean clone.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

print("=" * 70)
print("RUNNING CLEAN-CLONE VERIFICATION IN TEMPORARY DIRECTORY")
print("=" * 70)

temp_dir = Path(tempfile.mkdtemp(prefix="clean_clone_test_"))
print(f"Temporary clone target: {temp_dir}")

try:
    # 1. Export only git-tracked files (clean clone simulation)
    print("\n[STEP 1] Exporting tracked git files...")
    # Use git archive to tar and extract
    archive_tar = temp_dir / "repo.tar"
    subprocess.run(["git", "archive", "--format=tar", "-o", str(archive_tar), "HEAD"], cwd=REPO_ROOT, check=True)
    subprocess.run(["tar", "-xf", str(archive_tar)], cwd=temp_dir, check=True)
    archive_tar.unlink()
    print("  Tracked files exported successfully.")

    # 2. Verify data/raw/ does NOT exist in clean clone
    raw_dir = temp_dir / "data" / "raw"
    assert not raw_dir.exists(), f"ERROR: data/raw/ was exported into clean clone: {raw_dir}"
    print("  PASS: data/raw/ is NOT present in clean clone.")

    # 3. Verify committed seed files exist
    seed_icij = temp_dir / "data" / "seed" / "icij"
    assert seed_icij.exists(), f"ERROR: data/seed/icij/ missing: {seed_icij}"
    assert (seed_icij / "nodes-entities.csv").exists()
    assert (seed_icij / "relationships.csv").exists()
    print("  PASS: Committed seed files exist in data/seed/icij/.")

    # 4. Copy .env with localhost DB and NO_LLM=1 for clean smoke test
    env_content = (
        "DATA_SOURCE=icij\n"
        "FALKORDB_HOST=localhost\n"
        "FALKORDB_PORT=6379\n"
        "GRAPH_NAME=ownership\n"
        "NO_LLM=1\n"
    )
    (temp_dir / ".env").write_text(env_content, encoding="utf-8")

    # 5. Run smoke test using existing venv
    print("\n[STEP 2] Running smoke tests against clean clone...")
    python_exe = sys.executable
    smoke_res = subprocess.run(
        [python_exe, "-m", "pytest", "-v", "tests/test_smoke.py"],
        cwd=temp_dir,
        capture_output=True,
        text=True,
    )
    print(smoke_res.stdout)
    assert smoke_res.returncode == 0, f"Smoke test failed on clean clone:\n{smoke_res.stderr}"
    print("  PASS: test_smoke.py succeeded on clean clone.")

    # 6. Run loader verification on clean clone
    print("\n[STEP 3] Testing ensure_seed on clean clone...")
    load_res = subprocess.run(
        [python_exe, "-c", "from data.load import ensure_seed; print('ensure_seed result:', ensure_seed('ownership'))"],
        cwd=temp_dir,
        capture_output=True,
        text=True,
    )
    print(load_res.stdout)
    assert load_res.returncode == 0, f"ensure_seed failed on clean clone:\n{load_res.stderr}"
    print("  PASS: ensure_seed succeeded using committed seed files.")

    print("\nCLEAN-CLONE VERIFICATION: ALL STEPS PASSED!")

finally:
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)
    print(f"Cleaned up temporary directory {temp_dir}.")
