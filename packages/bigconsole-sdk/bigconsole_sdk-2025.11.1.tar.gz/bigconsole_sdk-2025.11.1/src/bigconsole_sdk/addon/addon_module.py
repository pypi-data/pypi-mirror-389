"""
Addon Client for Bigconsole SDK.

Provides access to addon management functionality including creating, updating,
and managing addon subscriptions.
"""

from typing import TYPE_CHECKING, List, Optional, TypedDict

if TYPE_CHECKING:
    from ..client.base_client import BaseGraphQLClient


# Type definitions for Addon system
class AddonQuotaInput(TypedDict):
    quotaId: str
    quantity: int


class CreateAddOnsInput(TypedDict):
    name: str
    price: float
    currency: str
    duration: str  # "monthly" or "yearly"
    quotas: List[AddonQuotaInput]
    productId: str


class UpdateAddOnsInput(TypedDict):
    id: str
    name: Optional[str]
    price: Optional[float]
    currency: Optional[str]
    duration: Optional[str]
    quotas: List[AddonQuotaInput]
    isActive: Optional[bool]


class SubscriptionFeatures(TypedDict):
    id: str
    planId: Optional[str]
    addonId: Optional[str]
    quotaId: str


class AddonSubscription(TypedDict):
    id: str
    currentSubscriptionId: str
    addonId: str
    quantity: int
    startDate: str
    endDate: str
    createdAt: str
    updatedAt: str


class Addon(TypedDict):
    id: str
    name: str
    price: float
    productID: str
    currency: str
    duration: str
    isActive: bool
    features: List[SubscriptionFeatures]
    addonSubscriptions: List[AddonSubscription]
    createdAt: str
    updatedAt: str


class AddonModule:
    """
    Client for managing addons in the Workspaces platform.

    Provides methods to create, update, retrieve, and manage addon subscriptions  # noqa: E501
    with proper authentication and error handling.
    """

    def __init__(self, client: "BaseGraphQLClient"):
        """
        Initialize the Addon module.

        Args:
            client: The base GraphQL client
        """
        self.client = client

    async def _execute_query(self, query: str, variables: dict = None):
        """Execute a GraphQL query using the base client."""
        return await self.client.request(query, variables)

    # Addon Query Operations
    async def get_all_addons(self, token: str) -> List[Addon]:
        """
        Retrieves all available addons.

        Args:
            token (str): Authentication token

        Returns:
            List[Addon]: List of all available addons
        """
        try:
            query_str = """
                query GetAllAddons {
                    getAllAddOns {
                        id
                        name
                        price
                        productID
                        currency
                        duration
                        isActive
                        features {
                            id
                            planId
                            addonId
                            quotaId
                        }
                        addonSubscriptions {
                            id
                            currentSubscriptionId
                            addonId
                            quantity
                            startDate
                            endDate
                            createdAt
                            updatedAt
                        }
                        createdAt
                        updatedAt
                    }
                }
            """

            result = await self._execute_query(query_str)
            return result.get("getAllAddOns", [])
        except Exception as e:
            print(f"Get all addons failed: {str(e)}")
            return []

    async def get_selected_addons(self, addon_ids: List[str], token: str) -> List[Addon]:  # noqa: E501
        """
        Retrieves specific addons by their IDs.

        Args:
            addon_ids (List[str]): List of addon IDs to retrieve
            token (str): Authentication token

        Returns:
            List[Addon]: List of requested addons
        """
        try:
            query_str = """
                query GetSelectedAddons($addonIDs: [String!]!) {
                    getSelectedAddons(addonIDs: $addonIDs) {
                        id
                        name
                        price
                        productID
                        currency
                        duration
                        isActive
                        features {
                            id
                            planId
                            addonId
                            quotaId
                        }
                        addonSubscriptions {
                            id
                            currentSubscriptionId
                            addonId
                            quantity
                            startDate
                            endDate
                            createdAt
                            updatedAt
                        }
                        createdAt
                        updatedAt
                    }
                }
            """

            variables = {"addonIDs": addon_ids}
            result = await self._execute_query(query_str, variables)
            return result.get("getSelectedAddons", [])
        except Exception as e:
            print(f"Get selected addons failed: {str(e)}")
            return []

    # Addon Mutation Operations
    async def create_addon(
        self,
        name: str,
        price: float,
        currency: str,
        duration: str,
        quotas: List[AddonQuotaInput],
        product_id: str,
        token: str,
    ) -> bool:
        """
        Creates a new addon.

        Args:
            name (str): Name of the addon
            price (float): Price of the addon
            currency (str): Currency for pricing
            duration (str): Duration ("monthly" or "yearly")
            quotas (List[AddonQuotaInput]): List of quota configurations
            product_id (str): Product ID the addon belongs to
            token (str): Authentication token

        Returns:
            bool: True if addon creation succeeded, False otherwise
        """
        try:
            mutation_str = """
                mutation CreateAddOns($input: createAddOnsInput!) {
                    createAddOns(input: $input)
                }
            """

            variables = {
                "input": {
                    "name": name,
                    "price": price,
                    "currency": currency,
                    "duration": duration,
                    "quotas": quotas,
                    "productId": product_id,
                }
            }

            result = await self._execute_query(mutation_str, variables)
            return result.get("createAddOns", False)
        except Exception as e:
            print(f"Create addon failed: {str(e)}")
            return False

    async def update_addon(
        self,
        addon_id: str,
        quotas: List[AddonQuotaInput],
        token: str,
        name: Optional[str] = None,
        price: Optional[float] = None,
        currency: Optional[str] = None,
        duration: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> bool:
        """
        Updates an existing addon.

        Args:
            addon_id (str): ID of the addon to update
            quotas (List[AddonQuotaInput]): List of quota configurations
            token (str): Authentication token
            name (str, optional): New name for the addon
            price (float, optional): New price for the addon
            currency (str, optional): New currency for the addon
            duration (str, optional): New duration for the addon
            is_active (bool, optional): New active status for the addon

        Returns:
            bool: True if addon update succeeded, False otherwise
        """
        try:
            mutation_str = """
                mutation UpdateAddonDetails($input: updateAddOnsInput!) {
                    updateAddOnDetails(input: $input)
                }
            """

            update_input = {"id": addon_id, "quotas": quotas}

            if name is not None:
                update_input["name"] = name
            if price is not None:
                update_input["price"] = price
            if currency is not None:
                update_input["currency"] = currency
            if duration is not None:
                update_input["duration"] = duration
            if is_active is not None:
                update_input["isActive"] = is_active

            variables = {"input": update_input}

            result = await self._execute_query(mutation_str, variables)
            return result.get("updateAddOnDetails", False)
        except Exception as e:
            print(f"Update addon failed: {str(e)}")
            return False

    async def toggle_addon(self, addon_id: str, status: bool, token: str) -> bool:
        """
        Toggles the active status of an addon.

        Args:
            addon_id (str): ID of the addon to toggle
            status (bool): New active status (True for active, False for inactive)  # noqa: E501
            token (str): Authentication token

        Returns:
            bool: True if toggle operation succeeded, False otherwise
        """
        try:
            mutation_str = """
                mutation ToggleAddon($id: ID!, $status: Boolean!) {
                    toggleAddOn(id: $id, status: $status)
                }
            """

            variables = {"id": addon_id, "status": status}

            result = await self._execute_query(mutation_str, variables)
            return result.get("toggleAddOn", False)
        except Exception as e:
            print(f"Toggle addon failed: {str(e)}")
            return False


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
