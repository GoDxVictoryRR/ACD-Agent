import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from core.db import ro

print("=== Probing Algorithms on FalkorDB ===")

# 1. PageRank
try:
    q_pr = "CALL algo.pageRank('Entity', null) YIELD node, score RETURN min(score), percentileCont(score, 0.95), percentileCont(score, 0.99), max(score)"
    res_pr = ro("ownership", q_pr)
    print("PageRank Entity:", res_pr["rows"])
except Exception as e:
    print("PageRank error:", e)

# 2. Betweenness
try:
    q_bw = "CALL algo.betweenness({nodeLabels:['Entity'], relationshipTypes:['SAME_AS', 'SAME_COMPANY_AS', 'CONNECTED_TO'], samplingSize:32, samplingSeed:42}) YIELD node, score RETURN min(score), percentileCont(score, 0.95), max(score)"
    res_bw = ro("ownership", q_bw)
    print("Betweenness Entity:", res_bw["rows"])
except Exception as e:
    print("Betweenness error:", e)

# 3. WCC
try:
    q_wcc = "CALL algo.wcc({nodeLabels:['Entity'], relationshipTypes:['SAME_AS', 'SAME_COMPANY_AS', 'CONNECTED_TO']}) YIELD node, componentId RETURN count(DISTINCT componentId)"
    res_wcc = ro("ownership", q_wcc)
    print("WCC Entity components count:", res_wcc["rows"])
except Exception as e:
    print("WCC error:", e)

# 4. Label Propagation
try:
    q_lp = "CALL algo.labelPropagation({nodeLabels:['Entity'], relationshipTypes:['SAME_AS', 'SAME_COMPANY_AS', 'CONNECTED_TO'], maxIterations:10}) YIELD node, communityId RETURN count(DISTINCT communityId)"
    res_lp = ro("ownership", q_lp)
    print("Label Propagation Entity communities count:", res_lp["rows"])
except Exception as e:
    print("Label Propagation error:", e)
