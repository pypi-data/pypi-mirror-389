# MCP Neo4j Temporal Substrate - Technical Debt Resolution

## Context

On November 2, 2025, we successfully addressed critical context window pollution in the `search_memories` tool by:
1. Adding `limit` parameter with default of 10, max of 50
2. Exposing relevance scores from Neo4j fulltext search
3. Constraining relationship traversal to prevent exponential expansion
4. Deploying as `mcp-neo4j-temporal-substrate` on PyPI

**Remaining Technical Debt:**
- `read_graph()` - Unbounded traversal causing context exhaustion
- `find_memories_by_name()` - Needs same bounded pattern as search_memories

## Architectural Principle

**Temporal Substrate Scale:** This MCP server manages temporal knowledge graphs with hundreds of interconnected nodes forming temporal substrates. Original design assumed toy chatbot memory (dozens of isolated facts). All tools must implement bounded traversal to prevent context window exhaustion.

## Task 1: Remove read_graph Tool

### Rationale
- `read_graph()` returns the ENTIRE graph with no limits
- Fundamentally incompatible with temporal substrate architecture
- At our scale (hundreds of temporal nodes), returns 78k+ tokens
- Cannot be "fixed" without fundamentally changing its purpose
- Deprecated in favor of bounded query tools: `search_memories`, `find_memories_by_name`

### Implementation Steps

1. **Remove from server.py MCP tool definitions**
   - Locate the `@mcp.tool()` decorator for `read_graph`
   - Remove the entire tool definition
   - Keep the underlying `load_graph()` function in neo4j_memory.py for internal use

2. **Update neo4j_memory.py**
   - Keep `load_graph()` function but mark it as internal/deprecated
   - Add docstring warning: "Internal use only. Use search_memories or find_memories_by_name for bounded queries."
   - Do NOT remove the function - it's used by other tools

3. **Add deprecation notice to CHANGELOG.md**
   ```markdown
   ## [0.6.0] - 2025-11-03
   ### Removed
   - `read_graph` tool - unbounded traversal incompatible with large-scale temporal knowledge graphs
   
   ### Migration Guide
   - Use `search_memories` with appropriate query and limit for keyword-based retrieval
   - Use `find_memories_by_name` for specific entity retrieval by name
   - Both tools implement bounded traversal suitable for temporal substrate scale
   ```

## Task 2: Align find_memories_by_name with search_memories Pattern

### Current Implementation Analysis
Currently `find_memories_by_name()` in neo4j_memory.py:
- Takes `names: list[str]` parameter
- Calls `load_graph(names=names)` with no limit
- Returns all relationships for matched entities (unbounded)
- No relevance scoring (doesn't use fulltext search)

### Target Implementation Pattern (from search_memories)

```python
async def search_memories(
    self, 
    query: str, 
    limit: int = 10  # Default 10, max 50 enforced in tool definition
) -> KnowledgeGraph:
    """Search with bounded results and relationship traversal."""
    
    # 1. Get top-N entities by relevance score
    result = await self.driver.execute_query(
        """
        CALL db.index.fulltext.queryNodes('entityIndex', $query)
        YIELD node, score
        RETURN 
            node.name AS name,
            node.type AS type, 
            node.observations AS observations,
            score
        ORDER BY score DESC
        LIMIT $limit
        """,
        query=query,
        limit=limit
    )
    
    # 2. Collect entity names for relationship constraint
    entity_names = [record["name"] for record in result.records]
    
    # 3. Get relationships ONLY between retrieved entities
    rels = await self.driver.execute_query(
        """
        MATCH (source:Entity)-[r]->(target:Entity)
        WHERE source.name IN $entity_names 
          AND target.name IN $entity_names
        RETURN 
            source.name AS source,
            type(r) AS relationType,
            target.name AS target
        """,
        entity_names=entity_names
    )
```

**Key Pattern Elements:**
1. Limit primary entity retrieval (ORDER BY + LIMIT)
2. Collect entity names into list
3. Constrain relationship query with WHERE...IN to only retrieved entities
4. Include score field in Entity model when available

### Implementation Steps for find_memories_by_name

1. **Update Entity model in neo4j_memory.py** (already done for search_memories)
   - Verify `score: float | None = None` field exists
   - No changes needed here

2. **Modify find_memories_by_name in neo4j_memory.py**
   
   Current signature:
   ```python
   async def find_memories_by_name(self, names: list[str]) -> KnowledgeGraph:
   ```
   
   Updated signature:
   ```python
   async def find_memories_by_name(
       self, 
       names: list[str], 
       limit: int = 20  # Higher default than search since names are explicit
   ) -> KnowledgeGraph:
       """
       Find specific entities by exact name match with bounded relationship traversal.
       
       Args:
           names: List of entity names to retrieve (exact match)
           limit: Maximum entities to return if >limit names provided (default 20)
       
       Returns:
           KnowledgeGraph with matched entities and relationships only between them
       """
   ```

3. **Implement bounded retrieval**
   ```python
   # Get entities with name match, applying limit if needed
   result = await self.driver.execute_query(
       """
       MATCH (e:Entity)
       WHERE e.name IN $names
       RETURN 
           e.name AS name,
           e.type AS type,
           e.observations AS observations
       LIMIT $limit
       """,
       names=names,
       limit=limit
   )
   
   entity_names = [record["name"] for record in result.records]
   
   # Get relationships ONLY between retrieved entities
   rels = await self.driver.execute_query(
       """
       MATCH (source:Entity)-[r]->(target:Entity)
       WHERE source.name IN $entity_names 
         AND target.name IN $entity_names
       RETURN 
           source.name AS source,
           type(r) AS relationType,
           target.name AS target
       """,
       entity_names=entity_names
   )
   ```

4. **Update MCP tool definition in server.py**
   
   Find:
   ```python
   @mcp.tool()
   async def find_memories_by_name(names: list[str]) -> str:
   ```
   
   Update to:
   ```python
   @mcp.tool()
   async def find_memories_by_name(
       names: Annotated[list[str], Field(description="List of entity names to find")],
       limit: Annotated[int, Field(default=20, ge=1, le=50, description="Maximum entities to return (1-50, default 20)")]
   ) -> str:
       """
       Find specific entities by exact name match.
       
       Returns entities with specified names and relationships only between 
       the returned entities. Limit constrains results if many names provided.
       
       Use search_memories for keyword-based discovery, find_memories_by_name 
       for retrieving known entities.
       """
       result = await memory_manager.find_memories_by_name(names, limit=limit)
   ```

5. **Test Cases to Verify**
   - Single entity retrieval: 1 entity + its relationships to other retrieved entities only
   - Multiple entities (< limit): All requested entities + relationships between them
   - Many entities (> limit): Top 20 entities + relationships between those 20 only
   - Non-existent entity: Empty result, no error
   - Mixed existing/non-existing: Returns only existing entities

## Task 3: Update README.md

### Changes Required

1. **Update tool list section** 
   - Remove `read_graph` from Query Tools section
   - Update `find_memories_by_name` description to include limit parameter

2. **Update Usage Example section**
   - Add note about bounded traversal design
   - Explain when to use search_memories vs find_memories_by_name

3. **Add Architecture section** (new)
   ```markdown
   ### 🏗️ Architecture Design
   
   This server is designed for **temporal knowledge graphs** at extensive substrate scale:
   - Hundreds of interconnected entities forming temporal chains
   - Dense relationship networks (NEXT_DAY, EVOLVED_FROM, DISCOVERS)
   - Bounded traversal patterns prevent context window exhaustion
   
   **All query tools implement limits:**
   - `search_memories`: Default 10, max 50 entities
   - `find_memories_by_name`: Default 20, max 50 entities
   - Relationships constrained to only returned entities
   
   For toy chatbot memory (dozens of isolated facts), consider the original 
   `mcp-neo4j-memory` package. This fork optimizes for large-scale temporal 
   knowledge graphs where unbounded queries are infeasible.
   ```

4. **Update Components section**
   
   Replace the Query Tools subsection with:
   ```markdown
   #### 🔎 Query Tools
   - `search_memories`
      - Search for entities using fulltext query
      - Input:
        - `query` (string): Search terms matching names, types, observations
        - `limit` (int, optional): Max entities to return (default 10, max 50)
      - Returns: Top-N matching entities by relevance with scores + relationships between them
   
   - `find_memories_by_name`
      - Find specific entities by exact name match
      - Input:
        - `names` (array of strings): Entity names to retrieve
        - `limit` (int, optional): Max entities if many names provided (default 20, max 50)
      - Returns: Specified entities + relationships only between them
   
   **Note:** Both tools implement bounded relationship traversal. Relationships are 
   constrained to only the entities returned by the query, preventing exponential 
   expansion in dense temporal knowledge graphs.
   ```

5. **Add version to changelog**
   - Update version references from 0.4.1 to 0.6.0 in configuration examples to reflect pyproject.toml versioning
   - Add release notes about removed/updated tools

## Implementation Approach

### Recommended Workflow

1. **Create feature branch**
   ```bash
   jj new -m "Remove read_graph, align find_memories_by_name with bounded pattern"
   ```

2. **Implement changes in order:**
   - First: Update find_memories_by_name (both neo4j_memory.py and server.py)
   - Second: Remove read_graph tool from server.py
   - Third: Update README.md
   - Fourth: Add CHANGELOG.md entry

3. **Test thoroughly**
   - Run existing test suite
   - Manual testing with MCP Inspector
   - Verify bounded behavior with large graphs

4. **Version bump**
   - Update pyproject.toml: 0.4.1 → 0.6.0 (minor version for removed tool)
   - Update version in README examples

5. **Build and publish**
   ```bash
   uv build
   uv publish
   ```

## Verification Checklist

- [ ] find_memories_by_name has limit parameter with validation (default 20, max 50)
- [ ] find_memories_by_name uses bounded relationship traversal pattern
- [ ] read_graph tool removed from server.py MCP tool definitions
- [ ] load_graph function kept in neo4j_memory.py with deprecation notice
- [ ] README.md updated with new tool signatures
- [ ] README.md removes read_graph from documentation
- [ ] README.md adds architecture section explaining bounded design
- [ ] CHANGELOG.md documents removal and changes
- [ ] Version bumped to 0.6.0 in pyproject.toml
- [ ] All tests passing
- [ ] Manual verification with MCP Inspector shows bounded behavior

## Rationale Summary

**Why remove read_graph:**
- Fundamentally incompatible with extensive substrate scale
- Returns 78k+ tokens on our temporal knowledge graphs
- Cannot be "fixed" without changing its core purpose (read EVERYTHING)
- Better alternatives exist: search_memories, find_memories_by_name

**Why align find_memories_by_name:**
- Currently calls load_graph with no limit - same problem as read_graph
- Should follow same bounded pattern as search_memories
- Higher default limit (20 vs 10) appropriate since names are explicit
- Maintains utility while preventing context exhaustion

**Architectural consistency:**
All query tools now follow the pattern:
1. Limit primary entity retrieval (explicit LIMIT clause)
2. Collect retrieved entity names
3. Constrain relationships with WHERE...IN to only retrieved entities
4. Return bounded, predictable result sizes

This makes the MCP server suitable for temporal substrates with hundreds of interconnected nodes while maintaining compatibility with simpler use cases.