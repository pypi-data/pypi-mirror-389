"""
Graph Client for Bigconsole SDK.

Provides access to graph and relationship management functionality including
entity relationships, dependency graphs, and network analysis.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from ..client.base_client import BaseGraphQLClient


class GraphModule:
    """
    Client for managing graphs and entity relationships.

    Provides methods to query relationships, build dependency graphs,
    and analyze network connections with proper authentication and error handling.
    """

    def __init__(self, client: "BaseGraphQLClient"):
        """
        Initialize the Graph module.

        Args:
            client: The base GraphQL client
        """
        self.client = client

    async def _execute_query(self, query: str, variables: dict = None):
        """Execute a GraphQL query using the base client."""
        return await self.client.request(query, variables or {})

    async def get_entity_relationships(
        self, entity_id: str, entity_type: str, relationship_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all relationships for a specific entity.

        Args:
            entity_id: The ID of the entity
            entity_type: The type of entity ("user", "workspace", "project", "resource")
            relationship_type: Optional filter by relationship type

        Returns:
            List[Dict[str, Any]]: List of relationships
        """
        query = """
            query GetEntityRelationships($entityId: ID!, $entityType: String!, $relationshipType: String) {  # noqa: E501
                getEntityRelationships(entityId: $entityId, entityType: $entityType, relationshipType: $relationshipType) {  # noqa: E501
                    id
                    sourceId
                    sourceType
                    targetId
                    targetType
                    relationshipType
                    metadata
                    createdAt
                }
            }
        """
        variables = {
            "entityId": entity_id,
            "entityType": entity_type,
            "relationshipType": relationship_type,
        }
        result = await self._execute_query(query, variables)
        return result.get("getEntityRelationships", [])

    async def create_relationship(
        self,
        source_id: str,
        source_type: str,
        target_id: str,
        target_type: str,
        relationship_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a relationship between two entities.

        Args:
            source_id: The ID of the source entity
            source_type: The type of source entity
            target_id: The ID of the target entity
            target_type: The type of target entity
            relationship_type: The type of relationship (e.g., "depends_on", "contains", "owned_by")  # noqa: E501
            metadata: Optional metadata for the relationship

        Returns:
            Dict[str, Any]: Created relationship details
        """
        mutation = """
            mutation CreateRelationship($input: CreateRelationshipInput!) {
                createRelationship(input: $input) {
                    id
                    sourceId
                    sourceType
                    targetId
                    targetType
                    relationshipType
                    metadata
                    createdAt
                }
            }
        """
        input_data = {
            "sourceId": source_id,
            "sourceType": source_type,
            "targetId": target_id,
            "targetType": target_type,
            "relationshipType": relationship_type,
        }
        if metadata:
            input_data["metadata"] = metadata

        result = await self._execute_query(mutation, {"input": input_data})
        return result.get("createRelationship", {})

    async def delete_relationship(self, relationship_id: str) -> bool:
        """
        Delete a relationship.

        Args:
            relationship_id: The ID of the relationship to delete

        Returns:
            bool: True if relationship was deleted successfully
        """
        mutation = """
            mutation DeleteRelationship($id: ID!) {
                deleteRelationship(id: $id)
            }
        """
        result = await self._execute_query(mutation, {"id": relationship_id})
        return result.get("deleteRelationship", False)

    async def get_dependency_graph(
        self, entity_id: str, entity_type: str, max_depth: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get the dependency graph for an entity.

        Args:
            entity_id: The ID of the entity
            entity_type: The type of entity
            max_depth: Optional maximum depth to traverse

        Returns:
            Dict[str, Any]: Dependency graph with nodes and edges
        """
        query = """
            query GetDependencyGraph($entityId: ID!, $entityType: String!, $maxDepth: Int) {  # noqa: E501
                getDependencyGraph(entityId: $entityId, entityType: $entityType, maxDepth: $maxDepth) {  # noqa: E501
                    rootEntity {
                        id
                        type
                        name
                    }
                    nodes {
                        id
                        type
                        name
                        depth
                    }
                    edges {
                        sourceId
                        targetId
                        relationshipType
                    }
                }
            }
        """
        variables = {"entityId": entity_id, "entityType": entity_type, "maxDepth": max_depth}  # noqa: E501
        result = await self._execute_query(query, variables)
        return result.get("getDependencyGraph", {})

    async def get_reverse_dependencies(
        self, entity_id: str, entity_type: str
    ) -> List[Dict[str, Any]]:
        """
        Get entities that depend on the specified entity.

        Args:
            entity_id: The ID of the entity
            entity_type: The type of entity

        Returns:
            List[Dict[str, Any]]: List of dependent entities
        """
        query = """
            query GetReverseDependencies($entityId: ID!, $entityType: String!) {
                getReverseDependencies(entityId: $entityId, entityType: $entityType) {
                    id
                    type
                    name
                    relationshipType
                }
            }
        """
        variables = {"entityId": entity_id, "entityType": entity_type}
        result = await self._execute_query(query, variables)
        return result.get("getReverseDependencies", [])

    async def find_path(
        self, source_id: str, target_id: str, entity_type: str
    ) -> List[Dict[str, Any]]:
        """
        Find the shortest path between two entities.

        Args:
            source_id: The ID of the source entity
            target_id: The ID of the target entity
            entity_type: The type of entities

        Returns:
            List[Dict[str, Any]]: List of entities forming the path
        """
        query = """
            query FindPath($sourceId: ID!, $targetId: ID!, $entityType: String!) {
                findPath(sourceId: $sourceId, targetId: $targetId, entityType: $entityType) {  # noqa: E501
                    path {
                        id
                        type
                        name
                    }
                    distance
                }
            }
        """
        variables = {"sourceId": source_id, "targetId": target_id, "entityType": entity_type}  # noqa: E501
        result = await self._execute_query(query, variables)
        return result.get("findPath", {})

    async def get_connected_entities(
        self, entity_id: str, entity_type: str, connection_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all entities connected to the specified entity.

        Args:
            entity_id: The ID of the entity
            entity_type: The type of entity
            connection_type: Optional filter by connection type

        Returns:
            List[Dict[str, Any]]: List of connected entities
        """
        query = """
            query GetConnectedEntities($entityId: ID!, $entityType: String!, $connectionType: String) {  # noqa: E501
                getConnectedEntities(entityId: $entityId, entityType: $entityType, connectionType: $connectionType) {  # noqa: E501
                    id
                    type
                    name
                    connectionType
                    connectionStrength
                }
            }
        """
        variables = {
            "entityId": entity_id,
            "entityType": entity_type,
            "connectionType": connection_type,
        }
        result = await self._execute_query(query, variables)
        return result.get("getConnectedEntities", [])

    async def analyze_network(self, workspace_id: str, entity_type: str) -> Dict[str, Any]:  # noqa: E501
        """
        Analyze the network structure for a workspace.

        Args:
            workspace_id: The ID of the workspace
            entity_type: The type of entities to analyze

        Returns:
            Dict[str, Any]: Network analysis metrics
        """
        query = """
            query AnalyzeNetwork($workspaceId: ID!, $entityType: String!) {
                analyzeNetwork(workspaceId: $workspaceId, entityType: $entityType) {
                    totalNodes
                    totalEdges
                    connectedComponents
                    averageDegree
                    maxDegree
                    density
                    centralNodes {
                        id
                        name
                        centrality
                    }
                }
            }
        """
        variables = {"workspaceId": workspace_id, "entityType": entity_type}
        result = await self._execute_query(query, variables)
        return result.get("analyzeNetwork", {})

    async def get_subgraph(
        self, entity_ids: List[str], include_relationships: Optional[bool] = True
    ) -> Dict[str, Any]:
        """
        Get a subgraph containing the specified entities.

        Args:
            entity_ids: List of entity IDs to include
            include_relationships: Whether to include relationships between entities

        Returns:
            Dict[str, Any]: Subgraph with nodes and edges
        """
        query = """
            query GetSubgraph($entityIds: [ID!]!, $includeRelationships: Boolean) {
                getSubgraph(entityIds: $entityIds, includeRelationships: $includeRelationships) {  # noqa: E501
                    nodes {
                        id
                        type
                        name
                        metadata
                    }
                    edges {
                        sourceId
                        targetId
                        relationshipType
                    }
                }
            }
        """
        variables = {"entityIds": entity_ids, "includeRelationships": include_relationships}  # noqa: E501
        result = await self._execute_query(query, variables)
        return result.get("getSubgraph", {})

    async def detect_cycles(self, workspace_id: str, entity_type: str) -> List[List[str]]:  # noqa: E501
        """
        Detect circular dependencies in the graph.

        Args:
            workspace_id: The ID of the workspace
            entity_type: The type of entities to check

        Returns:
            List[List[str]]: List of cycles, where each cycle is a list of entity IDs
        """
        query = """
            query DetectCycles($workspaceId: ID!, $entityType: String!) {
                detectCycles(workspaceId: $workspaceId, entityType: $entityType) {
                    cycles {
                        entityIds
                        entityNames
                    }
                }
            }
        """
        variables = {"workspaceId": workspace_id, "entityType": entity_type}
        result = await self._execute_query(query, variables)
        cycles_data = result.get("detectCycles", {}).get("cycles", [])
        return [cycle.get("entityIds", []) for cycle in cycles_data]

    async def get_entity_hierarchy(
        self, root_id: str, entity_type: str, max_depth: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get the hierarchical structure starting from a root entity.

        Args:
            root_id: The ID of the root entity
            entity_type: The type of entity
            max_depth: Optional maximum depth to traverse

        Returns:
            Dict[str, Any]: Hierarchical tree structure
        """
        query = """
            query GetEntityHierarchy($rootId: ID!, $entityType: String!, $maxDepth: Int) {  # noqa: E501
                getEntityHierarchy(rootId: $rootId, entityType: $entityType, maxDepth: $maxDepth) {  # noqa: E501
                    root {
                        id
                        type
                        name
                    }
                    children {
                        id
                        type
                        name
                        parentId
                        depth
                        children
                    }
                }
            }
        """
        variables = {"rootId": root_id, "entityType": entity_type, "maxDepth": max_depth}  # noqa: E501
        result = await self._execute_query(query, variables)
        return result.get("getEntityHierarchy", {})
