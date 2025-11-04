"""
Credit Client for Vibecontrols SDK.

Provides access to credit management functionality including credit balance,
transactions, and credit allocation.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from ..client.base_client import BaseGraphQLClient


class CreditModule:
    """
    Client for managing credits and credit transactions.

    Provides methods to retrieve credit balances, manage transactions,
    and allocate credits with proper authentication and error handling.
    """

    def __init__(self, client: "BaseGraphQLClient"):
        """
        Initialize the Credit module.

        Args:
            client: The base GraphQL client
        """
        self.client = client

    async def _execute_query(self, query: str, variables: dict = None):
        """Execute a GraphQL query using the base client."""
        return await self.client.request(query, variables or {})

    async def get_credit_balance(self, workspace_id: str) -> Dict[str, Any]:
        """
        Get the current credit balance for a workspace.

        Args:
            workspace_id: The ID of the workspace

        Returns:
            Dict[str, Any]: Credit balance information including total and available credits  # noqa: E501
        """
        query = """
            query GetCreditBalance($workspaceId: ID!) {
                getCreditBalance(workspaceId: $workspaceId) {
                    workspaceId
                    totalCredits
                    availableCredits
                    reservedCredits
                    currency
                    lastUpdated
                }
            }
        """
        result = await self._execute_query(query, {"workspaceId": workspace_id})
        return result.get("getCreditBalance", {})

    async def get_credit_transactions(
        self,
        workspace_id: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        transaction_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get credit transactions for a workspace.

        Args:
            workspace_id: The ID of the workspace
            limit: Maximum number of transactions to return
            offset: Number of transactions to skip for pagination
            transaction_type: Optional filter by transaction type ("credit", "debit", "refund")  # noqa: E501

        Returns:
            List[Dict[str, Any]]: List of credit transactions
        """
        query = """
            query GetCreditTransactions($workspaceId: ID!, $limit: Int, $offset: Int, $transactionType: String) {  # noqa: E501
                getCreditTransactions(workspaceId: $workspaceId, limit: $limit, offset: $offset, transactionType: $transactionType) {  # noqa: E501
                    id
                    workspaceId
                    billingAccountId
                    amount
                    type
                    status
                    description
                    metadata
                    transactionId
                    productId
                    entityId
                    entityType
                    createdAt
                    updatedAt
                }
            }
        """
        variables = {
            "workspaceId": workspace_id,
            "limit": limit,
            "offset": offset,
            "transactionType": transaction_type,
        }
        result = await self._execute_query(query, variables)
        return result.get("getCreditTransactions", [])

    async def get_transaction_by_id(self, transaction_id: str) -> Optional[Dict[str, Any]]:  # noqa: E501
        """
        Get a specific credit transaction by ID.

        Args:
            transaction_id: The ID of the transaction

        Returns:
            Optional[Dict[str, Any]]: Transaction details or None if not found
        """
        query = """
            query GetTransactionById($id: ID!) {
                getTransactionById(id: $id) {
                    id
                    workspaceId
                    billingAccountId
                    amount
                    type
                    status
                    description
                    metadata
                    transactionId
                    productId
                    entityId
                    entityType
                    createdAt
                    updatedAt
                }
            }
        """
        result = await self._execute_query(query, {"id": transaction_id})
        return result.get("getTransactionById")

    async def add_credits(
        self,
        workspace_id: str,
        amount: float,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Add credits to a workspace.

        Args:
            workspace_id: The ID of the workspace
            amount: Amount of credits to add
            description: Optional description of the credit addition
            metadata: Optional metadata for the transaction

        Returns:
            Dict[str, Any]: Transaction details
        """
        mutation = """
            mutation AddCredits($input: AddCreditsInput!) {
                addCredits(input: $input) {
                    id
                    workspaceId
                    amount
                    type
                    status
                    description
                    createdAt
                }
            }
        """
        input_data = {"workspaceId": workspace_id, "amount": amount}
        if description:
            input_data["description"] = description
        if metadata:
            input_data["metadata"] = metadata

        result = await self._execute_query(mutation, {"input": input_data})
        return result.get("addCredits", {})

    async def deduct_credits(
        self,
        workspace_id: str,
        amount: float,
        description: Optional[str] = None,
        entity_id: Optional[str] = None,
        entity_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Deduct credits from a workspace.

        Args:
            workspace_id: The ID of the workspace
            amount: Amount of credits to deduct
            description: Optional description of the deduction
            entity_id: Optional ID of the entity using the credits
            entity_type: Optional type of the entity

        Returns:
            Dict[str, Any]: Transaction details
        """
        mutation = """
            mutation DeductCredits($input: DeductCreditsInput!) {
                deductCredits(input: $input) {
                    id
                    workspaceId
                    amount
                    type
                    status
                    description
                    entityId
                    entityType
                    createdAt
                }
            }
        """
        input_data = {"workspaceId": workspace_id, "amount": amount}
        if description:
            input_data["description"] = description
        if entity_id:
            input_data["entityId"] = entity_id
        if entity_type:
            input_data["entityType"] = entity_type

        result = await self._execute_query(mutation, {"input": input_data})
        return result.get("deductCredits", {})

    async def transfer_credits(
        self,
        from_workspace_id: str,
        to_workspace_id: str,
        amount: float,
        description: Optional[str] = None,
    ) -> bool:
        """
        Transfer credits between workspaces.

        Args:
            from_workspace_id: Source workspace ID
            to_workspace_id: Destination workspace ID
            amount: Amount of credits to transfer
            description: Optional description of the transfer

        Returns:
            bool: True if transfer was successful
        """
        mutation = """
            mutation TransferCredits($input: TransferCreditsInput!) {
                transferCredits(input: $input)
            }
        """
        input_data = {
            "fromWorkspaceId": from_workspace_id,
            "toWorkspaceId": to_workspace_id,
            "amount": amount,
        }
        if description:
            input_data["description"] = description

        result = await self._execute_query(mutation, {"input": input_data})
        return result.get("transferCredits", False)

    async def refund_credits(
        self, transaction_id: str, amount: Optional[float] = None, reason: Optional[str] = None  # noqa: E501
    ) -> Dict[str, Any]:
        """
        Refund a credit transaction.

        Args:
            transaction_id: The ID of the transaction to refund
            amount: Optional partial refund amount (full refund if not specified)
            reason: Optional reason for the refund

        Returns:
            Dict[str, Any]: Refund transaction details
        """
        mutation = """
            mutation RefundCredits($input: RefundCreditsInput!) {
                refundCredits(input: $input) {
                    id
                    workspaceId
                    amount
                    type
                    status
                    description
                    createdAt
                }
            }
        """
        input_data = {"transactionId": transaction_id}
        if amount:
            input_data["amount"] = amount
        if reason:
            input_data["reason"] = reason

        result = await self._execute_query(mutation, {"input": input_data})
        return result.get("refundCredits", {})

    async def get_credit_usage(
        self, workspace_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None  # noqa: E501
    ) -> Dict[str, Any]:
        """
        Get credit usage statistics for a workspace.

        Args:
            workspace_id: The ID of the workspace
            start_date: Optional start date (ISO 8601 format)
            end_date: Optional end date (ISO 8601 format)

        Returns:
            Dict[str, Any]: Credit usage statistics
        """
        query = """
            query GetCreditUsage($workspaceId: ID!, $startDate: String, $endDate: String) {  # noqa: E501
                getCreditUsage(workspaceId: $workspaceId, startDate: $startDate, endDate: $endDate) {  # noqa: E501
                    workspaceId
                    totalCreditsUsed
                    totalCreditsAdded
                    averageDailyUsage
                    usageByProduct {
                        productId
                        amount
                    }
                    usageByEntity {
                        entityType
                        amount
                    }
                }
            }
        """
        variables = {"workspaceId": workspace_id, "startDate": start_date, "endDate": end_date}  # noqa: E501
        result = await self._execute_query(query, variables)
        return result.get("getCreditUsage", {})

    async def set_credit_limit(self, workspace_id: str, limit: float) -> bool:
        """
        Set a credit limit for a workspace.

        Args:
            workspace_id: The ID of the workspace
            limit: Credit limit to set

        Returns:
            bool: True if limit was set successfully
        """
        mutation = """
            mutation SetCreditLimit($workspaceId: ID!, $limit: Float!) {
                setCreditLimit(workspaceId: $workspaceId, limit: $limit)
            }
        """
        result = await self._execute_query(mutation, {"workspaceId": workspace_id, "limit": limit})  # noqa: E501
        return result.get("setCreditLimit", False)
