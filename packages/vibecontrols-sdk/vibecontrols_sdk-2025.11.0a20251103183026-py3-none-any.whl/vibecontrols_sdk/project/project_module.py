"""
Project Client for Vibecontrols SDK.

Provides access to project management functionality including creating,
updating, archiving, and managing projects and project members.
"""

from typing import TYPE_CHECKING, List, Optional, TypedDict

if TYPE_CHECKING:
    from ..client.base_client import BaseGraphQLClient

# Type definitions for Project system


class CreateProjectInput(TypedDict):
    name: str


class EditProjectInput(TypedDict):
    id: str
    name: str


class RemoveProjectMemberInput(TypedDict):
    projectID: str
    userID: str
    id: str


class UpdateProjectMemberRoleInput(TypedDict):
    projectID: str
    userID: str
    role: str


class User(TypedDict):
    id: str
    name: Optional[str]
    email: str


class ProjectMember(TypedDict):
    id: str
    projectID: str
    userID: str
    project: Optional["Project"]
    user: Optional[User]
    createdAt: Optional[str]
    role: Optional[str]


class Project(TypedDict):
    id: str
    name: str
    workspaceID: str
    userID: str
    key: str
    createdAt: Optional[str]
    archived: bool
    projectMembers: Optional[List[ProjectMember]]


class WorkspaceProjects(TypedDict):
    workspaceID: str
    projects: List[Project]


class ProjectModule:
    """
    Client for managing projects in the Workspaces platform.

    Provides methods to create, update, retrieve, archive, and manage projects
    and their members with proper authentication and error handling.
    """

    def __init__(self, client: "BaseGraphQLClient"):
        """
        Initialize the Project module.

        Args:
            client: The base GraphQL client
        """
        self.client = client

    async def _execute_query(self, query: str, variables: dict = None):
        """Execute a GraphQL query using the base client."""
        return await self.client.request(query, variables)

    # Project Query Operations
    async def get_project(self, project_id: str, token: str) -> Optional[Project]:
        """
        Retrieves a specific project by ID.

        Args:
            project_id (str): Project ID
            token (str): Authentication token

        Returns:
            Optional[Project]: Project details or None if not found
        """
        try:
            query_str = """
                query GetProject($id: ID!) {
                    getProject(id: $id) {
                        id
                        name
                        workspaceID
                        userID
                        key
                        createdAt
                        archived
                        projectMembers {
                            id
                            projectID
                            userID
                            user {
                                id
                                name
                                email
                            }
                            createdAt
                            role
                        }
                    }
                }
            """

            variables = {"id": project_id}

            result = await self._execute_query(query_str, variables)
            return result.get("getProject")
        except Exception as e:
            print(f"Get project failed: {str(e)}")
            return None

    async def get_workspace_projects(
        self, workspace_ids: List[str], token: str
    ) -> List[WorkspaceProjects]:
        """
        Retrieves all projects for given workspace IDs.

        Args:
            workspace_ids (List[str]): List of workspace IDs
            token (str): Authentication token

        Returns:
            List[WorkspaceProjects]: List of workspace projects
        """
        try:
            query_str = """
                query GetWorkspaceProjects($workspaceIDs: [ID!]) {
                    getWorkspaceProjects(workspaceIDs: $workspaceIDs) {
                        workspaceID
                        projects {
                            id
                            name
                            workspaceID
                            userID
                            key
                            createdAt
                            archived
                            projectMembers {
                                id
                                projectID
                                userID
                                role
                                createdAt
                            }
                        }
                    }
                }
            """

            variables = {"workspaceIDs": workspace_ids}

            result = await self._execute_query(query_str, variables)
            return result.get("getWorkspaceProjects", [])
        except Exception as e:
            print(f"Get workspace projects failed: {str(e)}")
            return []

    # Project Mutation Operations
    async def create_project(self, name: str, token: str) -> Optional[Project]:
        """
        Creates a new project.

        Args:
            name (str): Project name
            token (str): Authentication token

        Returns:
            Optional[Project]: The created project or None if failed
        """
        try:
            mutation_str = """
                mutation CreateProject($input: createProjectInput!) {
                    createProject(input: $input) {
                        id
                        name
                        workspaceID
                        userID
                        key
                        createdAt
                        archived
                    }
                }
            """

            input_data = {"name": name}
            variables = {"input": input_data}

            result = await self._execute_query(mutation_str, variables)
            return result.get("createProject")
        except Exception as e:
            print(f"Create project failed: {str(e)}")
            return None

    async def edit_project(self, project_id: str, name: str, token: str) -> Optional[Project]:  # noqa: E501
        """
        Edits an existing project.

        Args:
            project_id (str): Project ID
            name (str): New project name
            token (str): Authentication token

        Returns:
            Optional[Project]: The updated project or None if failed
        """
        try:
            mutation_str = """
                mutation EditProject($input: editProjectInput!) {
                    editProject(input: $input) {
                        id
                        name
                        workspaceID
                        userID
                        key
                        createdAt
                        archived
                    }
                }
            """

            input_data = {"id": project_id, "name": name}
            variables = {"input": input_data}

            result = await self._execute_query(mutation_str, variables)
            return result.get("editProject")
        except Exception as e:
            print(f"Edit project failed: {str(e)}")
            return None

    async def archive_project(self, project_id: str, token: str) -> Optional[Project]:
        """
        Archives a project.

        Args:
            project_id (str): Project ID
            token (str): Authentication token

        Returns:
            Optional[Project]: The archived project or None if failed
        """
        try:
            mutation_str = """
                mutation ArchiveProject($id: ID!) {
                    archiveProject(id: $id) {
                        id
                        name
                        workspaceID
                        userID
                        key
                        createdAt
                        archived
                    }
                }
            """

            variables = {"id": project_id}

            result = await self._execute_query(mutation_str, variables)
            return result.get("archiveProject")
        except Exception as e:
            print(f"Archive project failed: {str(e)}")
            return None

    async def unarchive_project(self, project_id: str, token: str) -> Optional[Project]:
        """
        Unarchives a project.

        Args:
            project_id (str): Project ID
            token (str): Authentication token

        Returns:
            Optional[Project]: The unarchived project or None if failed
        """
        try:
            mutation_str = """
                mutation UnarchiveProject($id: ID!) {
                    unarchiveProject(id: $id) {
                        id
                        name
                        workspaceID
                        userID
                        key
                        createdAt
                        archived
                    }
                }
            """

            variables = {"id": project_id}

            result = await self._execute_query(mutation_str, variables)
            return result.get("unarchiveProject")
        except Exception as e:
            print(f"Unarchive project failed: {str(e)}")
            return None

    async def switch_project(self, project_id: str, token: str) -> Optional[str]:
        """
        Switches to a different project.

        Args:
            project_id (str): Project ID to switch to
            token (str): Authentication token

        Returns:
            Optional[str]: New token or None if failed
        """
        try:
            mutation_str = """
                mutation SwitchProject($projID: ID!) {
                    switchProject(projID: $projID)
                }
            """

            variables = {"projID": project_id}

            result = await self._execute_query(mutation_str, variables)
            return result.get("switchProject")
        except Exception as e:
            print(f"Switch project failed: {str(e)}")
            return None

    # Project Member Operations
    async def remove_project_member(
        self, project_id: str, user_id: str, member_id: str, token: str
    ) -> bool:
        """
        Removes a member from a project.

        Args:
            project_id (str): Project ID
            user_id (str): User ID to remove
            member_id (str): Project member ID
            token (str): Authentication token

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            mutation_str = """
                mutation RemoveProjectMember($input: RemoveProjectMemberInput!) {  # noqa: E501
                    removeProjectMember(input: $input)
                }
            """

            input_data = {
                "projectID": project_id,
                "userID": user_id,
                "id": member_id,
            }
            variables = {"input": input_data}

            result = await self._execute_query(mutation_str, variables)
            return result.get("removeProjectMember", False)
        except Exception as e:
            print(f"Remove project member failed: {str(e)}")
            return False

    async def update_project_member_role(
        self, project_id: str, user_id: str, role: str, token: str
    ) -> Optional[ProjectMember]:
        """
        Updates a project member's role.

        Args:
            project_id (str): Project ID
            user_id (str): User ID
            role (str): New role
            token (str): Authentication token

        Returns:
            Optional[ProjectMember]: The updated project member or None if failed  # noqa: E501
        """
        try:
            mutation_str = """
                mutation UpdateProjectMemberRole($input: UpdateProjectMemberRoleInput!) {  # noqa: E501
                    updateProjectMemberRole(input: $input) {
                        id
                        projectID
                        userID
                        role
                        createdAt
                        user {
                            id
                            name
                            email
                        }
                    }
                }
            """

            input_data = {
                "projectID": project_id,
                "userID": user_id,
                "role": role,
            }
            variables = {"input": input_data}

            result = await self._execute_query(mutation_str, variables)
            return result.get("updateProjectMemberRole")
        except Exception as e:
            print(f"Update project member role failed: {str(e)}")
            return None


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
