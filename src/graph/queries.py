"""
Framelink — v3 Schema OpenCypher & Graph Algorithm Queries
Documented queries including 2-4 hop traversals, Conflict node retrieval, and algo.SSpaths / algo.MSpaths
"""

# 2-Hop Traversal: Claim -> NarrativeFrame -> TheoryTopic
TWO_HOP_TRAVERSAL_QUERY = """
MATCH (c:Claim)-[r1:USES_FRAME]->(f:NarrativeFrame)-[r2:BELONGS_TO]->(t:TheoryTopic)
RETURN c, r1, f, r2, t
"""

MULTI_HOP_TRAVERSAL_QUERY = TWO_HOP_TRAVERSAL_QUERY

# 3-Hop Traversal: FactCheck -> CHECKS -> Claim -> MENTIONS -> Entity
THREE_HOP_TRAVERSAL_QUERY = """
MATCH (fc:FactCheck)-[r1:CHECKS]->(c:Claim)-[r2:MENTIONS]->(e:Entity)-[r3:HAS_BROAD_TOPIC]->(bt:BroadTopic)
RETURN fc, r1, c, r2, e, r3, bt
"""

# 4-Hop Traversal: ClaimVariant -> EXPRESSES -> Claim -> CONTRADICTS -> Conflict -> SUPPORTS -> Source
FOUR_HOP_TRAVERSAL_QUERY = """
MATCH (cv:ClaimVariant)-[r1:EXPRESSES]->(c:Claim)-[r2:CONTRADICTS]->(cnf:Conflict)-[r3:SUPPORTS]->(s:Source)
RETURN cv, r1, c, r2, cnf, r3, s
"""

# Conflict Detection Query
CONFLICT_DETECTION_QUERY = """
MATCH (c:Claim)-[r:CONTRADICTS]-(cnf:Conflict)
RETURN c, r, cnf
"""

# Entity Bridge Query
ENTITY_BRIDGE_QUERY = """
MATCH (c1:Claim)-[:MENTIONS]->(e:Entity)<-[:MENTIONS]-(c2:Claim)
RETURN c1, e, c2
"""

# Frame Explorer Query
FRAME_EXPLORER_QUERY = """
MATCH (c:Claim)-[:USES_FRAME]->(f:NarrativeFrame)
RETURN c, f
"""

# Evidence Collector Query
EVIDENCE_COLLECTOR_QUERY = """
MATCH (fc:FactCheck)-[:CHECKS]->(c:Claim)-[:CONTRADICTS]-(cnf:Conflict)-[:SUPPORTS]->(s:Source)
RETURN fc, c, cnf, s
"""

# Temporal Evolution Query
TEMPORAL_EVOLUTION_QUERY = """
MATCH (c1:Claim)-[r:EVOLVED_FROM|SUPERSEDES]->(c2:Claim)
RETURN c1, r, c2
"""

# Statistics OpenCypher Fallback Query
STATISTICS_QUERY = """
MATCH (n)
RETURN labels(n) AS label, count(n) AS count
"""

# Path Explanation Query
PATH_EXPLANATION_QUERY = """
MATCH p = shortestPath((c:Claim {id: $claim_id})-[*..6]-(s:Source {is_root: true}))
RETURN p, [node in nodes(p) | node.confidence_score] AS confidence_scores
"""

# Single-Source Shortest Paths (algo.SSpaths)
SSPATHS_QUERY = """
CALL algo.SSpaths($start_node_id, ['EXPRESSES', 'CHECKS', 'CONTRADICTS', 'SUPPORTS'], {max_depth: 4})
YIELD path, weight
RETURN path, weight
"""

# Multi-Source Shortest Paths (algo.MSpaths)
MSPATHS_QUERY = """
CALL algo.MSpaths($start_node_ids, $target_node_ids, {max_depth: 5})
YIELD path, source, target
RETURN path, source, target
"""
