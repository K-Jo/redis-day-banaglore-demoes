CALL db.idx.fulltext.queryNodes('Brewery', '%brew%') yield node
MATCH (node)<-[:BREWED_BY]-(b)<-[:LIKES]-(:Person {pid:26})
WITH node, count(b) as count
RETURN node.name, count ORDER BY count DESC limit 10

CALL db.idx.fulltext.createNodeIndex('Brewery', 'name')

MATH (n:Beer) return n limit 10
