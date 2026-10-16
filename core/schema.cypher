// core/schema.cypher — FalkorDB schema definitions and indexes.
// FalkorDB Cypher syntax verified against official documentation (16 Oct 2026).

// Range indexes on node_id for O(1) entity lookups
CREATE INDEX FOR (e:Entity) ON (e.node_id);
CREATE INDEX FOR (o:Officer) ON (o.node_id);
CREATE INDEX FOR (i:Intermediary) ON (i.node_id);
CREATE INDEX FOR (a:Address) ON (a.node_id);
CREATE INDEX FOR (x:Other) ON (x.node_id);
CREATE INDEX FOR (c:Case) ON (c.case_id);

// Fulltext indexes on names for resolve_entity tool
CALL db.idx.fulltext.createNodeIndex('Entity', 'name');
CALL db.idx.fulltext.createNodeIndex('Officer', 'name');
CALL db.idx.fulltext.createNodeIndex('Intermediary', 'name');
CALL db.idx.fulltext.createNodeIndex('Address', 'address');
