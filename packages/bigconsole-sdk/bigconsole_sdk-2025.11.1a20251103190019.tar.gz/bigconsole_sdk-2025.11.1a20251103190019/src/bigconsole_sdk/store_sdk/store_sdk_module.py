"""
Store SDK Client for Vibecontrols SDK.

Provides access to marketplace and store functionality including
apps, extensions, and marketplace transactions.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from ..client.base_client import BaseGraphQLClient


class StoreSdkModule:
    """
    Client for managing marketplace and store operations.

    Provides methods to browse, install, and manage marketplace apps
    with proper authentication and error handling.
    """

    def __init__(self, client: "BaseGraphQLClient"):
        """
        Initialize the Store SDK module.

        Args:
            client: The base GraphQL client
        """
        self.client = client

    async def _execute_query(self, query: str, variables: dict = None):
        """Execute a GraphQL query using the base client."""
        return await self.client.request(query, variables or {})

    async def get_marketplace_apps(
        self, category: Optional[str] = None, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get available apps from the marketplace.

        Args:
            category: Optional category filter
            limit: Maximum number of apps to return

        Returns:
            List[Dict[str, Any]]: List of marketplace apps
        """
        query = """
            query GetMarketplaceApps($category: String, $limit: Int) {
                getMarketplaceApps(category: $category, limit: $limit) {
                    id
                    name
                    description
                    version
                    category
                    publisher
                    price
                    rating
                    downloads
                    iconUrl
                    screenshots
                    features
                    isVerified
                    createdAt
                    updatedAt
                }
            }
        """
        variables = {"category": category, "limit": limit}
        result = await self._execute_query(query, variables)
        return result.get("getMarketplaceApps", [])

    async def get_app_by_id(self, app_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a marketplace app.

        Args:
            app_id: The ID of the app

        Returns:
            Optional[Dict[str, Any]]: App details or None if not found
        """
        query = """
            query GetAppById($id: ID!) {
                getAppById(id: $id) {
                    id
                    name
                    description
                    version
                    category
                    publisher
                    price
                    rating
                    downloads
                    iconUrl
                    screenshots
                    features
                    permissions
                    documentation
                    supportUrl
                    privacyPolicyUrl
                    termsOfServiceUrl
                    isVerified
                    reviews {
                        userId
                        rating
                        comment
                        createdAt
                    }
                    createdAt
                    updatedAt
                }
            }
        """
        result = await self._execute_query(query, {"id": app_id})
        return result.get("getAppById")

    async def install_app(self, app_id: str, workspace_id: str) -> Dict[str, Any]:
        """
        Install an app to a workspace.

        Args:
            app_id: The ID of the app to install
            workspace_id: The ID of the workspace

        Returns:
            Dict[str, Any]: Installation details
        """
        mutation = """
            mutation InstallApp($input: InstallAppInput!) {
                installApp(input: $input) {
                    id
                    appId
                    workspaceId
                    status
                    installedAt
                    config
                }
            }
        """
        input_data = {"appId": app_id, "workspaceId": workspace_id}
        result = await self._execute_query(mutation, {"input": input_data})
        return result.get("installApp", {})

    async def uninstall_app(self, installation_id: str) -> bool:
        """
        Uninstall an app from a workspace.

        Args:
            installation_id: The ID of the app installation

        Returns:
            bool: True if app was uninstalled successfully
        """
        mutation = """
            mutation UninstallApp($id: ID!) {
                uninstallApp(id: $id)
            }
        """
        result = await self._execute_query(mutation, {"id": installation_id})
        return result.get("uninstallApp", False)

    async def get_installed_apps(self, workspace_id: str) -> List[Dict[str, Any]]:
        """
        Get all apps installed in a workspace.

        Args:
            workspace_id: The ID of the workspace

        Returns:
            List[Dict[str, Any]]: List of installed apps
        """
        query = """
            query GetInstalledApps($workspaceId: ID!) {
                getInstalledApps(workspaceId: $workspaceId) {
                    id
                    appId
                    workspaceId
                    app {
                        id
                        name
                        version
                        iconUrl
                    }
                    status
                    config
                    installedAt
                    lastUsedAt
                }
            }
        """
        result = await self._execute_query(query, {"workspaceId": workspace_id})
        return result.get("getInstalledApps", [])

    async def update_app_config(
        self, installation_id: str, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update the configuration for an installed app.

        Args:
            installation_id: The ID of the app installation
            config: New configuration

        Returns:
            Dict[str, Any]: Updated installation details
        """
        mutation = """
            mutation UpdateAppConfig($input: UpdateAppConfigInput!) {
                updateAppConfig(input: $input) {
                    id
                    config
                    updatedAt
                }
            }
        """
        input_data = {"installationId": installation_id, "config": config}
        result = await self._execute_query(mutation, {"input": input_data})
        return result.get("updateAppConfig", {})

    async def submit_app_review(
        self, app_id: str, rating: int, comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Submit a review for a marketplace app.

        Args:
            app_id: The ID of the app
            rating: Rating (1-5)
            comment: Optional review comment

        Returns:
            Dict[str, Any]: Review details
        """
        mutation = """
            mutation SubmitAppReview($input: SubmitAppReviewInput!) {
                submitAppReview(input: $input) {
                    id
                    appId
                    userId
                    rating
                    comment
                    createdAt
                }
            }
        """
        input_data = {"appId": app_id, "rating": rating}
        if comment:
            input_data["comment"] = comment

        result = await self._execute_query(mutation, {"input": input_data})
        return result.get("submitAppReview", {})

    async def get_app_reviews(
        self, app_id: str, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get reviews for a marketplace app.

        Args:
            app_id: The ID of the app
            limit: Maximum number of reviews to return

        Returns:
            List[Dict[str, Any]]: List of reviews
        """
        query = """
            query GetAppReviews($appId: ID!, $limit: Int) {
                getAppReviews(appId: $appId, limit: $limit) {
                    id
                    appId
                    userId
                    userName
                    rating
                    comment
                    createdAt
                }
            }
        """
        variables = {"appId": app_id, "limit": limit}
        result = await self._execute_query(query, variables)
        return result.get("getAppReviews", [])

    async def search_apps(self, query: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:  # noqa: E501
        """
        Search for apps in the marketplace.

        Args:
            query: Search query
            limit: Maximum number of results to return

        Returns:
            List[Dict[str, Any]]: List of matching apps
        """
        graphql_query = """
            query SearchApps($query: String!, $limit: Int) {
                searchApps(query: $query, limit: $limit) {
                    id
                    name
                    description
                    version
                    category
                    publisher
                    price
                    rating
                    iconUrl
                    isVerified
                }
            }
        """
        variables = {"query": query, "limit": limit}
        result = await self._execute_query(graphql_query, variables)
        return result.get("searchApps", [])

    async def get_app_categories(self) -> List[Dict[str, Any]]:
        """
        Get all available app categories.

        Returns:
            List[Dict[str, Any]]: List of categories
        """
        query = """
            query GetAppCategories {
                getAppCategories {
                    id
                    name
                    description
                    appCount
                }
            }
        """
        result = await self._execute_query(query)
        return result.get("getAppCategories", [])

    async def purchase_app(self, app_id: str, workspace_id: str) -> Dict[str, Any]:
        """
        Purchase a paid app.

        Args:
            app_id: The ID of the app to purchase
            workspace_id: The ID of the workspace

        Returns:
            Dict[str, Any]: Purchase transaction details
        """
        mutation = """
            mutation PurchaseApp($input: PurchaseAppInput!) {
                purchaseApp(input: $input) {
                    transactionId
                    appId
                    workspaceId
                    amount
                    status
                    purchasedAt
                }
            }
        """
        input_data = {"appId": app_id, "workspaceId": workspace_id}
        result = await self._execute_query(mutation, {"input": input_data})
        return result.get("purchaseApp", {})

    async def get_app_purchases(self, workspace_id: str) -> List[Dict[str, Any]]:
        """
        Get all app purchases for a workspace.

        Args:
            workspace_id: The ID of the workspace

        Returns:
            List[Dict[str, Any]]: List of purchases
        """
        query = """
            query GetAppPurchases($workspaceId: ID!) {
                getAppPurchases(workspaceId: $workspaceId) {
                    transactionId
                    appId
                    app {
                        id
                        name
                        iconUrl
                    }
                    workspaceId
                    amount
                    status
                    purchasedAt
                }
            }
        """
        result = await self._execute_query(query, {"workspaceId": workspace_id})
        return result.get("getAppPurchases", [])

    async def publish_app(
        self,
        name: str,
        description: str,
        version: str,
        category: str,
        price: float,
        icon_url: str,
        features: List[str],
        permissions: List[str],
    ) -> Dict[str, Any]:
        """
        Publish a new app to the marketplace (for developers).

        Args:
            name: App name
            description: App description
            version: App version
            category: App category
            price: App price (0 for free)
            icon_url: URL to app icon
            features: List of app features
            permissions: List of required permissions

        Returns:
            Dict[str, Any]: Published app details
        """
        mutation = """
            mutation PublishApp($input: PublishAppInput!) {
                publishApp(input: $input) {
                    id
                    name
                    version
                    category
                    publisher
                    status
                    createdAt
                }
            }
        """
        input_data = {
            "name": name,
            "description": description,
            "version": version,
            "category": category,
            "price": price,
            "iconUrl": icon_url,
            "features": features,
            "permissions": permissions,
        }
        result = await self._execute_query(mutation, {"input": input_data})
        return result.get("publishApp", {})

    async def update_app(self, app_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing marketplace app (for developers).

        Args:
            app_id: The ID of the app to update
            updates: Fields to update

        Returns:
            Dict[str, Any]: Updated app details
        """
        mutation = """
            mutation UpdateApp($input: UpdateAppInput!) {
                updateApp(input: $input) {
                    id
                    name
                    version
                    updatedAt
                }
            }
        """
        input_data = {"appId": app_id, **updates}
        result = await self._execute_query(mutation, {"input": input_data})
        return result.get("updateApp", {})
