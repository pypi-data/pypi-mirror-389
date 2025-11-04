"""
Tenant Client for Vibecontrols SDK.

Provides access to multi-tenancy management functionality including
tenant configuration, isolation, and tenant-specific settings.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from ..client.base_client import BaseGraphQLClient


class TenantModule:
    """
    Client for managing tenants in a multi-tenant environment.

    Provides methods to create, update, and manage tenants
    with proper authentication and error handling.
    """

    def __init__(self, client: "BaseGraphQLClient"):
        """
        Initialize the Tenant module.

        Args:
            client: The base GraphQL client
        """
        self.client = client

    async def _execute_query(self, query: str, variables: dict = None):
        """Execute a GraphQL query using the base client."""
        return await self.client.request(query, variables or {})

    async def get_tenant(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """
        Get tenant information by ID.

        Args:
            tenant_id: The ID of the tenant

        Returns:
            Optional[Dict[str, Any]]: Tenant details or None if not found
        """
        query = """
            query GetTenant($id: ID!) {
                getTenant(id: $id) {
                    id
                    name
                    domain
                    subdomain
                    status
                    plan
                    settings
                    features
                    limits {
                        maxUsers
                        maxWorkspaces
                        maxStorage
                    }
                    usage {
                        users
                        workspaces
                        storage
                    }
                    createdAt
                    updatedAt
                }
            }
        """
        result = await self._execute_query(query, {"id": tenant_id})
        return result.get("getTenant")

    async def get_current_tenant(self) -> Dict[str, Any]:
        """
        Get the current tenant information.

        Returns:
            Dict[str, Any]: Current tenant details
        """
        query = """
            query GetCurrentTenant {
                getCurrentTenant {
                    id
                    name
                    domain
                    subdomain
                    status
                    plan
                    settings
                    features
                    limits {
                        maxUsers
                        maxWorkspaces
                        maxStorage
                    }
                    usage {
                        users
                        workspaces
                        storage
                    }
                    createdAt
                    updatedAt
                }
            }
        """
        result = await self._execute_query(query)
        return result.get("getCurrentTenant", {})

    async def create_tenant(
        self,
        name: str,
        domain: str,
        subdomain: str,
        plan: str,
        admin_email: str,
        settings: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new tenant.

        Args:
            name: Tenant name
            domain: Custom domain
            subdomain: Subdomain
            plan: Tenant plan ("free", "starter", "professional", "enterprise")
            admin_email: Admin email for the tenant
            settings: Optional tenant settings

        Returns:
            Dict[str, Any]: Created tenant details
        """
        mutation = """
            mutation CreateTenant($input: CreateTenantInput!) {
                createTenant(input: $input) {
                    id
                    name
                    domain
                    subdomain
                    status
                    plan
                    createdAt
                }
            }
        """
        input_data = {
            "name": name,
            "domain": domain,
            "subdomain": subdomain,
            "plan": plan,
            "adminEmail": admin_email,
        }
        if settings:
            input_data["settings"] = settings

        result = await self._execute_query(mutation, {"input": input_data})
        return result.get("createTenant", {})

    async def update_tenant(
        self,
        tenant_id: str,
        name: Optional[str] = None,
        domain: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None,
        features: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Update tenant information.

        Args:
            tenant_id: The ID of the tenant
            name: Optional new name
            domain: Optional new domain
            settings: Optional new settings
            features: Optional new features list

        Returns:
            Dict[str, Any]: Updated tenant details
        """
        mutation = """
            mutation UpdateTenant($input: UpdateTenantInput!) {
                updateTenant(input: $input) {
                    id
                    name
                    domain
                    subdomain
                    settings
                    features
                    updatedAt
                }
            }
        """
        input_data = {"id": tenant_id}
        if name is not None:
            input_data["name"] = name
        if domain is not None:
            input_data["domain"] = domain
        if settings is not None:
            input_data["settings"] = settings
        if features is not None:
            input_data["features"] = features

        result = await self._execute_query(mutation, {"input": input_data})
        return result.get("updateTenant", {})

    async def delete_tenant(self, tenant_id: str) -> bool:
        """
        Delete a tenant.

        Args:
            tenant_id: The ID of the tenant to delete

        Returns:
            bool: True if tenant was deleted successfully
        """
        mutation = """
            mutation DeleteTenant($id: ID!) {
                deleteTenant(id: $id)
            }
        """
        result = await self._execute_query(mutation, {"id": tenant_id})
        return result.get("deleteTenant", False)

    async def suspend_tenant(self, tenant_id: str, reason: Optional[str] = None) -> bool:  # noqa: E501
        """
        Suspend a tenant.

        Args:
            tenant_id: The ID of the tenant to suspend
            reason: Optional reason for suspension

        Returns:
            bool: True if tenant was suspended successfully
        """
        mutation = """
            mutation SuspendTenant($id: ID!, $reason: String) {
                suspendTenant(id: $id, reason: $reason)
            }
        """
        result = await self._execute_query(mutation, {"id": tenant_id, "reason": reason})  # noqa: E501
        return result.get("suspendTenant", False)

    async def activate_tenant(self, tenant_id: str) -> bool:
        """
        Activate a suspended tenant.

        Args:
            tenant_id: The ID of the tenant to activate

        Returns:
            bool: True if tenant was activated successfully
        """
        mutation = """
            mutation ActivateTenant($id: ID!) {
                activateTenant(id: $id)
            }
        """
        result = await self._execute_query(mutation, {"id": tenant_id})
        return result.get("activateTenant", False)

    async def get_tenant_settings(self, tenant_id: str) -> Dict[str, Any]:
        """
        Get tenant settings.

        Args:
            tenant_id: The ID of the tenant

        Returns:
            Dict[str, Any]: Tenant settings
        """
        query = """
            query GetTenantSettings($id: ID!) {
                getTenantSettings(id: $id) {
                    tenantId
                    branding {
                        logo
                        primaryColor
                        secondaryColor
                    }
                    authentication {
                        ssoEnabled
                        mfaRequired
                        passwordPolicy
                    }
                    features {
                        name
                        enabled
                    }
                    notifications {
                        emailEnabled
                        slackEnabled
                    }
                    dataRetention {
                        logs
                        analytics
                        backups
                    }
                }
            }
        """
        result = await self._execute_query(query, {"id": tenant_id})
        return result.get("getTenantSettings", {})

    async def update_tenant_settings(
        self, tenant_id: str, settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update tenant settings.

        Args:
            tenant_id: The ID of the tenant
            settings: New settings

        Returns:
            Dict[str, Any]: Updated tenant settings
        """
        mutation = """
            mutation UpdateTenantSettings($input: UpdateTenantSettingsInput!) {
                updateTenantSettings(input: $input) {
                    tenantId
                    branding {
                        logo
                        primaryColor
                        secondaryColor
                    }
                    authentication {
                        ssoEnabled
                        mfaRequired
                        passwordPolicy
                    }
                    updatedAt
                }
            }
        """
        input_data = {"tenantId": tenant_id, "settings": settings}
        result = await self._execute_query(mutation, {"input": input_data})
        return result.get("updateTenantSettings", {})

    async def get_tenant_usage(self, tenant_id: str) -> Dict[str, Any]:
        """
        Get usage statistics for a tenant.

        Args:
            tenant_id: The ID of the tenant

        Returns:
            Dict[str, Any]: Tenant usage statistics
        """
        query = """
            query GetTenantUsage($id: ID!) {
                getTenantUsage(id: $id) {
                    tenantId
                    users {
                        current
                        limit
                        percentage
                    }
                    workspaces {
                        current
                        limit
                        percentage
                    }
                    storage {
                        current
                        limit
                        percentage
                        unit
                    }
                    apiCalls {
                        today
                        thisMonth
                        limit
                    }
                }
            }
        """
        result = await self._execute_query(query, {"id": tenant_id})
        return result.get("getTenantUsage", {})

    async def get_tenant_limits(self, tenant_id: str) -> Dict[str, Any]:
        """
        Get limits for a tenant.

        Args:
            tenant_id: The ID of the tenant

        Returns:
            Dict[str, Any]: Tenant limits
        """
        query = """
            query GetTenantLimits($id: ID!) {
                getTenantLimits(id: $id) {
                    tenantId
                    maxUsers
                    maxWorkspaces
                    maxStorage
                    maxApiCalls
                    maxProjects
                    maxTeams
                }
            }
        """
        result = await self._execute_query(query, {"id": tenant_id})
        return result.get("getTenantLimits", {})

    async def update_tenant_limits(self, tenant_id: str, limits: Dict[str, Any]) -> Dict[str, Any]:  # noqa: E501
        """
        Update limits for a tenant.

        Args:
            tenant_id: The ID of the tenant
            limits: New limits

        Returns:
            Dict[str, Any]: Updated tenant limits
        """
        mutation = """
            mutation UpdateTenantLimits($input: UpdateTenantLimitsInput!) {
                updateTenantLimits(input: $input) {
                    tenantId
                    maxUsers
                    maxWorkspaces
                    maxStorage
                    maxApiCalls
                    updatedAt
                }
            }
        """
        input_data = {"tenantId": tenant_id, "limits": limits}
        result = await self._execute_query(mutation, {"input": input_data})
        return result.get("updateTenantLimits", {})

    async def list_tenants(
        self,
        status: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        List all tenants (admin only).

        Args:
            status: Optional filter by status ("active", "suspended", "trial")
            limit: Maximum number of tenants to return
            offset: Number of tenants to skip for pagination

        Returns:
            List[Dict[str, Any]]: List of tenants
        """
        query = """
            query ListTenants($status: String, $limit: Int, $offset: Int) {
                listTenants(status: $status, limit: $limit, offset: $offset) {
                    id
                    name
                    domain
                    subdomain
                    status
                    plan
                    createdAt
                    updatedAt
                }
            }
        """
        variables = {"status": status, "limit": limit, "offset": offset}
        result = await self._execute_query(query, variables)
        return result.get("listTenants", [])

    async def get_tenant_by_domain(self, domain: str) -> Optional[Dict[str, Any]]:
        """
        Get tenant by domain or subdomain.

        Args:
            domain: The domain or subdomain to search for

        Returns:
            Optional[Dict[str, Any]]: Tenant details or None if not found
        """
        query = """
            query GetTenantByDomain($domain: String!) {
                getTenantByDomain(domain: $domain) {
                    id
                    name
                    domain
                    subdomain
                    status
                    plan
                    createdAt
                }
            }
        """
        result = await self._execute_query(query, {"domain": domain})
        return result.get("getTenantByDomain")

    async def upgrade_tenant_plan(self, tenant_id: str, new_plan: str) -> Dict[str, Any]:  # noqa: E501
        """
        Upgrade or downgrade a tenant's plan.

        Args:
            tenant_id: The ID of the tenant
            new_plan: New plan ("free", "starter", "professional", "enterprise")

        Returns:
            Dict[str, Any]: Updated tenant with new plan
        """
        mutation = """
            mutation UpgradeTenantPlan($tenantId: ID!, $newPlan: String!) {
                upgradeTenantPlan(tenantId: $tenantId, newPlan: $newPlan) {
                    id
                    plan
                    limits {
                        maxUsers
                        maxWorkspaces
                        maxStorage
                    }
                    updatedAt
                }
            }
        """
        result = await self._execute_query(mutation, {"tenantId": tenant_id, "newPlan": new_plan})  # noqa: E501
        return result.get("upgradeTenantPlan", {})
