"""
Store Client for Vibecontrols SDK.

Provides access to store management functionality including store items, categories,  # noqa: E501
orders, reviews, publishers, and subscription entitlements.
"""

from typing import TYPE_CHECKING, Any, List, Optional, TypedDict

if TYPE_CHECKING:
    from ..client.base_client import BaseGraphQLClient

# Enums


class ItemType:
    WORKFLOW = "WORKFLOW"
    NODE = "NODE"
    APP = "APP"


class SubmissionStatus:
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class PricingModel:
    FREE = "FREE"
    PAID_ONETIME = "PAID_ONETIME"
    SUBSCRIPTION = "SUBSCRIPTION"


class OrderStatus:
    PROCESSED = "processed"
    FAILED = "failed"
    PENDING = "pending"


class PublishStatus:
    DRAFT = "DRAFT"
    PENDING_REVIEW = "PENDING_REVIEW"
    PUBLISHED = "PUBLISHED"
    REJECTED = "REJECTED"
    ARCHIVED = "ARCHIVED"


class VersionStatus:
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PUBLISHED = "PUBLISHED"


class EntitlementAccessType:
    FREE_ACCESS = "FREE_ACCESS"
    DISCOUNT = "DISCOUNT"


# Type definitions for Store system


class StoreCategory(TypedDict):
    id: str
    name: str
    slug: str
    description: Optional[str]


class Review(TypedDict):
    id: str
    rating: int
    comment: Optional[str]
    createdAt: str
    updatedAt: str


class Publisher(TypedDict):
    id: str
    name: str
    email: str
    websiteUrl: Optional[str]
    logoUrl: Optional[str]
    createdAt: str
    updatedAt: str


class SubscriptionEntitlement(TypedDict):
    id: str
    itemId: str
    planId: str
    accessType: str
    discountPercentage: Optional[float]
    createdAt: str
    updatedAt: str


class StoreItemVersion(TypedDict):
    id: str
    version: str
    description: str
    longDescription: Optional[str]
    tags: List[str]
    iconUrl: Optional[str]
    screenshotUrls: List[str]
    videoUrls: List[str]
    documentationUrl: Optional[str]
    repositoryUrl: Optional[str]
    pricingModel: str
    price: Optional[float]
    currency: Optional[str]
    content: Any  # JSON content
    zipFileUrl: Optional[str]
    status: str
    createdAt: str
    updatedAt: str


class StoreItemSubmission(TypedDict):
    id: str
    storeItemId: str
    versionId: str
    status: str
    rejectionNote: Optional[str]
    submittedAt: str
    reviewedAt: Optional[str]


class StoreItem(TypedDict):
    id: str
    slug: str
    name: str
    itemType: str
    version: str
    description: str
    longDescription: Optional[str]
    tags: List[str]
    productID: str
    iconUrl: Optional[str]
    screenshotUrls: List[str]
    videoUrls: List[str]
    documentationUrl: Optional[str]
    repositoryUrl: Optional[str]
    pricingModel: str
    price: Optional[float]
    currency: Optional[str]
    publisherId: str
    status: str
    publishedAt: Optional[str]
    downloadCount: int
    viewCount: int
    content: Any  # JSON content
    featured: bool
    zipFileUrl: Optional[str]
    createdAt: str
    updatedAt: str


class StoreOrder(TypedDict):
    id: str
    status: str
    itemNameAtPurchase: str
    itemVersionAtPurchase: Optional[str]
    appliedEntitlementId: Optional[str]
    createdAt: str
    updatedAt: str


class DeveloperEarnings(TypedDict):
    totalEarnings: float
    monthlyEarnings: float
    totalOrders: int
    monthlyOrders: int
    currency: str


class MonthlyEarning(TypedDict):
    month: str
    year: int
    earnings: float
    orders: int
    currency: str


class ItemSalesStats(TypedDict):
    totalSales: int
    totalEarnings: float
    monthlySales: int
    monthlyEarnings: float
    currency: str


# Input types


class PublishItemsToStoreInput(TypedDict):
    name: str
    version: str
    itemType: str
    description: str
    longDescription: Optional[str]
    documentationUrl: Optional[str]
    repositoryUrl: Optional[str]
    tags: List[str]
    categories: List[str]
    iconUrl: str
    screenshotUrls: List[str]
    videoUrls: List[str]
    pricingModel: str
    price: float
    currency: Optional[str]
    zipFileUrl: Optional[str]
    content: str


class EditBasicStoreItemDetailsInput(TypedDict):
    id: str
    name: Optional[str]
    version: str
    itemType: Optional[str]
    description: Optional[str]
    longDescription: Optional[str]
    documentationUrl: Optional[str]
    repositoryUrl: Optional[str]
    tags: Optional[List[str]]
    categories: Optional[List[str]]
    iconUrl: Optional[str]
    screenshotUrls: Optional[List[str]]
    videoUrls: Optional[List[str]]


class CreateNewStoreItemVersionInput(TypedDict):
    id: str
    name: Optional[str]
    version: str
    description: Optional[str]
    longDescription: Optional[str]
    documentationUrl: Optional[str]
    repositoryUrl: Optional[str]
    tags: Optional[List[str]]
    categories: Optional[List[str]]
    iconUrl: Optional[str]
    screenshotUrls: Optional[List[str]]
    videoUrls: Optional[List[str]]
    pricingModel: Optional[str]
    price: Optional[float]
    currency: Optional[str]
    content: str
    zipFileUrl: Optional[str]


class BrowseAllCategoriesInput(TypedDict, total=False):
    searchTerm: Optional[str]
    filterTypes: Optional[List[str]]
    filterPricing: Optional[List[str]]
    filterTags: Optional[List[str]]
    sortBy: Optional[str]
    limit: Optional[int]
    offset: Optional[int]


class SearchArgsInput(TypedDict, total=False):
    searchTerm: Optional[str]
    filterTypes: Optional[List[str]]
    filterPricing: Optional[List[str]]
    filterTags: Optional[List[str]]
    limit: Optional[int]
    offset: Optional[int]


class DeveloperEarningsInput(TypedDict, total=False):
    period: Optional[str]  # "month", "quarter", "year", "all"
    startDate: Optional[str]
    endDate: Optional[str]


class ItemOrdersInput(TypedDict):
    storeItemId: str
    page: int
    limit: int
    status: Optional[str]
    startDate: Optional[str]
    endDate: Optional[str]


class RollbackStoreItemVersionInput(TypedDict):
    storeItemId: str
    targetVersionId: str
    reason: Optional[str]


class CompareVersionsInput(TypedDict):
    storeItemId: str
    sourceVersionId: str
    targetVersionId: str


class StoreModule:
    """
    Client for managing store functionality in the Workspaces platform.

    Provides methods to manage store items, categories, orders, reviews,
    publishers, and subscription entitlements with proper authentication
    and error handling.
    """

    def __init__(self, client: "BaseGraphQLClient"):
        """
        Initialize the Store module.

        Args:
            client: The base GraphQL client
        """
        self.client = client

    async def _execute_query(self, query: str, variables: dict = None):
        """Execute a GraphQL query using the base client."""
        return await self.client.request(query, variables)

    # Store Item Query Operations
    async def get_store_items(self, token: str) -> List[StoreItem]:
        """
        Retrieves all store items.

        Args:
            token (str): Authentication token

        Returns:
            List[StoreItem]: List of all store items
        """
        try:
            query_str = """
                query GetStoreItems {
                    getStoreItems {
                        id
                        slug
                        name
                        itemType
                        version
                        description
                        longDescription
                        tags
                        productID
                        iconUrl
                        screenshotUrls
                        videoUrls
                        documentationUrl
                        repositoryUrl
                        pricingModel
                        price
                        currency
                        publisherId
                        status
                        publishedAt
                        downloadCount
                        viewCount
                        content
                        featured
                        zipFileUrl
                        createdAt
                        updatedAt
                    }
                }
            """

            result = await self._execute_query(query_str)
            return result.get("getStoreItems", [])
        except Exception as e:
            print(f"Get store items failed: {str(e)}")
            return []

    async def get_store_item(self, item_id: str, token: str) -> Optional[StoreItem]:
        """
        Retrieves a specific store item by ID.

        Args:
            item_id (str): Store item ID
            token (str): Authentication token

        Returns:
            Optional[StoreItem]: Store item details or None if not found
        """
        try:
            query_str = """
                query GetStoreItem($id: String!) {
                    getStoreItem(id: $id) {
                        id
                        slug
                        name
                        itemType
                        version
                        description
                        longDescription
                        tags
                        productID
                        iconUrl
                        screenshotUrls
                        videoUrls
                        documentationUrl
                        repositoryUrl
                        pricingModel
                        price
                        currency
                        publisherId
                        status
                        publishedAt
                        downloadCount
                        viewCount
                        content
                        featured
                        zipFileUrl
                        createdAt
                        updatedAt
                    }
                }
            """

            variables = {"id": item_id}
            result = await self._execute_query(query_str, variables)
            return result.get("getStoreItem")
        except Exception as e:
            print(f"Get store item failed: {str(e)}")
            return None

    async def search_store_items(
        self, search_input: SearchArgsInput, token: str
    ) -> List[StoreItem]:
        """
        Searches store items with filtering options.

        Args:
            search_input (SearchArgsInput): Search parameters
            token (str): Authentication token

        Returns:
            List[StoreItem]: Filtered list of store items
        """
        try:
            query_str = """
                query SearchStoreItem($input: SearchArgs) {
                    searchStoreItem(input: $input) {
                        id
                        slug
                        name
                        itemType
                        version
                        description
                        longDescription
                        tags
                        iconUrl
                        screenshotUrls
                        pricingModel
                        price
                        currency
                        status
                        downloadCount
                        viewCount
                        featured
                        createdAt
                        updatedAt
                    }
                }
            """

            variables = {"input": search_input}
            result = await self._execute_query(query_str, variables)
            return result.get("searchStoreItem", [])
        except Exception as e:
            print(f"Search store items failed: {str(e)}")
            return []

    async def browse_categories_all(
        self, browse_input: BrowseAllCategoriesInput, token: str
    ) -> List[StoreItem]:
        """
        Browses store items by categories with filtering.

        Args:
            browse_input (BrowseAllCategoriesInput): Browse parameters
            token (str): Authentication token

        Returns:
            List[StoreItem]: Filtered store items
        """
        try:
            query_str = """
                query BrowseCategoriesAll($input: BrowseAllCategories!) {
                    browseCategoriesAll(input: $input) {
                        id
                        slug
                        name
                        itemType
                        version
                        description
                        tags
                        iconUrl
                        pricingModel
                        price
                        currency
                        status
                        downloadCount
                        viewCount
                        featured
                    }
                }
            """

            variables = {"input": browse_input}
            result = await self._execute_query(query_str, variables)
            return result.get("browseCategoriesAll", [])
        except Exception as e:
            print(f"Browse categories failed: {str(e)}")
            return []

    async def get_home_grouped_store_items(self, token: str) -> dict:
        """
        Retrieves grouped store items for home page display.

        Args:
            token (str): Authentication token

        Returns:
            dict: Grouped store items (featured, mostDownloaded, etc.)
        """
        try:
            query_str = """
                query GetHomeGroupedStoreItems {
                    getHomeGroupedStoreItems {
                        featured {
                            id
                            name
                            itemType
                            description
                            iconUrl
                            pricingModel
                            price
                            currency
                            downloadCount
                        }
                        mostDownloaded {
                            id
                            name
                            itemType
                            description
                            iconUrl
                            pricingModel
                            price
                            currency
                            downloadCount
                        }
                        recentlyAdded {
                            id
                            name
                            itemType
                            description
                            iconUrl
                            pricingModel
                            price
                            currency
                            createdAt
                        }
                        freeItems {
                            id
                            name
                            itemType
                            description
                            iconUrl
                            pricingModel
                            downloadCount
                        }
                    }
                }
            """

            result = await self._execute_query(query_str)
            return result.get("getHomeGroupedStoreItems", {})
        except Exception as e:
            print(f"Get home grouped store items failed: {str(e)}")
            return {}

    async def get_unpublished_items(
        self,
        token: str,
        search_query: Optional[str] = None,
        filter_type: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[StoreItem]:
        """
        Retrieves unpublished store items.

        Args:
            token (str): Authentication token
            search_query (str, optional): Search query
            filter_type (str, optional): Item type filter
            limit (int, optional): Number of items to return
            offset (int, optional): Number of items to skip

        Returns:
            List[StoreItem]: List of unpublished items
        """
        try:
            query_str = """
                query GetUnPublishedEntitys(
                    $searchQuery: String
                    $filterType: ItemType
                    $limit: Int
                    $offset: Int
                ) {
                    getUnPublishedEntitys(
                        searchQuery: $searchQuery
                        filterType: $filterType
                        limit: $limit
                        offset: $offset
                    ) {
                        id
                        name
                        itemType
                        version
                        description
                        status
                        createdAt
                        updatedAt
                    }
                }
            """

            variables = {}
            if search_query is not None:
                variables["searchQuery"] = search_query
            if filter_type is not None:
                variables["filterType"] = filter_type
            if limit is not None:
                variables["limit"] = limit
            if offset is not None:
                variables["offset"] = offset

            result = await self._execute_query(query_str, variables)
            return result.get("getUnPublishedEntitys", [])
        except Exception as e:
            print(f"Get unpublished items failed: {str(e)}")
            return []

    # Store Order Query Operations
    async def get_workspace_store_orders(
        self,
        page: int,
        limit: int,
        token: str,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> dict:
        """
        Retrieves workspace store orders with pagination.

        Args:
            page (int): Page number
            limit (int): Items per page
            token (str): Authentication token
            status (str, optional): Order status filter
            search (str, optional): Search query

        Returns:
            dict: Store orders with total count
        """
        try:
            query_str = """
                query GetWorkspaceStoreOrder(
                    $page: Int!
                    $limit: Int!
                    $status: OrderStatus
                    $search: String
                ) {
                    getWorkspaceStoreOrder(
                        page: $page
                        limit: $limit
                        status: $status
                        search: $search
                    ) {
                        total
                        orders {
                            id
                            status
                            itemNameAtPurchase
                            itemVersionAtPurchase
                            appliedEntitlementId
                            createdAt
                            updatedAt
                        }
                    }
                }
            """

            variables = {"page": page, "limit": limit}
            if status is not None:
                variables["status"] = status
            if search is not None:
                variables["search"] = search

            result = await self._execute_query(query_str, variables)
            return result.get("getWorkspaceStoreOrder", {"total": 0, "orders": []})
        except Exception as e:
            print(f"Get workspace store orders failed: {str(e)}")
            return {"total": 0, "orders": []}

    async def get_store_order_by_id(self, order_id: str, token: str) -> Optional[StoreOrder]:  # noqa: E501
        """
        Retrieves a specific store order by ID.

        Args:
            order_id (str): Store order ID
            token (str): Authentication token

        Returns:
            Optional[StoreOrder]: Store order details or None if not found
        """
        try:
            query_str = """
                query GetStoreOrderById($orderId: String!) {
                    getStoreOrderById(orderId: $orderId) {
                        id
                        status
                        itemNameAtPurchase
                        itemVersionAtPurchase
                        appliedEntitlementId
                        createdAt
                        updatedAt
                    }
                }
            """

            variables = {"orderId": order_id}
            result = await self._execute_query(query_str, variables)
            return result.get("getStoreOrderById")
        except Exception as e:
            print(f"Get store order by ID failed: {str(e)}")
            return None

    # Developer Analytics Operations
    async def get_developer_earnings(
        self, earnings_input: Optional[DeveloperEarningsInput], token: str
    ) -> Optional[DeveloperEarnings]:
        """
        Retrieves developer earnings analytics.

        Args:
            earnings_input (DeveloperEarningsInput, optional): Filter parameters
            token (str): Authentication token

        Returns:
            Optional[DeveloperEarnings]: Developer earnings data or None if failed  # noqa: E501
        """
        try:
            query_str = """
                query GetDeveloperEarnings($input: DeveloperEarningsInput) {
                    getDeveloperEarnings(input: $input) {
                        totalEarnings
                        monthlyEarnings
                        totalOrders
                        monthlyOrders
                        currency
                        earnings {
                            month
                            year
                            earnings
                            orders
                            currency
                        }
                        topSellingItems {
                            totalSales
                            totalEarnings
                            monthlySales
                            monthlyEarnings
                            currency
                        }
                    }
                }
            """

            variables = {}
            if earnings_input is not None:
                variables["input"] = earnings_input

            result = await self._execute_query(query_str, variables)
            return result.get("getDeveloperEarnings")
        except Exception as e:
            print(f"Get developer earnings failed: {str(e)}")
            return None

    async def get_store_item_orders(self, orders_input: ItemOrdersInput, token: str) -> dict:  # noqa: E501
        """
        Retrieves orders for a specific store item.

        Args:
            orders_input (ItemOrdersInput): Order filter parameters
            token (str): Authentication token

        Returns:
            dict: Store item orders with pagination info
        """
        try:
            query_str = """
                query GetStoreItemOrders($input: ItemOrdersInput!) {
                    getStoreItemOrders(input: $input) {
                        orders {
                            id
                            status
                            itemNameAtPurchase
                            itemVersionAtPurchase
                            createdAt
                            updatedAt
                            appliedEntitlementId
                        }
                        totalCount
                        totalEarnings
                        currency
                    }
                }
            """

            variables = {"input": orders_input}
            result = await self._execute_query(query_str, variables)
            return result.get(
                "getStoreItemOrders",
                {
                    "orders": [],
                    "totalCount": 0,
                    "totalEarnings": 0.0,
                    "currency": "USD",
                },
            )
        except Exception as e:
            print(f"Get store item orders failed: {str(e)}")
            return {
                "orders": [],
                "totalCount": 0,
                "totalEarnings": 0.0,
                "currency": "USD",
            }

    # Admin Operations
    async def get_pending_store_item_submissions(
        self,
        limit: int,
        offset: int,
        token: str,
        search_query: Optional[str] = None,
        filter_item_type: Optional[str] = None,
    ) -> dict:
        """
        Retrieves pending store item submissions for admin review.

        Args:
            limit (int): Number of submissions to return
            offset (int): Number of submissions to skip
            token (str): Authentication token
            search_query (str, optional): Search query
            filter_item_type (str, optional): Item type filter

        Returns:
            dict: Pending submissions with total count
        """
        try:
            query_str = """
                query GetPendingStoreItemSubmissions(
                    $searchQuery: String
                    $filterItemType: ItemType
                    $limit: Int!
                    $offset: Int!
                ) {
                    getPendingStoreItemSubmissions(
                        searchQuery: $searchQuery
                        filterItemType: $filterItemType
                        limit: $limit
                        offset: $offset
                    ) {
                        submissions {
                            id
                            storeItemId
                            versionId
                            status
                            rejectionNote
                            submittedAt
                            reviewedAt
                        }
                        totalCount
                    }
                }
            """

            variables = {"limit": limit, "offset": offset}
            if search_query is not None:
                variables["searchQuery"] = search_query
            if filter_item_type is not None:
                variables["filterItemType"] = filter_item_type

            result = await self._execute_query(query_str, variables)
            return result.get(
                "getPendingStoreItemSubmissions",
                {"submissions": [], "totalCount": 0},
            )
        except Exception as e:
            print(f"Get pending store item submissions failed: {str(e)}")
            return {"submissions": [], "totalCount": 0}

    async def get_admin_store_item_summary(self, token: str) -> dict:
        """
        Retrieves admin dashboard summary for store items.

        Args:
            token (str): Authentication token

        Returns:
            dict: Store item summary counts
        """
        try:
            query_str = """
                query GetAdminStoreItemSummary {
                    getAdminStoreItemSummary {
                        pendingCount
                        approvedCount
                        rejectedCount
                    }
                }
            """

            result = await self._execute_query(query_str)
            return result.get(
                "getAdminStoreItemSummary",
                {"pendingCount": 0, "approvedCount": 0, "rejectedCount": 0},
            )
        except Exception as e:
            print(f"Get admin store item summary failed: {str(e)}")
            return {"pendingCount": 0, "approvedCount": 0, "rejectedCount": 0}

    async def get_store_dashboard_items(self, token: str) -> dict:
        """
        Retrieves dashboard statistics for the store including total users,
        total store items, and top unpublished items.

        Args:
            token (str): Authentication token

        Returns:
            dict: Dashboard statistics with totalUsers, totalStoreItems, and topUnpublishedItems  # noqa: E501
        """
        try:
            query_str = """
                query GetStoreDashBoardItems {
                    getStoreDashBoardItems {
                        totalUsers
                        totalStoreItems
                        topUnpublishedItems {
                            id
                            title
                            author
                            type
                        }
                    }
                }
            """

            result = await self._execute_query(query_str)
            return result.get(
                "getStoreDashBoardItems",
                {
                    "totalUsers": 0,
                    "totalStoreItems": 0,
                    "topUnpublishedItems": [],
                },
            )
        except Exception as e:
            print(f"Get store dashboard items failed: {str(e)}")
            return {
                "totalUsers": 0,
                "totalStoreItems": 0,
                "topUnpublishedItems": [],
            }

    async def get_store_item_publish_by_user(self, token: str) -> Optional[dict]:
        """
        Retrieves the user who published the store item.

        Args:
            token (str): Authentication token

        Returns:
            Optional[dict]: User information who published the item
        """
        try:
            query_str = """
                query GetStoreItemPublishByUser {
                    getStoreItemPublishByUser {
                        id
                        name
                        email
                    }
                }
            """

            result = await self._execute_query(query_str)
            return result.get("getStoreItemPublishByUser")
        except Exception as e:
            print(f"Get store item publish by user failed: {str(e)}")
            return None

    async def get_approved_store_items(
        self,
        limit: int,
        offset: int,
        token: str,
        search_query: Optional[str] = None,
        filter_item_type: Optional[str] = None,
    ) -> dict:
        """
        Retrieves approved store items with optional filtering.

        Args:
            limit (int): Number of items to return
            offset (int): Number of items to skip
            token (str): Authentication token
            search_query (str, optional): Search query
            filter_item_type (str, optional): Item type filter

        Returns:
            dict: Approved store items with total count
        """
        try:
            query_str = """
                query GetApprovedStoreItems(
                    $searchQuery: String
                    $filterItemType: ItemType
                    $limit: Int!
                    $offset: Int!
                ) {
                    getApprovedStoreItems(
                        searchQuery: $searchQuery
                        filterItemType: $filterItemType
                        limit: $limit
                        offset: $offset
                    ) {
                        items {
                            id
                            slug
                            name
                            itemType
                            version
                            description
                            longDescription
                            tags
                            productID
                            iconUrl
                            screenshotUrls
                            videoUrls
                            documentationUrl
                            repositoryUrl
                            pricingModel
                            price
                            currency
                            publisherId
                            status
                            publishedAt
                            downloadCount
                            viewCount
                        }
                        totalCount
                    }
                }
            """

            variables = {"limit": limit, "offset": offset}
            if search_query is not None:
                variables["searchQuery"] = search_query
            if filter_item_type is not None:
                variables["filterItemType"] = filter_item_type

            result = await self._execute_query(query_str, variables)
            return result.get("getApprovedStoreItems", {"items": [], "totalCount": 0})
        except Exception as e:
            print(f"Get approved store items failed: {str(e)}")
            return {"items": [], "totalCount": 0}

    async def fetch_rejected_submission_req_store_item(
        self, submission_id: str, token: str
    ) -> Optional[dict]:
        """
        Fetches a specific rejected store item submission by ID.

        Args:
            submission_id (str): ID of the rejected submission
            token (str): Authentication token

        Returns:
            Optional[dict]: Store item submission details
        """
        try:
            query_str = """
                query FetchRejectedSubmissionReqStoreItem($submissionId: ID!) {
                    fetchRejectedSubmissionReqStoreItem(submissionId: $submissionId) {  # noqa: E501
                        id
                        storeItemId
                        versionId
                        status
                        rejectionNote
                        submittedAt
                        reviewedAt
                    }
                }
            """

            variables = {"submissionId": submission_id}
            result = await self._execute_query(query_str, variables)
            return result.get("fetchRejectedSubmissionReqStoreItem")
        except Exception as e:
            print(f"Fetch rejected submission failed: {str(e)}")
            return None

    # Store Item Mutation Operations
    async def publish_item_to_store(self, item_input: PublishItemsToStoreInput, token: str) -> bool:  # noqa: E501
        """
        Publishes a new item to the store.

        Args:
            item_input (PublishItemsToStoreInput): Item details
            token (str): Authentication token

        Returns:
            bool: True if publication succeeded, False otherwise
        """
        try:
            mutation_str = """
                mutation PublishItemsToStore($input: PublishItemsToStoreInput!) {  # noqa: E501
                    publishItemsToStore(input: $input)
                }
            """

            variables = {"input": item_input}
            result = await self._execute_query(mutation_str, variables)
            return result.get("publishItemsToStore", False)
        except Exception as e:
            print(f"Publish item to store failed: {str(e)}")
            return False

    async def edit_store_item_basic_details(
        self, edit_input: EditBasicStoreItemDetailsInput, token: str
    ) -> bool:
        """
        Edits basic details of a store item.

        Args:
            edit_input (EditBasicStoreItemDetailsInput): Updated item details
            token (str): Authentication token

        Returns:
            bool: True if edit succeeded, False otherwise
        """
        try:
            mutation_str = """
                mutation EditStoreItemBasicDetails($input: EditBasicStoreItemDeatilsInput!) {  # noqa: E501
                    editStoreItemBasicDetails(input: $input)
                }
            """

            variables = {"input": edit_input}
            result = await self._execute_query(mutation_str, variables)
            return result.get("editStoreItemBasicDetails", False)
        except Exception as e:
            print(f"Edit store item basic details failed: {str(e)}")
            return False

    async def create_new_store_item_version(
        self, version_input: CreateNewStoreItemVersionInput, token: str
    ) -> bool:
        """
        Creates a new version of a store item.

        Args:
            version_input (CreateNewStoreItemVersionInput): New version details
            token (str): Authentication token

        Returns:
            bool: True if version creation succeeded, False otherwise
        """
        try:
            mutation_str = """
                mutation CreateNewStoreItemVersion($input: CreateNewStoreItemVersionInput!) {  # noqa: E501
                    createNewStoreItemVersion(input: $input)
                }
            """

            variables = {"input": version_input}
            result = await self._execute_query(mutation_str, variables)
            return result.get("createNewStoreItemVersion", False)
        except Exception as e:
            print(f"Create new store item version failed: {str(e)}")
            return False

    async def purchase_item(self, store_item_id: str, token: str) -> bool:
        """
        Purchases a store item.

        Args:
            store_item_id (str): Store item ID to purchase
            token (str): Authentication token

        Returns:
            bool: True if purchase succeeded, False otherwise
        """
        try:
            mutation_str = """
                mutation PurchaseItem($storeItemId: String!) {
                    purchaseItem(storeItemId: $storeItemId)
                }
            """

            variables = {"storeItemId": store_item_id}
            result = await self._execute_query(mutation_str, variables)
            return result.get("purchaseItem", False)
        except Exception as e:
            print(f"Purchase item failed: {str(e)}")
            return False

    async def request_store_item_for_publish(self, store_item_id: str, token: str) -> bool:  # noqa: E501
        """
        Requests a store item for publication.

        Args:
            store_item_id (str): Store item ID
            token (str): Authentication token

        Returns:
            bool: True if request succeeded, False otherwise
        """
        try:
            mutation_str = """
                mutation RequestStoreItemForPublish($storeItemId: ID!) {
                    requestStoreItemForPublish(storeItemId: $storeItemId)
                }
            """

            variables = {"storeItemId": store_item_id}
            result = await self._execute_query(mutation_str, variables)
            return result.get("requestStoreItemForPublish", False)
        except Exception as e:
            print(f"Request store item for publish failed: {str(e)}")
            return False

    async def toggle_featured_item_state(self, store_item_id: str, state: bool, token: str) -> bool:  # noqa: E501
        """
        Toggles the featured state of a store item.

        Args:
            store_item_id (str): Store item ID
            state (bool): Featured state to set
            token (str): Authentication token

        Returns:
            bool: True if toggle succeeded, False otherwise
        """
        try:
            mutation_str = """
                mutation ToggleFeaturedItemState($storeItemId: ID!, $state: Boolean!) {  # noqa: E501
                    toggleFeaturedItemState(storeItemId: $storeItemId, state: $state)
                }
            """

            variables = {"storeItemId": store_item_id, "state": state}
            result = await self._execute_query(mutation_str, variables)
            return result.get("toggleFeaturedItemState", False)
        except Exception as e:
            print(f"Toggle featured item state failed: {str(e)}")
            return False

    # Admin Mutation Operations
    async def approve_store_item_submission(
        self, submission_id: str, token: str
    ) -> Optional[StoreItemSubmission]:
        """
        Approves a store item submission.

        Args:
            submission_id (str): Submission ID to approve
            token (str): Authentication token

        Returns:
            Optional[StoreItemSubmission]: Approved submission or None if failed  # noqa: E501
        """
        try:
            mutation_str = """
                mutation ApproveStoreItemSubmission($submissionId: String!) {
                    approveStoreItemSubmission(submissionId: $submissionId) {
                        id
                        storeItemId
                        versionId
                        status
                        rejectionNote
                        submittedAt
                        reviewedAt
                    }
                }
            """

            variables = {"submissionId": submission_id}
            result = await self._execute_query(mutation_str, variables)
            return result.get("approveStoreItemSubmission")
        except Exception as e:
            print(f"Approve store item submission failed: {str(e)}")
            return None

    async def reject_store_item_submission(
        self, submission_id: str, reason: str, token: str
    ) -> Optional[StoreItemSubmission]:
        """
        Rejects a store item submission with a reason.

        Args:
            submission_id (str): Submission ID to reject
            reason (str): Rejection reason
            token (str): Authentication token

        Returns:
            Optional[StoreItemSubmission]: Rejected submission or None if failed  # noqa: E501
        """
        try:
            mutation_str = """
                mutation RejectStoreItemSubmission($submissionId: String!, $reason: String!) {  # noqa: E501
                    rejectStoreItemSubmission(submissionId: $submissionId, reason: $reason) {
                        id
                        storeItemId
                        versionId
                        status
                        rejectionNote
                        submittedAt
                        reviewedAt
                    }
                }
            """

            variables = {"submissionId": submission_id, "reason": reason}
            result = await self._execute_query(mutation_str, variables)
            return result.get("rejectStoreItemSubmission")
        except Exception as e:
            print(f"Reject store item submission failed: {str(e)}")
            return None

    async def approve_publish_item(self, item_id: str, token: str) -> bool:
        """
        Approves a publish item request (simpler approval workflow).

        Args:
            item_id (str): ID of the item to approve
            token (str): Authentication token

        Returns:
            bool: True if approval succeeded, False otherwise
        """
        try:
            mutation_str = """
                mutation ApprovePublishItem($id: String!) {
                    approvePublishItem(id: $id)
                }
            """

            variables = {"id": item_id}
            result = await self._execute_query(mutation_str, variables)
            return result.get("approvePublishItem", False)
        except Exception as e:
            print(f"Approve publish item failed: {str(e)}")
            return False

    async def reject_publish_item(self, submission_id: str, reason: str, token: str) -> bool:  # noqa: E501
        """
        Rejects a publish item request (simpler rejection workflow).

        Args:
            submission_id (str): ID of the submission to reject
            reason (str): Reason for rejection
            token (str): Authentication token

        Returns:
            bool: True if rejection succeeded, False otherwise
        """
        try:
            mutation_str = """
                mutation RejectPublishItem($submissionId: String!, $reason: String!) {  # noqa: E501
                    rejectPublishItem(submissionId: $submissionId, reason: $reason)
                }
            """

            variables = {"submissionId": submission_id, "reason": reason}
            result = await self._execute_query(mutation_str, variables)
            return result.get("rejectPublishItem", False)
        except Exception as e:
            print(f"Reject publish item failed: {str(e)}")
            return False

    async def toggle_current_active_version(
        self, version_id: str, store_item_id: str, token: str
    ) -> bool:
        """
        Toggles the current active version of a store item.

        Args:
            version_id (str): ID of the version to make active
            store_item_id (str): ID of the store item
            token (str): Authentication token

        Returns:
            bool: True if toggle succeeded, False otherwise
        """
        try:
            mutation_str = """
                mutation ToggleCurrentActiveVersionOfTheStoreItem(
                    $versionId: ID!
                    $storeItemId: ID!
                ) {
                    toggleCurrentActiveVersionOfTheStoreItem(
                        versionId: $versionId
                        storeItemId: $storeItemId
                    )
                }
            """

            variables = {"versionId": version_id, "storeItemId": store_item_id}
            result = await self._execute_query(mutation_str, variables)
            return result.get("toggleCurrentActiveVersionOfTheStoreItem", False)
        except Exception as e:
            print(f"Toggle current active version failed: {str(e)}")
            return False

    async def create_categories(self, category_names: List[str], token: str) -> bool:
        """
        Creates new store categories.

        Args:
            category_names (List[str]): List of category names to create
            token (str): Authentication token

        Returns:
            bool: True if category creation succeeded, False otherwise
        """
        try:
            mutation_str = """
                mutation CreateCategories($input: CreateCategoriesInput!) {
                    createCategories(input: $input)
                }
            """

            variables = {"input": {"names": category_names}}
            result = await self._execute_query(mutation_str, variables)
            return result.get("createCategories", False)
        except Exception as e:
            print(f"Create categories failed: {str(e)}")
            return False

    # Version Management Operations
    async def rollback_store_item_version(
        self, rollback_input: RollbackStoreItemVersionInput, token: str
    ) -> dict:
        """
        Rolls back a store item to a previous version.

        Args:
            rollback_input (RollbackStoreItemVersionInput): Rollback parameters
            token (str): Authentication token

        Returns:
            dict: Rollback result with success status and message
        """
        try:
            mutation_str = """
                mutation RollbackStoreItemVersion($input: RollbackStoreItemVersionInput!) {  # noqa: E501
                    rollbackStoreItemVersion(input: $input) {
                        success
                        message
                        newActiveVersion
                    }
                }
            """

            variables = {"input": rollback_input}
            result = await self._execute_query(mutation_str, variables)
            return result.get(
                "rollbackStoreItemVersion",
                {
                    "success": False,
                    "message": "Rollback failed",
                    "newActiveVersion": "",
                },
            )
        except Exception as e:
            print(f"Rollback store item version failed: {str(e)}")
            return {
                "success": False,
                "message": f"Rollback failed: {str(e)}",
                "newActiveVersion": "",
            }

    async def compare_store_item_versions(
        self, compare_input: CompareVersionsInput, token: str
    ) -> Optional[dict]:
        """
        Compares two versions of a store item.

        Args:
            compare_input (CompareVersionsInput): Comparison parameters
            token (str): Authentication token

        Returns:
            Optional[dict]: Version comparison result or None if failed
        """
        try:
            query_str = """
                query CompareStoreItemVersions($input: CompareVersionsInput!) {
                    compareStoreItemVersions(input: $input) {
                        storeItem {
                            id
                            name
                        }
                        sourceVersion {
                            id
                            version
                            description
                        }
                        targetVersion {
                            id
                            version
                            description
                        }
                        differences {
                            name {
                                changed
                                sourceValue
                                targetValue
                            }
                            description {
                                changed
                                sourceValue
                                targetValue
                            }
                        }
                    }
                }
            """

            variables = {"input": compare_input}
            result = await self._execute_query(query_str, variables)
            return result.get("compareStoreItemVersions")
        except Exception as e:
            print(f"Compare store item versions failed: {str(e)}")
            return None


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
