"""
Discount Client for Vibecontrols SDK.

Provides access to discount and coupon management functionality including
creating, validating, and applying discounts.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from ..client.base_client import BaseGraphQLClient


class DiscountModule:
    """
    Client for managing discounts and promotional codes.

    Provides methods to create, update, validate, and apply discounts
    with proper authentication and error handling.
    """

    def __init__(self, client: "BaseGraphQLClient"):
        """
        Initialize the Discount module.

        Args:
            client: The base GraphQL client
        """
        self.client = client

    async def _execute_query(self, query: str, variables: dict = None):
        """Execute a GraphQL query using the base client."""
        return await self.client.request(query, variables or {})

    async def get_discounts(
        self, workspace_id: str, active_only: Optional[bool] = False
    ) -> List[Dict[str, Any]]:
        """
        Get all discounts for a workspace.

        Args:
            workspace_id: The ID of the workspace
            active_only: If True, return only active discounts

        Returns:
            List[Dict[str, Any]]: List of discount objects
        """
        query = """
            query GetDiscounts($workspaceId: ID!, $activeOnly: Boolean) {
                getDiscounts(workspaceId: $workspaceId, activeOnly: $activeOnly) {
                    id
                    code
                    name
                    description
                    discountType
                    discountValue
                    maxDiscountAmount
                    minPurchaseAmount
                    workspaceId
                    productId
                    validFrom
                    validUntil
                    usageLimit
                    usageCount
                    isActive
                    createdAt
                    updatedAt
                }
            }
        """
        variables = {"workspaceId": workspace_id, "activeOnly": active_only}
        result = await self._execute_query(query, variables)
        return result.get("getDiscounts", [])

    async def get_discount_by_id(self, discount_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific discount by ID.

        Args:
            discount_id: The ID of the discount

        Returns:
            Optional[Dict[str, Any]]: Discount details or None if not found
        """
        query = """
            query GetDiscountById($id: ID!) {
                getDiscountById(id: $id) {
                    id
                    code
                    name
                    description
                    discountType
                    discountValue
                    maxDiscountAmount
                    minPurchaseAmount
                    workspaceId
                    productId
                    validFrom
                    validUntil
                    usageLimit
                    usageCount
                    isActive
                    createdAt
                    updatedAt
                }
            }
        """
        result = await self._execute_query(query, {"id": discount_id})
        return result.get("getDiscountById")

    async def get_discount_by_code(self, code: str, workspace_id: str) -> Optional[Dict[str, Any]]:  # noqa: E501
        """
        Get a discount by its code.

        Args:
            code: The discount code
            workspace_id: The ID of the workspace

        Returns:
            Optional[Dict[str, Any]]: Discount details or None if not found
        """
        query = """
            query GetDiscountByCode($code: String!, $workspaceId: ID!) {
                getDiscountByCode(code: $code, workspaceId: $workspaceId) {
                    id
                    code
                    name
                    description
                    discountType
                    discountValue
                    maxDiscountAmount
                    minPurchaseAmount
                    workspaceId
                    productId
                    validFrom
                    validUntil
                    usageLimit
                    usageCount
                    isActive
                    createdAt
                    updatedAt
                }
            }
        """
        variables = {"code": code, "workspaceId": workspace_id}
        result = await self._execute_query(query, variables)
        return result.get("getDiscountByCode")

    async def create_discount(
        self,
        workspace_id: str,
        code: str,
        name: str,
        discount_type: str,
        discount_value: float,
        description: Optional[str] = None,
        product_id: Optional[str] = None,
        valid_from: Optional[str] = None,
        valid_until: Optional[str] = None,
        usage_limit: Optional[int] = None,
        min_purchase_amount: Optional[float] = None,
        max_discount_amount: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Create a new discount.

        Args:
            workspace_id: The ID of the workspace
            code: Unique discount code
            name: Display name for the discount
            discount_type: Type of discount ("percentage", "fixed", "buy_x_get_y")
            discount_value: Value of the discount (percentage or fixed amount)
            description: Optional description
            product_id: Optional product ID this discount applies to
            valid_from: Optional start date (ISO 8601 format)
            valid_until: Optional end date (ISO 8601 format)
            usage_limit: Optional maximum number of uses
            min_purchase_amount: Optional minimum purchase amount
            max_discount_amount: Optional maximum discount amount

        Returns:
            Dict[str, Any]: Created discount details
        """
        mutation = """
            mutation CreateDiscount($input: CreateDiscountInput!) {
                createDiscount(input: $input) {
                    id
                    code
                    name
                    description
                    discountType
                    discountValue
                    maxDiscountAmount
                    minPurchaseAmount
                    workspaceId
                    productId
                    validFrom
                    validUntil
                    usageLimit
                    usageCount
                    isActive
                    createdAt
                }
            }
        """
        input_data = {
            "workspaceId": workspace_id,
            "code": code,
            "name": name,
            "discountType": discount_type,
            "discountValue": discount_value,
        }
        if description:
            input_data["description"] = description
        if product_id:
            input_data["productId"] = product_id
        if valid_from:
            input_data["validFrom"] = valid_from
        if valid_until:
            input_data["validUntil"] = valid_until
        if usage_limit:
            input_data["usageLimit"] = usage_limit
        if min_purchase_amount:
            input_data["minPurchaseAmount"] = min_purchase_amount
        if max_discount_amount:
            input_data["maxDiscountAmount"] = max_discount_amount

        result = await self._execute_query(mutation, {"input": input_data})
        return result.get("createDiscount", {})

    async def update_discount(
        self,
        discount_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        discount_value: Optional[float] = None,
        valid_from: Optional[str] = None,
        valid_until: Optional[str] = None,
        usage_limit: Optional[int] = None,
        is_active: Optional[bool] = None,
        min_purchase_amount: Optional[float] = None,
        max_discount_amount: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Update an existing discount.

        Args:
            discount_id: The ID of the discount to update
            name: Optional new name
            description: Optional new description
            discount_value: Optional new discount value
            valid_from: Optional new start date
            valid_until: Optional new end date
            usage_limit: Optional new usage limit
            is_active: Optional active status
            min_purchase_amount: Optional new minimum purchase amount
            max_discount_amount: Optional new maximum discount amount

        Returns:
            Dict[str, Any]: Updated discount details
        """
        mutation = """
            mutation UpdateDiscount($input: UpdateDiscountInput!) {
                updateDiscount(input: $input) {
                    id
                    code
                    name
                    description
                    discountType
                    discountValue
                    maxDiscountAmount
                    minPurchaseAmount
                    validFrom
                    validUntil
                    usageLimit
                    usageCount
                    isActive
                    updatedAt
                }
            }
        """
        input_data = {"id": discount_id}
        if name is not None:
            input_data["name"] = name
        if description is not None:
            input_data["description"] = description
        if discount_value is not None:
            input_data["discountValue"] = discount_value
        if valid_from is not None:
            input_data["validFrom"] = valid_from
        if valid_until is not None:
            input_data["validUntil"] = valid_until
        if usage_limit is not None:
            input_data["usageLimit"] = usage_limit
        if is_active is not None:
            input_data["isActive"] = is_active
        if min_purchase_amount is not None:
            input_data["minPurchaseAmount"] = min_purchase_amount
        if max_discount_amount is not None:
            input_data["maxDiscountAmount"] = max_discount_amount

        result = await self._execute_query(mutation, {"input": input_data})
        return result.get("updateDiscount", {})

    async def delete_discount(self, discount_id: str) -> bool:
        """
        Delete a discount.

        Args:
            discount_id: The ID of the discount to delete

        Returns:
            bool: True if discount was deleted successfully
        """
        mutation = """
            mutation DeleteDiscount($id: ID!) {
                deleteDiscount(id: $id)
            }
        """
        result = await self._execute_query(mutation, {"id": discount_id})
        return result.get("deleteDiscount", False)

    async def validate_discount(
        self, code: str, workspace_id: str, purchase_amount: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Validate a discount code.

        Args:
            code: The discount code to validate
            workspace_id: The ID of the workspace
            purchase_amount: Optional purchase amount to validate against

        Returns:
            Dict[str, Any]: Validation result with discount details if valid
        """
        query = """
            query ValidateDiscount($code: String!, $workspaceId: ID!, $purchaseAmount: Float) {  # noqa: E501
                validateDiscount(code: $code, workspaceId: $workspaceId, purchaseAmount: $purchaseAmount) {  # noqa: E501
                    isValid
                    discount {
                        id
                        code
                        name
                        discountType
                        discountValue
                    }
                    calculatedDiscount
                    reason
                }
            }
        """
        variables = {"code": code, "workspaceId": workspace_id, "purchaseAmount": purchase_amount}  # noqa: E501
        result = await self._execute_query(query, variables)
        return result.get("validateDiscount", {})

    async def apply_discount(
        self, code: str, workspace_id: str, order_id: str, amount: float
    ) -> Dict[str, Any]:
        """
        Apply a discount to an order.

        Args:
            code: The discount code
            workspace_id: The ID of the workspace
            order_id: The ID of the order
            amount: The order amount

        Returns:
            Dict[str, Any]: Applied discount details
        """
        mutation = """
            mutation ApplyDiscount($input: ApplyDiscountInput!) {
                applyDiscount(input: $input) {
                    orderId
                    discountId
                    discountCode
                    originalAmount
                    discountAmount
                    finalAmount
                    appliedAt
                }
            }
        """
        input_data = {
            "code": code,
            "workspaceId": workspace_id,
            "orderId": order_id,
            "amount": amount,
        }
        result = await self._execute_query(mutation, {"input": input_data})
        return result.get("applyDiscount", {})

    async def get_discount_usage(self, discount_id: str) -> Dict[str, Any]:
        """
        Get usage statistics for a discount.

        Args:
            discount_id: The ID of the discount

        Returns:
            Dict[str, Any]: Usage statistics
        """
        query = """
            query GetDiscountUsage($id: ID!) {
                getDiscountUsage(id: $id) {
                    discountId
                    totalUses
                    uniqueUsers
                    totalDiscountAmount
                    averageDiscountAmount
                    usageHistory {
                        userId
                        orderId
                        amount
                        appliedAt
                    }
                }
            }
        """
        result = await self._execute_query(query, {"id": discount_id})
        return result.get("getDiscountUsage", {})
