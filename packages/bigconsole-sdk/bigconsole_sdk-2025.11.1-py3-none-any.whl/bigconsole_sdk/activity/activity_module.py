"""
Activity Client for Vibecontrols SDK.

Provides access to activity tracking functionality including activity logs,
user actions, and system events.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from ..client.base_client import BaseGraphQLClient


class ActivityModule:
    """
    Client for managing activity logs and tracking user actions.

    Provides methods to retrieve, filter, and manage activity logs
    with proper authentication and error handling.
    """

    def __init__(self, client: "BaseGraphQLClient"):
        """
        Initialize the Activity module.

        Args:
            client: The base GraphQL client
        """
        self.client = client

    async def _execute_query(self, query: str, variables: dict = None):
        """Execute a GraphQL query using the base client."""
        return await self.client.request(query, variables or {})

    async def get_activities(
        self, filter_input: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get activity logs with optional filtering.

        Args:
            filter_input: Optional filter criteria including:
                - userId: Filter by user ID
                - productId: Filter by product ID
                - workspaceId: Filter by workspace ID
                - action: Filter by action type
                - startDate: Filter by start date
                - endDate: Filter by end date
                - limit: Maximum number of results
                - offset: Pagination offset

        Returns:
            List[Dict[str, Any]]: List of activity log entries
        """
        query = """
            query GetActivities($filter: ActivityLogFilter) {
                getActivities(filter: $filter) {
                    id
                    action
                    productId
                    workspaceId
                    userId
                    userName
                    userEmail
                    metadata
                    ipAddress
                    userAgent
                    createdAt
                    updatedAt
                }
            }
        """
        result = await self._execute_query(query, {"filter": filter_input})
        return result.get("getActivities", [])

    async def get_activity_by_id(self, activity_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific activity log by ID.

        Args:
            activity_id: The ID of the activity log

        Returns:
            Optional[Dict[str, Any]]: Activity log details or None if not found
        """
        query = """
            query GetActivityById($id: ID!) {
                getActivityById(id: $id) {
                    id
                    action
                    productId
                    workspaceId
                    userId
                    userName
                    userEmail
                    metadata
                    ipAddress
                    userAgent
                    createdAt
                    updatedAt
                }
            }
        """
        result = await self._execute_query(query, {"id": activity_id})
        return result.get("getActivityById")

    async def get_user_activities(
        self, user_id: str, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all activities for a specific user.

        Args:
            user_id: The ID of the user
            limit: Maximum number of results to return
            offset: Number of results to skip for pagination

        Returns:
            List[Dict[str, Any]]: List of activity logs for the user
        """
        query = """
            query GetUserActivities($userId: ID!, $limit: Int, $offset: Int) {
                getUserActivities(userId: $userId, limit: $limit, offset: $offset) {
                    id
                    action
                    productId
                    workspaceId
                    userId
                    userName
                    userEmail
                    metadata
                    ipAddress
                    userAgent
                    createdAt
                }
            }
        """
        variables = {"userId": user_id, "limit": limit, "offset": offset}
        result = await self._execute_query(query, variables)
        return result.get("getUserActivities", [])

    async def get_workspace_activities(
        self,
        workspace_id: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all activities for a specific workspace.

        Args:
            workspace_id: The ID of the workspace
            limit: Maximum number of results to return
            offset: Number of results to skip for pagination

        Returns:
            List[Dict[str, Any]]: List of activity logs for the workspace
        """
        query = """
            query GetWorkspaceActivities(
                $workspaceId: ID!, $limit: Int, $offset: Int
            ) {
                getWorkspaceActivities(
                    workspaceId: $workspaceId,
                    limit: $limit,
                    offset: $offset
                ) {
                    id
                    action
                    productId
                    workspaceId
                    userId
                    userName
                    userEmail
                    metadata
                    createdAt
                }
            }
        """
        variables = {"workspaceId": workspace_id, "limit": limit, "offset": offset}
        result = await self._execute_query(query, variables)
        return result.get("getWorkspaceActivities", [])

    async def log_activity(
        self,
        action: str,
        product_id: str,
        workspace_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Log a new activity.

        Args:
            action: The action being performed
            product_id: The ID of the product
            workspace_id: The ID of the workspace
            metadata: Optional metadata associated with the activity

        Returns:
            bool: True if activity was logged successfully
        """
        mutation = """
            mutation LogActivity($input: LogActivityInput!) {
                logActivity(input: $input)
            }
        """
        input_data = {
            "action": action,
            "productId": product_id,
            "workspaceId": workspace_id,
        }
        if metadata:
            input_data["metadata"] = metadata

        result = await self._execute_query(mutation, {"input": input_data})
        return result.get("logActivity", False)

    async def delete_activity(self, activity_id: str) -> bool:
        """
        Delete an activity log.

        Args:
            activity_id: The ID of the activity to delete

        Returns:
            bool: True if activity was deleted successfully
        """
        mutation = """
            mutation DeleteActivity($id: ID!) {
                deleteActivity(id: $id)
            }
        """
        result = await self._execute_query(mutation, {"id": activity_id})
        return result.get("deleteActivity", False)

    async def get_activity_stats(
        self,
        workspace_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get activity statistics for a workspace.

        Args:
            workspace_id: The ID of the workspace
            start_date: Optional start date for statistics (ISO 8601 format)
            end_date: Optional end date for statistics (ISO 8601 format)

        Returns:
            Dict[str, Any]: Activity statistics including counts by action type
        """
        query = """
            query GetActivityStats(
                $workspaceId: ID!, $startDate: String, $endDate: String
            ) {
                getActivityStats(
                    workspaceId: $workspaceId,
                    startDate: $startDate,
                    endDate: $endDate
                ) {
                    totalActivities
                    activitiesByAction
                    activitiesByUser
                    activitiesByProduct
                }
            }
        """
        variables = {
            "workspaceId": workspace_id,
            "startDate": start_date,
            "endDate": end_date,
        }
        result = await self._execute_query(query, variables)
        return result.get("getActivityStats", {})
