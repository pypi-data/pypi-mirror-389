"""
Support Module for Bigconsole SDK.

This module provides support functionality.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..client.base_client import BaseGraphQLClient


class SupportModule:
    """
    Support operations module.
    """

    def __init__(self, client: "BaseGraphQLClient") -> None:
        """
        Initialize the support module.

        Args:
            client: The base GraphQL client
        """
        self.client = client

    async def _execute_query(self, query: str, variables: dict = None):
        """Execute a GraphQL query using the base client."""
        return await self.client.request(query, variables)

    # TODO: Implement support operations
