import logging
from typing import Any, Dict, List

from neo4j import AsyncDriver, RoutingControl
from pydantic import BaseModel, Field


# Set up logging
logger = logging.getLogger('mcp_neo4j_memory')
logger.setLevel(logging.INFO)

# Models for our knowledge graph
class Entity(BaseModel):
    """Represents a memory entity in the knowledge graph.
    
    Example:
    {
        "name": "John Smith",
        "type": "person", 
        "observations": ["Works at Neo4j", "Lives in San Francisco", "Expert in graph databases"],
        "score": 5.42
    }
    """
    name: str = Field(
        description="Unique identifier/name for the entity. Should be descriptive and specific.",
        min_length=1,
        examples=["John Smith", "Neo4j Inc", "San Francisco"]
    )
    type: str = Field(
        description="Category or classification of the entity. Common types: 'person', 'company', 'location', 'concept', 'event'",
        min_length=1,
        examples=["person", "company", "location", "concept", "event"]
    )
    observations: List[str] = Field(
        description="List of facts, observations, or notes about this entity. Each observation should be a complete, standalone fact.",
        examples=[["Works at Neo4j", "Lives in San Francisco"], ["Headquartered in Sweden", "Graph database company"]]
    )
    score: float | None = Field(
        default=None,
        description="Relevance score from fulltext search (higher = better match). Only present when entity comes from search results."
    )

class Relation(BaseModel):
    """Represents a relationship between two entities in the knowledge graph.
    
    Example:
    {
        "source": "John Smith",
        "target": "Neo4j Inc", 
        "relationType": "WORKS_AT"
    }
    """
    source: str = Field(
        description="Name of the source entity (must match an existing entity name exactly)",
        min_length=1,
        examples=["John Smith", "Neo4j Inc"]
    )
    target: str = Field(
        description="Name of the target entity (must match an existing entity name exactly)",
        min_length=1, 
        examples=["Neo4j Inc", "San Francisco"]
    )
    relationType: str = Field(
        description="Type of relationship between source and target. Use descriptive, uppercase names with underscores.",
        min_length=1,
        examples=["WORKS_AT", "LIVES_IN", "MANAGES", "COLLABORATES_WITH", "LOCATED_IN"]
    )

class KnowledgeGraph(BaseModel):
    """Complete knowledge graph containing entities and their relationships."""
    entities: List[Entity] = Field(
        description="List of all entities in the knowledge graph",
        default=[]
    )
    relations: List[Relation] = Field(
        description="List of all relationships between entities",
        default=[]
    )

class ObservationAddition(BaseModel):
    """Request to add new observations to an existing entity.
    
    Example:
    {
        "entityName": "John Smith",
        "observations": ["Recently promoted to Senior Engineer", "Speaks fluent German"]
    }
    """
    entityName: str = Field(
        description="Exact name of the existing entity to add observations to",
        min_length=1,
        examples=["John Smith", "Neo4j Inc"]
    )
    observations: List[str] = Field(
        description="New observations/facts to add to the entity. Each should be unique and informative.",
        min_length=1
    )

class ObservationDeletion(BaseModel):
    """Request to delete specific observations from an existing entity.
    
    Example:
    {
        "entityName": "John Smith", 
        "observations": ["Old job title", "Outdated contact info"]
    }
    """
    entityName: str = Field(
        description="Exact name of the existing entity to remove observations from",
        min_length=1,
        examples=["John Smith", "Neo4j Inc"]
    )
    observations: List[str] = Field(
        description="Exact observation texts to delete from the entity (must match existing observations exactly)",
        min_length=1
    )

class Neo4jMemory:
    def __init__(self, neo4j_driver: AsyncDriver):
        self.driver = neo4j_driver

    async def create_fulltext_index(self):
        """Create a fulltext search index for entities if it doesn't exist."""
        try:
            query = "CREATE FULLTEXT INDEX search IF NOT EXISTS FOR (m:Memory) ON EACH [m.name, m.type, m.observations];"
            await self.driver.execute_query(query, routing_control=RoutingControl.WRITE)
            logger.info("Created fulltext search index")
        except Exception as e:
            # Index might already exist, which is fine
            logger.debug(f"Fulltext index creation: {e}")

    async def load_graph(self, filter_query: str = "*", limit: int | None = None):
        """Load the knowledge graph from Neo4j with optional result limiting.

        INTERNAL USE ONLY. This function is used internally by search_memories.
        For external queries, use search_memories or find_memories_by_name for bounded results.

        Args:
            filter_query: Fulltext search query
            limit: Maximum number of entities to return (ordered by relevance score)
        """
        logger.info(f"Loading knowledge graph from Neo4j (limit={limit})")
        
        limit_clause = f"LIMIT {limit}" if limit else ""
        
        query = f"""
            CALL db.index.fulltext.queryNodes('search', $filter) YIELD node as entity, score
            WITH entity, score 
            ORDER BY score DESC 
            {limit_clause}
            WITH collect({{ent: entity, score: score}}) as scored_entities
            UNWIND scored_entities as se
            WITH se.ent as entity, se.score as score, [x in scored_entities | x.ent] as entity_list
            OPTIONAL MATCH (entity)-[r]-(other)
            WHERE other IN entity_list
            RETURN collect(distinct {{
                name: entity.name, 
                type: entity.type, 
                observations: entity.observations,
                score: score
            }}) as nodes,
            collect(distinct {{
                source: startNode(r).name, 
                target: endNode(r).name, 
                relationType: type(r)
            }}) as relations
        """
        
        result = await self.driver.execute_query(query, {"filter": filter_query}, routing_control=RoutingControl.READ)
        
        if not result.records:
            return KnowledgeGraph(entities=[], relations=[])
        
        record = result.records[0]
        nodes = record.get('nodes', list())
        rels = record.get('relations', list())
        
        entities = [
            Entity(
                name=node['name'],
                type=node['type'],
                observations=node.get('observations', list()),
                score=node.get('score')
            )
            for node in nodes if node.get('name')
        ]
        
        relations = [
            Relation(
                source=rel['source'],
                target=rel['target'],
                relationType=rel['relationType']
            )
            for rel in rels if rel.get('relationType')
        ]
        
        logger.debug(f"Loaded {len(entities)} entities and {len(relations)} relations")
        
        return KnowledgeGraph(entities=entities, relations=relations)

    async def create_entities(self, entities: List[Entity]) -> List[Entity]:
        """Create multiple new entities in the knowledge graph."""
        logger.info(f"Creating {len(entities)} entities")
        for entity in entities:
            query = f"""
            WITH $entity as entity
            MERGE (e:Memory {{ name: entity.name }})
            SET e += entity {{ .type, .observations }}
            SET e:`{entity.type}`
            """
            await self.driver.execute_query(query, {"entity": entity.model_dump()}, routing_control=RoutingControl.WRITE)

        return entities

    async def create_relations(self, relations: List[Relation]) -> List[Relation]:
        """Create multiple new relations between entities."""
        logger.info(f"Creating {len(relations)} relations")
        for relation in relations:
            query = f"""
            WITH $relation as relation
            MATCH (from:Memory),(to:Memory)
            WHERE from.name = relation.source
            AND  to.name = relation.target
            MERGE (from)-[r:`{relation.relationType}`]->(to)
            """
            
            await self.driver.execute_query(
                query, 
                {"relation": relation.model_dump()},
                routing_control=RoutingControl.WRITE
            )

        return relations

    async def add_observations(self, observations: List[ObservationAddition]) -> List[Dict[str, Any]]:
        """Add new observations to existing entities."""
        logger.info(f"Adding observations to {len(observations)} entities")
        query = """
        UNWIND $observations as obs  
        MATCH (e:Memory { name: obs.entityName })
        WITH e, [o in obs.observations WHERE NOT o IN e.observations] as new
        SET e.observations = coalesce(e.observations,[]) + new
        RETURN e.name as name, new
        """
            
        result = await self.driver.execute_query(
            query, 
            {"observations": [obs.model_dump() for obs in observations]},
            routing_control=RoutingControl.WRITE
        )

        results = [{"entityName": record.get("name"), "addedObservations": record.get("new")} for record in result.records]
        return results

    async def delete_entities(self, entity_names: List[str]) -> None:
        """Delete multiple entities and their associated relations."""
        logger.info(f"Deleting {len(entity_names)} entities")
        query = """
        UNWIND $entities as name
        MATCH (e:Memory { name: name })
        DETACH DELETE e
        """
        
        await self.driver.execute_query(query, {"entities": entity_names}, routing_control=RoutingControl.WRITE)
        logger.info(f"Successfully deleted {len(entity_names)} entities")

    async def delete_observations(self, deletions: List[ObservationDeletion]) -> None:
        """Delete specific observations from entities."""
        logger.info(f"Deleting observations from {len(deletions)} entities")
        query = """
        UNWIND $deletions as d  
        MATCH (e:Memory { name: d.entityName })
        SET e.observations = [o in coalesce(e.observations,[]) WHERE NOT o IN d.observations]
        """
        await self.driver.execute_query(
            query, 
            {"deletions": [deletion.model_dump() for deletion in deletions]},
            routing_control=RoutingControl.WRITE
        )
        logger.info(f"Successfully deleted observations from {len(deletions)} entities")

    async def delete_relations(self, relations: List[Relation]) -> None:
        """Delete multiple relations from the graph."""
        logger.info(f"Deleting {len(relations)} relations")
        for relation in relations:
            query = f"""
            WITH $relation as relation
            MATCH (source:Memory)-[r:`{relation.relationType}`]->(target:Memory)
            WHERE source.name = relation.source
            AND target.name = relation.target
            DELETE r
            """
            await self.driver.execute_query(
                query, 
                {"relation": relation.model_dump()},
                routing_control=RoutingControl.WRITE
            )
        logger.info(f"Successfully deleted {len(relations)} relations")

    async def read_graph(self) -> KnowledgeGraph:
        """Read the entire knowledge graph.

        DEPRECATED: This function returns unbounded results and is incompatible with
        large-scale temporal knowledge graphs. Use search_memories or find_memories_by_name
        with appropriate limits instead.

        Kept for internal use only.
        """
        return await self.load_graph()

    async def search_memories(self, query: str, limit: int = 10) -> KnowledgeGraph:
        """Search for memories based on a query with Fulltext Search.
        
        Args:
            query: Search query string
            limit: Maximum number of entities to return (default 10)
        """
        logger.info(f"Searching for memories with query: '{query}' (limit={limit})")
        return await self.load_graph(query, limit=limit)

    async def find_memories_by_name(self, names: List[str], limit: int = 20) -> KnowledgeGraph:
        """Find specific memories by their names with bounded relationship traversal.

        Args:
            names: List of entity names to retrieve (exact match)
            limit: Maximum entities to return if >limit names provided (default 20)

        Returns:
            KnowledgeGraph with matched entities and relationships only between them
        """
        logger.info(f"Finding {len(names)} memories by name (limit={limit})")

        # Get entities with name match, applying limit if needed
        query = """
        MATCH (e:Memory)
        WHERE e.name IN $names
        RETURN  e.name as name,
                e.type as type,
                e.observations as observations
        LIMIT $limit
        """
        result_nodes = await self.driver.execute_query(
            query,
            {"names": names, "limit": limit},
            routing_control=RoutingControl.READ
        )

        entities: list[Entity] = list()
        entity_names: list[str] = list()

        for record in result_nodes.records:
            entities.append(Entity(
                name=record['name'],
                type=record['type'],
                observations=record.get('observations', list())
            ))
            entity_names.append(record['name'])

        # Get relations ONLY between retrieved entities (bounded traversal)
        relations: list[Relation] = list()
        if entity_names:
            query = """
            MATCH (source:Memory)-[r]->(target:Memory)
            WHERE source.name IN $entity_names
              AND target.name IN $entity_names
            RETURN  source.name as source,
                    target.name as target,
                    type(r) as relationType
            """
            result_relations = await self.driver.execute_query(
                query,
                {"entity_names": entity_names},
                routing_control=RoutingControl.READ
            )
            for record in result_relations.records:
                relations.append(Relation(
                    source=record["source"],
                    target=record["target"],
                    relationType=record["relationType"]
                ))

        logger.info(f"Found {len(entities)} entities and {len(relations)} relations")
        return KnowledgeGraph(entities=entities, relations=relations)