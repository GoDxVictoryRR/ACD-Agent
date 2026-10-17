from core.db import ro
from core.tools import cluster_view

# Let's inspect some entities in ownership graph
# We want:
# 1. An entity with high betweenness in its scratch graph (HUB_CENTRALITY)
# 2. An entity that shares a community with another entity (which we can put in watchlist)
# but has NO path within depth 1 (or depth 2) or no direct path.


def find_high_betweenness():
    # Find entities with multiple officers/addresses that create local cycles/bridges
    q = """
    MATCH (e:Entity)-[:OFFICER_OF]-(o:Officer)-[:OFFICER_OF]-(other:Entity)
    WITH e, count(DISTINCT other) AS other_count
    WHERE other_count >= 5 AND other_count <= 20
    RETURN e.node_id AS id, e.name AS name, other_count
    LIMIT 10
    """
    res = ro("ownership", q)
    print("Candidates for cluster_view centrality:")
    for r in res.get("rows", []):
        eid, name, _cnt = r[0], r[1], r[2]
        cv = cluster_view(eid, max_depth=2)
        if cv.status == "ok" and cv.data:
            top_bw = cv.data[0].get("top_betweenness", [])
            print(f"Entity: {name} ({eid}) -> top_bw: {top_bw[:3]}")


if __name__ == "__main__":
    find_high_betweenness()
