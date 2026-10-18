"""Test suite for automated visual verification of the Network Topology Graph (G2)."""

import pytest

playwright = pytest.importorskip("playwright")
from scripts.verify_graph_visual import run_visual_verification


def test_network_graph_visual_verification():
    passed, report = run_visual_verification()
    assert passed, f"Visual verification assertions failed:\n{report}"

