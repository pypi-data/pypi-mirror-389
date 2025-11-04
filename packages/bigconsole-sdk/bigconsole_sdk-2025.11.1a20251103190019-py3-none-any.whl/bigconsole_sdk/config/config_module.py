"""
Config Module for Bigconsole SDK.

This module provides config functionality.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..client.base_client import BaseGraphQLClient


class ConfigModule:
    """
    Config operations module.
    """

    def __init__(self, client: "BaseGraphQLClient") -> None:
        """
        Initialize the config module.

        Args:
            client: The base GraphQL client
        """
        self.client = client

    async def _execute_query(self, query: str, variables: dict = None):
        """Execute a GraphQL query using the base client."""
        return await self.client.request(query, variables)

    # TODO: Implement config operations
