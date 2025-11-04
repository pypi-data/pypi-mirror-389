"""
Export Client for Vibecontrols SDK.

Provides access to data export functionality including generating exports,
downloading data, and managing export jobs.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from ..client.base_client import BaseGraphQLClient


class ExportModule:
    """
    Client for managing data exports.

    Provides methods to create export jobs, retrieve export status,
    and download exported data with proper authentication and error handling.
    """

    def __init__(self, client: "BaseGraphQLClient"):
        """
        Initialize the Export module.

        Args:
            client: The base GraphQL client
        """
        self.client = client

    async def _execute_query(self, query: str, variables: dict = None):
        """Execute a GraphQL query using the base client."""
        return await self.client.request(query, variables or {})

    async def create_export(
        self,
        workspace_id: str,
        export_type: str,
        format: str,
        filters: Optional[Dict[str, Any]] = None,
        include_fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new export job.

        Args:
            workspace_id: The ID of the workspace
            export_type: Type of data to export ("users", "activities", "analytics", "billing")  # noqa: E501
            format: Export format ("csv", "json", "xlsx", "pdf")
            filters: Optional filters to apply to the export
            include_fields: Optional list of fields to include in the export

        Returns:
            Dict[str, Any]: Export job details
        """
        mutation = """
            mutation CreateExport($input: CreateExportInput!) {
                createExport(input: $input) {
                    id
                    workspaceId
                    exportType
                    format
                    status
                    fileUrl
                    fileSize
                    filters
                    includeFields
                    createdAt
                    completedAt
                }
            }
        """
        input_data = {
            "workspaceId": workspace_id,
            "exportType": export_type,
            "format": format,
        }
        if filters:
            input_data["filters"] = filters
        if include_fields:
            input_data["includeFields"] = include_fields

        result = await self._execute_query(mutation, {"input": input_data})
        return result.get("createExport", {})

    async def get_export_status(self, export_id: str) -> Dict[str, Any]:
        """
        Get the status of an export job.

        Args:
            export_id: The ID of the export job

        Returns:
            Dict[str, Any]: Export job status and details
        """
        query = """
            query GetExportStatus($id: ID!) {
                getExportStatus(id: $id) {
                    id
                    workspaceId
                    exportType
                    format
                    status
                    progress
                    fileUrl
                    fileSize
                    errorMessage
                    createdAt
                    startedAt
                    completedAt
                }
            }
        """
        result = await self._execute_query(query, {"id": export_id})
        return result.get("getExportStatus", {})

    async def get_exports(
        self, workspace_id: str, limit: Optional[int] = None, offset: Optional[int] = None  # noqa: E501
    ) -> List[Dict[str, Any]]:
        """
        Get all exports for a workspace.

        Args:
            workspace_id: The ID of the workspace
            limit: Maximum number of exports to return
            offset: Number of exports to skip for pagination

        Returns:
            List[Dict[str, Any]]: List of export jobs
        """
        query = """
            query GetExports($workspaceId: ID!, $limit: Int, $offset: Int) {
                getExports(workspaceId: $workspaceId, limit: $limit, offset: $offset) {
                    id
                    workspaceId
                    exportType
                    format
                    status
                    fileUrl
                    fileSize
                    createdAt
                    completedAt
                }
            }
        """
        variables = {"workspaceId": workspace_id, "limit": limit, "offset": offset}
        result = await self._execute_query(query, variables)
        return result.get("getExports", [])

    async def download_export(self, export_id: str) -> Dict[str, Any]:
        """
        Get download information for an export.

        Args:
            export_id: The ID of the export job

        Returns:
            Dict[str, Any]: Download URL and metadata
        """
        query = """
            query DownloadExport($id: ID!) {
                downloadExport(id: $id) {
                    exportId
                    downloadUrl
                    expiresAt
                    fileName
                    fileSize
                    format
                }
            }
        """
        result = await self._execute_query(query, {"id": export_id})
        return result.get("downloadExport", {})

    async def cancel_export(self, export_id: str) -> bool:
        """
        Cancel a pending or running export job.

        Args:
            export_id: The ID of the export job to cancel

        Returns:
            bool: True if export was cancelled successfully
        """
        mutation = """
            mutation CancelExport($id: ID!) {
                cancelExport(id: $id)
            }
        """
        result = await self._execute_query(mutation, {"id": export_id})
        return result.get("cancelExport", False)

    async def delete_export(self, export_id: str) -> bool:
        """
        Delete an export job and its associated file.

        Args:
            export_id: The ID of the export job to delete

        Returns:
            bool: True if export was deleted successfully
        """
        mutation = """
            mutation DeleteExport($id: ID!) {
                deleteExport(id: $id)
            }
        """
        result = await self._execute_query(mutation, {"id": export_id})
        return result.get("deleteExport", False)

    async def schedule_export(
        self,
        workspace_id: str,
        export_type: str,
        format: str,
        schedule: str,
        filters: Optional[Dict[str, Any]] = None,
        include_fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Schedule a recurring export.

        Args:
            workspace_id: The ID of the workspace
            export_type: Type of data to export
            format: Export format
            schedule: Cron expression for scheduling (e.g., "0 0 * * *" for daily)
            filters: Optional filters to apply
            include_fields: Optional list of fields to include

        Returns:
            Dict[str, Any]: Scheduled export details
        """
        mutation = """
            mutation ScheduleExport($input: ScheduleExportInput!) {
                scheduleExport(input: $input) {
                    id
                    workspaceId
                    exportType
                    format
                    schedule
                    isActive
                    nextRunAt
                    lastRunAt
                    createdAt
                }
            }
        """
        input_data = {
            "workspaceId": workspace_id,
            "exportType": export_type,
            "format": format,
            "schedule": schedule,
        }
        if filters:
            input_data["filters"] = filters
        if include_fields:
            input_data["includeFields"] = include_fields

        result = await self._execute_query(mutation, {"input": input_data})
        return result.get("scheduleExport", {})

    async def get_scheduled_exports(self, workspace_id: str) -> List[Dict[str, Any]]:
        """
        Get all scheduled exports for a workspace.

        Args:
            workspace_id: The ID of the workspace

        Returns:
            List[Dict[str, Any]]: List of scheduled exports
        """
        query = """
            query GetScheduledExports($workspaceId: ID!) {
                getScheduledExports(workspaceId: $workspaceId) {
                    id
                    workspaceId
                    exportType
                    format
                    schedule
                    isActive
                    nextRunAt
                    lastRunAt
                    createdAt
                }
            }
        """
        result = await self._execute_query(query, {"workspaceId": workspace_id})
        return result.get("getScheduledExports", [])

    async def update_scheduled_export(
        self,
        schedule_id: str,
        schedule: Optional[str] = None,
        is_active: Optional[bool] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Update a scheduled export.

        Args:
            schedule_id: The ID of the scheduled export
            schedule: Optional new schedule cron expression
            is_active: Optional active status
            filters: Optional new filters

        Returns:
            Dict[str, Any]: Updated scheduled export details
        """
        mutation = """
            mutation UpdateScheduledExport($input: UpdateScheduledExportInput!) {
                updateScheduledExport(input: $input) {
                    id
                    schedule
                    isActive
                    nextRunAt
                    updatedAt
                }
            }
        """
        input_data = {"id": schedule_id}
        if schedule is not None:
            input_data["schedule"] = schedule
        if is_active is not None:
            input_data["isActive"] = is_active
        if filters is not None:
            input_data["filters"] = filters

        result = await self._execute_query(mutation, {"input": input_data})
        return result.get("updateScheduledExport", {})

    async def delete_scheduled_export(self, schedule_id: str) -> bool:
        """
        Delete a scheduled export.

        Args:
            schedule_id: The ID of the scheduled export to delete

        Returns:
            bool: True if scheduled export was deleted successfully
        """
        mutation = """
            mutation DeleteScheduledExport($id: ID!) {
                deleteScheduledExport(id: $id)
            }
        """
        result = await self._execute_query(mutation, {"id": schedule_id})
        return result.get("deleteScheduledExport", False)

    async def get_export_templates(self, export_type: str) -> List[Dict[str, Any]]:
        """
        Get available export templates for a specific export type.

        Args:
            export_type: The type of export

        Returns:
            List[Dict[str, Any]]: List of available templates
        """
        query = """
            query GetExportTemplates($exportType: String!) {
                getExportTemplates(exportType: $exportType) {
                    id
                    name
                    description
                    exportType
                    defaultFormat
                    availableFields
                    defaultFields
                }
            }
        """
        result = await self._execute_query(query, {"exportType": export_type})
        return result.get("getExportTemplates", [])
