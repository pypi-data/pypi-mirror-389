"""
Team Management Module

This module provides comprehensive team management functionality including:
- Creating, updating, and deleting teams
- Managing team members
- Team role assignments
- Retrieving teams by workspace
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from ..client.base_client import BaseGraphQLClient


class TeamModule:
    """
    Client for managing teams and team members.
    """

    def __init__(self, client: "BaseGraphQLClient"):
        """
        Initialize the Team module.

        Args:
            client: The base GraphQL client
        """
        self.client = client

    async def _execute_query(self, query: str, variables: dict = None):
        """Execute a GraphQL query using the base client."""
        return await self.client.request(query, variables)

    async def create_team(
        self, name: str, workspace_id: str, token: str
    ) -> Dict[str, Any]:
        """
        Create a new team in a workspace.

        Args:
            name (str): Team name
            workspace_id (str): Workspace ID
            token (str): Authentication token

        Returns:
            dict: Created team information

        Example:
            >>> team = await client.create_team("Dev Team", "workspace-123", token)  # noqa: E501
            >>> print(team['id'])
        """
        try:
            mutation_str = """
                mutation CreateTeam($name: String!, $workspaceID: ID!) {
                    createTeam(name: $name, workspaceID: $workspaceID) {
                        id
                        name
                        status
                        workspaceID
                        createdAt
                        updatedAt
                    }
                }
            """

            variables = {"name": name, "workspaceID": workspace_id}
            result = await self._execute_query(mutation_str, variables)
            return result.get("createTeam")
        except Exception as e:
            print(f"Create team failed: {str(e)}")
            raise

    async def get_team(self, team_id: str, token: str) -> Optional[Dict[str, Any]]:
        """
        Get team details by ID.

        Args:
            team_id (str): Team ID
            token (str): Authentication token

        Returns:
            dict: Team information including members, or None if not found

        Example:
            >>> team = await client.get_team("team-123", token)
            >>> print(team['name'])
        """
        try:
            query_str = """
                query GetTeam($id: ID!) {
                    getTeam(id: $id) {
                        id
                        name
                        status
                        workspaceID
                        createdAt
                        updatedAt
                        users {
                            id
                            email
                            name
                        }
                    }
                }
            """

            variables = {"id": team_id}
            result = await self._execute_query(query_str, variables)
            return result.get("getTeam")
        except Exception as e:
            print(f"Get team failed: {str(e)}")
            return None

    async def get_teams_by_workspace(
        self,
        workspace_id: str,
        token: str,
        items_per_page: Optional[int] = None,
        page: Optional[int] = None,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get all teams in a workspace with pagination and search.

        Args:
            workspace_id (str): Workspace ID
            token (str): Authentication token
            items_per_page (int, optional): Number of items per page
            page (int, optional): Page number
            search (str, optional): Search query

        Returns:
            dict: Response containing count and teams list

        Example:
            >>> result = await client.get_teams_by_workspace(
            ...     "workspace-123",
            ...     token,
            ...     items_per_page=10,
            ...     page=1
            ... )
            >>> print(f"Found {result['count']} teams")
            >>> for team in result['teams']:
            ...     print(team['name'])
        """
        try:
            query_str = """
                query GetTeamsByWorkspace(
                    $workspaceID: ID!
                    $itemsPerPage: Int
                    $page: Int
                    $search: String
                ) {
                    getTeamByWorkspaceID(
                        workspaceID: $workspaceID
                        itemsPerPage: $itemsPerPage
                        page: $page
                        search: $search
                    ) {
                        count
                        teams {
                            id
                            name
                            status
                            workspaceID
                            createdAt
                            updatedAt
                        }
                    }
                }
            """

            variables = {"workspaceID": workspace_id}
            if items_per_page is not None:
                variables["itemsPerPage"] = items_per_page
            if page is not None:
                variables["page"] = page
            if search is not None:
                variables["search"] = search

            result = await self._execute_query(query_str, variables)
            return result.get("getTeamByWorkspaceID", {"count": 0, "teams": []})
        except Exception as e:
            print(f"Get teams by workspace failed: {str(e)}")
            return {"count": 0, "teams": []}

    async def get_team_members(
        self,
        team_id: str,
        token: str,
        items_per_page: Optional[int] = None,
        page: Optional[int] = None,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get all members of a team with pagination and search.

        Args:
            team_id (str): Team ID
            token (str): Authentication token
            items_per_page (int, optional): Number of items per page
            page (int, optional): Page number
            search (str, optional): Search query

        Returns:
            dict: Response containing count and users list

        Example:
            >>> result = await client.get_team_members(
            ...     "team-123",
            ...     token,
            ...     items_per_page=10,
            ...     page=1
            ... )
            >>> print(f"Team has {result['count']} members")
            >>> for user in result['users']:
            ...     print(user['email'])
        """
        try:
            query_str = """
                query GetTeamMembers(
                    $teamID: ID!
                    $itemsPerPage: Int
                    $page: Int
                    $search: String
                ) {
                    getTeamMembers(
                        teamID: $teamID
                        itemsPerPage: $itemsPerPage
                        page: $page
                        search: $search
                    ) {
                        count
                        users {
                            id
                            email
                            name
                            status
                            createdAt
                            updatedAt
                        }
                    }
                }
            """

            variables = {"teamID": team_id}
            if items_per_page is not None:
                variables["itemsPerPage"] = items_per_page
            if page is not None:
                variables["page"] = page
            if search is not None:
                variables["search"] = search

            result = await self._execute_query(query_str, variables)
            return result.get("getTeamMembers", {"count": 0, "users": []})
        except Exception as e:
            print(f"Get team members failed: {str(e)}")
            return {"count": 0, "users": []}

    async def update_team(
        self,
        team_id: str,
        token: str,
        name: Optional[str] = None,
        status: Optional[str] = None,
        workspace_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update team information.

        Args:
            team_id (str): Team ID
            token (str): Authentication token
            name (str, optional): New team name
            status (str, optional): New team status
            workspace_id (str, optional): New workspace ID

        Returns:
            dict: Updated team information

        Example:
            >>> team = await client.update_team(
            ...     "team-123",
            ...     token,
            ...     name="Updated Team Name"
            ... )
        """
        try:
            mutation_str = """
                mutation UpdateTeam($id: ID!, $input: UpdateTeamInput!) {
                    updateTeam(id: $id, input: $input) {
                        id
                        name
                        status
                        workspaceID
                        updatedAt
                    }
                }
            """

            input_data = {}
            if name is not None:
                input_data["name"] = name
            if status is not None:
                input_data["status"] = status
            if workspace_id is not None:
                input_data["workspaceID"] = workspace_id

            variables = {"id": team_id, "input": input_data}
            result = await self._execute_query(mutation_str, variables)
            return result.get("updateTeam")
        except Exception as e:
            print(f"Update team failed: {str(e)}")
            raise

    async def archive_team(self, team_id: str, token: str) -> Dict[str, Any]:
        """
        Archive a team.

        Args:
            team_id (str): Team ID
            token (str): Authentication token

        Returns:
            dict: Archived team information
        """
        try:
            mutation_str = """
                mutation ArchiveTeam($id: ID!) {
                    archiveTeam(id: $id) {
                        id
                        name
                        status
                        updatedAt
                    }
                }
            """

            variables = {"id": team_id}
            result = await self._execute_query(mutation_str, variables)
            return result.get("archiveTeam")
        except Exception as e:
            print(f"Archive team failed: {str(e)}")
            raise

    async def reactivate_team(self, team_id: str, token: str) -> Dict[str, Any]:
        """
        Reactivate an archived team.

        Args:
            team_id (str): Team ID
            token (str): Authentication token

        Returns:
            dict: Reactivated team information
        """
        try:
            mutation_str = """
                mutation ReactivateTeam($id: ID!) {
                    reactivateTeam(id: $id) {
                        id
                        name
                        status
                        updatedAt
                    }
                }
            """

            variables = {"id": team_id}
            result = await self._execute_query(mutation_str, variables)
            return result.get("reactivateTeam")
        except Exception as e:
            print(f"Reactivate team failed: {str(e)}")
            raise

    async def delete_team(self, team_id: str, token: str) -> Dict[str, Any]:
        """
        Delete a team permanently.

        Args:
            team_id (str): Team ID
            token (str): Authentication token

        Returns:
            dict: Deleted team information
        """
        try:
            mutation_str = """
                mutation DeleteTeam($id: ID!) {
                    deleteTeam(id: $id) {
                        id
                        name
                        status
                    }
                }
            """

            variables = {"id": team_id}
            result = await self._execute_query(mutation_str, variables)
            return result.get("deleteTeam")
        except Exception as e:
            print(f"Delete team failed: {str(e)}")
            raise

    async def add_user_to_team(
        self, team_id: str, user_email: str, token: str
    ) -> Dict[str, Any]:
        """
        Add a user to a team.

        Args:
            team_id (str): Team ID
            user_email (str): User email
            token (str): Authentication token

        Returns:
            dict: Updated team information with users

        Example:
            >>> team = await client.add_user_to_team(
            ...     "team-123",
            ...     "user@example.com",
            ...     token
            ... )
        """
        try:
            mutation_str = """
                mutation AddUserToTeam($teamID: ID!, $userEmail: String!) {
                    addUserToTeam(teamID: $teamID, userEmail: $userEmail) {
                        id
                        name
                        status
                        workspaceID
                        users {
                            id
                            email
                            name
                        }
                    }
                }
            """

            variables = {"teamID": team_id, "userEmail": user_email}
            result = await self._execute_query(mutation_str, variables)
            return result.get("addUserToTeam")
        except Exception as e:
            print(f"Add user to team failed: {str(e)}")
            raise

    async def remove_user_from_team(
        self, team_id: str, user_id: str, token: str
    ) -> Dict[str, Any]:
        """
        Remove a user from a team.

        Args:
            team_id (str): Team ID
            user_id (str): User ID
            token (str): Authentication token

        Returns:
            dict: Updated team information with users

        Example:
            >>> team = await client.remove_user_from_team(
            ...     "team-123",
            ...     "user-456",
            ...     token
            ... )
        """
        try:
            mutation_str = """
                mutation RemoveUserFromTeam($teamID: ID!, $userID: ID!) {
                    removeUserFromTeam(teamID: $teamID, userID: $userID) {
                        id
                        name
                        status
                        workspaceID
                        users {
                            id
                            email
                            name
                        }
                    }
                }
            """

            variables = {"teamID": team_id, "userID": user_id}
            result = await self._execute_query(mutation_str, variables)
            return result.get("removeUserFromTeam")
        except Exception as e:
            print(f"Remove user from team failed: {str(e)}")
            raise

    async def assign_role_to_team(
        self, team_id: str, role_id: str, token: str
    ) -> Dict[str, Any]:
        """
        Assign a role to a team.

        Args:
            team_id (str): Team ID
            role_id (str): Role ID
            token (str): Authentication token

        Returns:
            dict: Team role assignment information
        """
        try:
            mutation_str = """
                mutation AssignRoleToTeam($input: AssignTeamRoleInput!) {
                    assignRoleToTeam(input: $input) {
                        id
                        teamId
                        roleId
                        assignedAt
                    }
                }
            """

            variables = {"input": {"teamId": team_id, "roleId": role_id}}
            result = await self._execute_query(mutation_str, variables)
            return result.get("assignRoleToTeam")
        except Exception as e:
            print(f"Assign role to team failed: {str(e)}")
            raise

    async def remove_role_from_team(
        self, team_id: str, role_id: str, token: str
    ) -> bool:
        """
        Remove a role from a team.

        Args:
            team_id (str): Team ID
            role_id (str): Role ID
            token (str): Authentication token

        Returns:
            bool: True if successful
        """
        try:
            mutation_str = """
                mutation RemoveRoleFromTeam($roleId: String!, $teamId: String!) {  # noqa: E501
                    removeRoleFromTeam(roleId: $roleId, teamId: $teamId)
                }
            """

            variables = {"roleId": role_id, "teamId": team_id}
            result = await self._execute_query(mutation_str, variables)
            return result.get("removeRoleFromTeam", False)
        except Exception as e:
            print(f"Remove role from team failed: {str(e)}")
            return False

    async def get_team_roles(self, team_id: str, token: str) -> List[Dict[str, Any]]:
        """
        Get all roles assigned to a team.

        Args:
            team_id (str): Team ID
            token (str): Authentication token

        Returns:
            list: List of team role assignments
        """
        try:
            query_str = """
                query GetTeamRoles($teamId: String!) {
                    getTeamRoles(teamId: $teamId) {
                        id
                        teamId
                        roleId
                        assignedAt
                        role {
                            id
                            name
                            description
                        }
                    }
                }
            """

            variables = {"teamId": team_id}
            result = await self._execute_query(query_str, variables)
            return result.get("getTeamRoles", [])
        except Exception as e:
            print(f"Get team roles failed: {str(e)}")
            return []


# Create convenience functions that use a default client
_default_client = None


def initialize(client: "BaseGraphQLClient"):
    """
    Initialize the default client.

    Args:
        client: The base GraphQL client
    """
    global _default_client
    _default_client = client
