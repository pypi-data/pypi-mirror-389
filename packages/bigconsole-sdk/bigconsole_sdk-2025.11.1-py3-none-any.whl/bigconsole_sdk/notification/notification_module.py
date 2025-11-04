"""
Notification Client for Vibecontrols SDK.

Provides access to notification management functionality including sending,
managing, and tracking notifications across multiple channels.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from ..client.base_client import BaseGraphQLClient


class NotificationModule:
    """
    Client for managing notifications.

    Provides methods to send, retrieve, and manage notifications
    with proper authentication and error handling.
    """

    def __init__(self, client: "BaseGraphQLClient"):
        """
        Initialize the Notification module.

        Args:
            client: The base GraphQL client
        """
        self.client = client

    async def _execute_query(self, query: str, variables: dict = None):
        """Execute a GraphQL query using the base client."""
        return await self.client.request(query, variables or {})

    async def send_notification(
        self,
        user_id: str,
        title: str,
        message: str,
        notification_type: str,
        channel: Optional[str] = "in_app",
        metadata: Optional[Dict[str, Any]] = None,
        action_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send a notification to a user.

        Args:
            user_id: The ID of the recipient user
            title: Notification title
            message: Notification message
            notification_type: Type of notification ("info", "warning", "error", "success")  # noqa: E501
            channel: Notification channel ("in_app", "email", "sms", "push")
            metadata: Optional metadata
            action_url: Optional URL for action button

        Returns:
            Dict[str, Any]: Sent notification details
        """
        mutation = """
            mutation SendNotification($input: SendNotificationInput!) {
                sendNotification(input: $input) {
                    id
                    userId
                    title
                    message
                    type
                    channel
                    status
                    metadata
                    actionUrl
                    createdAt
                }
            }
        """
        input_data = {
            "userId": user_id,
            "title": title,
            "message": message,
            "type": notification_type,
            "channel": channel,
        }
        if metadata:
            input_data["metadata"] = metadata
        if action_url:
            input_data["actionUrl"] = action_url

        result = await self._execute_query(mutation, {"input": input_data})
        return result.get("sendNotification", {})

    async def send_bulk_notification(
        self,
        user_ids: List[str],
        title: str,
        message: str,
        notification_type: str,
        channel: Optional[str] = "in_app",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Send a notification to multiple users.

        Args:
            user_ids: List of recipient user IDs
            title: Notification title
            message: Notification message
            notification_type: Type of notification
            channel: Notification channel
            metadata: Optional metadata

        Returns:
            Dict[str, Any]: Bulk notification result
        """
        mutation = """
            mutation SendBulkNotification($input: SendBulkNotificationInput!) {
                sendBulkNotification(input: $input) {
                    totalSent
                    totalFailed
                    notificationIds
                }
            }
        """
        input_data = {
            "userIds": user_ids,
            "title": title,
            "message": message,
            "type": notification_type,
            "channel": channel,
        }
        if metadata:
            input_data["metadata"] = metadata

        result = await self._execute_query(mutation, {"input": input_data})
        return result.get("sendBulkNotification", {})

    async def get_notifications(
        self,
        user_id: str,
        status: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get notifications for a user.

        Args:
            user_id: The ID of the user
            status: Optional filter by status ("unread", "read", "archived")
            limit: Maximum number of notifications to return
            offset: Number of notifications to skip for pagination

        Returns:
            List[Dict[str, Any]]: List of notifications
        """
        query = """
            query GetNotifications($userId: ID!, $status: String, $limit: Int, $offset: Int) {  # noqa: E501
                getNotifications(userId: $userId, status: $status, limit: $limit, offset: $offset) {  # noqa: E501
                    id
                    userId
                    title
                    message
                    type
                    channel
                    status
                    metadata
                    actionUrl
                    readAt
                    createdAt
                }
            }
        """
        variables = {"userId": user_id, "status": status, "limit": limit, "offset": offset}  # noqa: E501
        result = await self._execute_query(query, variables)
        return result.get("getNotifications", [])

    async def get_notification_by_id(self, notification_id: str) -> Optional[Dict[str, Any]]:  # noqa: E501
        """
        Get a specific notification by ID.

        Args:
            notification_id: The ID of the notification

        Returns:
            Optional[Dict[str, Any]]: Notification details or None if not found
        """
        query = """
            query GetNotificationById($id: ID!) {
                getNotificationById(id: $id) {
                    id
                    userId
                    title
                    message
                    type
                    channel
                    status
                    metadata
                    actionUrl
                    readAt
                    createdAt
                }
            }
        """
        result = await self._execute_query(query, {"id": notification_id})
        return result.get("getNotificationById")

    async def mark_as_read(self, notification_id: str) -> bool:
        """
        Mark a notification as read.

        Args:
            notification_id: The ID of the notification

        Returns:
            bool: True if notification was marked as read
        """
        mutation = """
            mutation MarkAsRead($id: ID!) {
                markAsRead(id: $id)
            }
        """
        result = await self._execute_query(mutation, {"id": notification_id})
        return result.get("markAsRead", False)

    async def mark_all_as_read(self, user_id: str) -> bool:
        """
        Mark all notifications as read for a user.

        Args:
            user_id: The ID of the user

        Returns:
            bool: True if all notifications were marked as read
        """
        mutation = """
            mutation MarkAllAsRead($userId: ID!) {
                markAllAsRead(userId: $userId)
            }
        """
        result = await self._execute_query(mutation, {"userId": user_id})
        return result.get("markAllAsRead", False)

    async def delete_notification(self, notification_id: str) -> bool:
        """
        Delete a notification.

        Args:
            notification_id: The ID of the notification to delete

        Returns:
            bool: True if notification was deleted successfully
        """
        mutation = """
            mutation DeleteNotification($id: ID!) {
                deleteNotification(id: $id)
            }
        """
        result = await self._execute_query(mutation, {"id": notification_id})
        return result.get("deleteNotification", False)

    async def archive_notification(self, notification_id: str) -> bool:
        """
        Archive a notification.

        Args:
            notification_id: The ID of the notification to archive

        Returns:
            bool: True if notification was archived successfully
        """
        mutation = """
            mutation ArchiveNotification($id: ID!) {
                archiveNotification(id: $id)
            }
        """
        result = await self._execute_query(mutation, {"id": notification_id})
        return result.get("archiveNotification", False)

    async def get_unread_count(self, user_id: str) -> int:
        """
        Get the count of unread notifications for a user.

        Args:
            user_id: The ID of the user

        Returns:
            int: Count of unread notifications
        """
        query = """
            query GetUnreadCount($userId: ID!) {
                getUnreadCount(userId: $userId)
            }
        """
        result = await self._execute_query(query, {"userId": user_id})
        return result.get("getUnreadCount", 0)

    async def get_notification_preferences(self, user_id: str) -> Dict[str, Any]:
        """
        Get notification preferences for a user.

        Args:
            user_id: The ID of the user

        Returns:
            Dict[str, Any]: Notification preferences
        """
        query = """
            query GetNotificationPreferences($userId: ID!) {
                getNotificationPreferences(userId: $userId) {
                    userId
                    emailEnabled
                    smsEnabled
                    pushEnabled
                    inAppEnabled
                    notificationTypes {
                        type
                        enabled
                        channels
                    }
                }
            }
        """
        result = await self._execute_query(query, {"userId": user_id})
        return result.get("getNotificationPreferences", {})

    async def update_notification_preferences(
        self, user_id: str, preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update notification preferences for a user.

        Args:
            user_id: The ID of the user
            preferences: New preferences

        Returns:
            Dict[str, Any]: Updated notification preferences
        """
        mutation = """
            mutation UpdateNotificationPreferences($input: UpdateNotificationPreferencesInput!) {  # noqa: E501
                updateNotificationPreferences(input: $input) {
                    userId
                    emailEnabled
                    smsEnabled
                    pushEnabled
                    inAppEnabled
                    notificationTypes {
                        type
                        enabled
                        channels
                    }
                    updatedAt
                }
            }
        """
        input_data = {"userId": user_id, "preferences": preferences}
        result = await self._execute_query(mutation, {"input": input_data})
        return result.get("updateNotificationPreferences", {})

    async def subscribe_to_topic(self, user_id: str, topic: str) -> bool:
        """
        Subscribe a user to a notification topic.

        Args:
            user_id: The ID of the user
            topic: The topic to subscribe to

        Returns:
            bool: True if subscription was successful
        """
        mutation = """
            mutation SubscribeToTopic($userId: ID!, $topic: String!) {
                subscribeToTopic(userId: $userId, topic: $topic)
            }
        """
        result = await self._execute_query(mutation, {"userId": user_id, "topic": topic})  # noqa: E501
        return result.get("subscribeToTopic", False)

    async def unsubscribe_from_topic(self, user_id: str, topic: str) -> bool:
        """
        Unsubscribe a user from a notification topic.

        Args:
            user_id: The ID of the user
            topic: The topic to unsubscribe from

        Returns:
            bool: True if unsubscription was successful
        """
        mutation = """
            mutation UnsubscribeFromTopic($userId: ID!, $topic: String!) {
                unsubscribeFromTopic(userId: $userId, topic: $topic)
            }
        """
        result = await self._execute_query(mutation, {"userId": user_id, "topic": topic})  # noqa: E501
        return result.get("unsubscribeFromTopic", False)

    async def send_workspace_notification(
        self,
        workspace_id: str,
        title: str,
        message: str,
        notification_type: str,
        role_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send a notification to all members of a workspace.

        Args:
            workspace_id: The ID of the workspace
            title: Notification title
            message: Notification message
            notification_type: Type of notification
            role_filter: Optional filter by role ("admin", "member", "viewer")

        Returns:
            Dict[str, Any]: Result of workspace notification
        """
        mutation = """
            mutation SendWorkspaceNotification($input: SendWorkspaceNotificationInput!) {  # noqa: E501
                sendWorkspaceNotification(input: $input) {
                    totalSent
                    totalFailed
                }
            }
        """
        input_data = {
            "workspaceId": workspace_id,
            "title": title,
            "message": message,
            "type": notification_type,
        }
        if role_filter:
            input_data["roleFilter"] = role_filter

        result = await self._execute_query(mutation, {"input": input_data})
        return result.get("sendWorkspaceNotification", {})
