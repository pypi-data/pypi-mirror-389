from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..client.base_client import BaseGraphQLClient


class RBACModule:
    def __init__(self, client: "BaseGraphQLClient") -> None:
        self.client = client

    async def get_permissions(self) -> None:
        # TODO: Implement RBAC operations
        pass
