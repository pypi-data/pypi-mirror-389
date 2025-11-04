"""
Utils Module for Vibecontrols SDK.

This module provides utils functionality.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..client.base_client import BaseGraphQLClient


class UtilsModule:
    """
    Utils operations module.
    """

    def __init__(self, client: "BaseGraphQLClient") -> None:
        """
        Initialize the utils module.

        Args:
            client: The base GraphQL client
        """
        self.client = client

    async def _execute_query(self, query: str, variables: dict = None):
        """Execute a GraphQL query using the base client."""
        return await self.client.request(query, variables)

    # TODO: Implement utils operations
