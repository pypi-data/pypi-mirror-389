"""
Analytics Client for Bigconsole SDK.

Provides access to analytics and reporting functionality including metrics,
insights, and data analysis.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from ..client.base_client import BaseGraphQLClient


class AnalyticsModule:
    """
    Client for managing analytics and reporting.

    Provides methods to retrieve analytics data, generate reports,
    and track metrics with proper authentication and error handling.
    """

    def __init__(self, client: "BaseGraphQLClient"):
        """
        Initialize the Analytics module.

        Args:
            client: The base GraphQL client
        """
        self.client = client

    async def _execute_query(self, query: str, variables: dict = None):
        """Execute a GraphQL query using the base client."""
        return await self.client.request(query, variables or {})

    async def get_workspace_analytics(
        self,
        workspace_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        metrics: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Get analytics data for a workspace.

        Args:
            workspace_id: The ID of the workspace
            start_date: Optional start date (ISO 8601 format)
            end_date: Optional end date (ISO 8601 format)
            metrics: Optional list of specific metrics to retrieve

        Returns:
            Dict[str, Any]: Analytics data including metrics and trends
        """
        query = """
            query GetWorkspaceAnalytics($workspaceId: ID!, $startDate: String, $endDate: String, $metrics: [String!]) {  # noqa: E501
                getWorkspaceAnalytics(workspaceId: $workspaceId, startDate: $startDate, endDate: $endDate, metrics: $metrics) {  # noqa: E501
                    workspaceId
                    metrics {
                        name
                        value
                        unit
                        trend
                    }
                    timeSeries {
                        timestamp
                        values
                    }
                    summary {
                        totalUsers
                        activeUsers
                        totalProjects
                        totalResources
                    }
                }
            }
        """
        variables = {
            "workspaceId": workspace_id,
            "startDate": start_date,
            "endDate": end_date,
            "metrics": metrics,
        }
        result = await self._execute_query(query, variables)
        return result.get("getWorkspaceAnalytics", {})

    async def get_user_analytics(
        self, user_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None  # noqa: E501
    ) -> Dict[str, Any]:
        """
        Get analytics data for a specific user.

        Args:
            user_id: The ID of the user
            start_date: Optional start date (ISO 8601 format)
            end_date: Optional end date (ISO 8601 format)

        Returns:
            Dict[str, Any]: User analytics including activity and usage metrics
        """
        query = """
            query GetUserAnalytics($userId: ID!, $startDate: String, $endDate: String) {
                getUserAnalytics(userId: $userId, startDate: $startDate, endDate: $endDate) {  # noqa: E501
                    userId
                    activityCount
                    lastActive
                    topActions
                    resourcesCreated
                    projectsContributed
                }
            }
        """
        variables = {"userId": user_id, "startDate": start_date, "endDate": end_date}
        result = await self._execute_query(query, variables)
        return result.get("getUserAnalytics", {})

    async def get_product_analytics(
        self, product_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None  # noqa: E501
    ) -> Dict[str, Any]:
        """
        Get analytics data for a specific product.

        Args:
            product_id: The ID of the product
            start_date: Optional start date (ISO 8601 format)
            end_date: Optional end date (ISO 8601 format)

        Returns:
            Dict[str, Any]: Product analytics including usage and performance metrics
        """
        query = """
            query GetProductAnalytics($productId: ID!, $startDate: String, $endDate: String) {  # noqa: E501
                getProductAnalytics(productId: $productId, startDate: $startDate, endDate: $endDate) {  # noqa: E501
                    productId
                    totalUsers
                    activeUsers
                    totalWorkspaces
                    usageMetrics {
                        metric
                        value
                        change
                    }
                    popularFeatures
                }
            }
        """
        variables = {"productId": product_id, "startDate": start_date, "endDate": end_date}  # noqa: E501
        result = await self._execute_query(query, variables)
        return result.get("getProductAnalytics", {})

    async def get_usage_metrics(
        self,
        workspace_id: str,
        metric_type: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        granularity: Optional[str] = "daily",
    ) -> List[Dict[str, Any]]:
        """
        Get usage metrics for a workspace.

        Args:
            workspace_id: The ID of the workspace
            metric_type: Type of metric (e.g., "api_calls", "storage", "compute")
            start_date: Optional start date (ISO 8601 format)
            end_date: Optional end date (ISO 8601 format)
            granularity: Time granularity ("hourly", "daily", "weekly", "monthly")

        Returns:
            List[Dict[str, Any]]: List of usage metrics over time
        """
        query = """
            query GetUsageMetrics($workspaceId: ID!, $metricType: String!, $startDate: String, $endDate: String, $granularity: String) {  # noqa: E501
                getUsageMetrics(workspaceId: $workspaceId, metricType: $metricType, startDate: $startDate, endDate: $endDate, granularity: $granularity) {  # noqa: E501
                    timestamp
                    value
                    unit
                    metadata
                }
            }
        """
        variables = {
            "workspaceId": workspace_id,
            "metricType": metric_type,
            "startDate": start_date,
            "endDate": end_date,
            "granularity": granularity,
        }
        result = await self._execute_query(query, variables)
        return result.get("getUsageMetrics", [])

    async def generate_report(
        self,
        workspace_id: str,
        report_type: str,
        start_date: str,
        end_date: str,
        include_sections: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Generate an analytics report.

        Args:
            workspace_id: The ID of the workspace
            report_type: Type of report ("usage", "performance", "billing", "activity")
            start_date: Start date for the report (ISO 8601 format)
            end_date: End date for the report (ISO 8601 format)
            include_sections: Optional list of sections to include in the report

        Returns:
            Dict[str, Any]: Generated report data
        """
        mutation = """
            mutation GenerateReport($input: GenerateReportInput!) {
                generateReport(input: $input) {
                    reportId
                    reportType
                    workspaceId
                    startDate
                    endDate
                    sections {
                        title
                        data
                    }
                    generatedAt
                }
            }
        """
        input_data = {
            "workspaceId": workspace_id,
            "reportType": report_type,
            "startDate": start_date,
            "endDate": end_date,
        }
        if include_sections:
            input_data["includeSections"] = include_sections

        result = await self._execute_query(mutation, {"input": input_data})
        return result.get("generateReport", {})

    async def get_dashboard_metrics(self, workspace_id: str) -> Dict[str, Any]:
        """
        Get real-time dashboard metrics for a workspace.

        Args:
            workspace_id: The ID of the workspace

        Returns:
            Dict[str, Any]: Dashboard metrics including key performance indicators
        """
        query = """
            query GetDashboardMetrics($workspaceId: ID!) {
                getDashboardMetrics(workspaceId: $workspaceId) {
                    activeUsers
                    totalProjects
                    totalResources
                    apiCallsToday
                    storageUsed
                    storageLimit
                    alerts {
                        severity
                        message
                        timestamp
                    }
                }
            }
        """
        result = await self._execute_query(query, {"workspaceId": workspace_id})
        return result.get("getDashboardMetrics", {})

    async def track_event(
        self, event_name: str, workspace_id: str, properties: Optional[Dict[str, Any]] = None  # noqa: E501
    ) -> bool:
        """
        Track a custom analytics event.

        Args:
            event_name: Name of the event to track
            workspace_id: The ID of the workspace
            properties: Optional event properties

        Returns:
            bool: True if event was tracked successfully
        """
        mutation = """
            mutation TrackEvent($input: TrackEventInput!) {
                trackEvent(input: $input)
            }
        """
        input_data = {"eventName": event_name, "workspaceId": workspace_id}
        if properties:
            input_data["properties"] = properties

        result = await self._execute_query(mutation, {"input": input_data})
        return result.get("trackEvent", False)

    async def get_trends(
        self, workspace_id: str, metric: str, time_period: str = "30d"
    ) -> Dict[str, Any]:
        """
        Get trend analysis for a specific metric.

        Args:
            workspace_id: The ID of the workspace
            metric: The metric to analyze
            time_period: Time period for trend analysis (e.g., "7d", "30d", "90d")

        Returns:
            Dict[str, Any]: Trend analysis including direction and percentage change
        """
        query = """
            query GetTrends($workspaceId: ID!, $metric: String!, $timePeriod: String!) {
                getTrends(workspaceId: $workspaceId, metric: $metric, timePeriod: $timePeriod) {  # noqa: E501
                    metric
                    currentValue
                    previousValue
                    percentageChange
                    direction
                    dataPoints {
                        timestamp
                        value
                    }
                }
            }
        """
        variables = {"workspaceId": workspace_id, "metric": metric, "timePeriod": time_period}  # noqa: E501
        result = await self._execute_query(query, variables)
        return result.get("getTrends", {})
