"""
Newsletter Client for Bigconsole SDK.

Provides access to newsletter management functionality including subscriptions,
campaigns, and email distribution.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from ..client.base_client import BaseGraphQLClient


class NewsletterModule:
    """
    Client for managing newsletters and email campaigns.

    Provides methods to manage subscriptions, create campaigns,
    and track newsletter performance with proper authentication and error handling.
    """

    def __init__(self, client: "BaseGraphQLClient"):
        """
        Initialize the Newsletter module.

        Args:
            client: The base GraphQL client
        """
        self.client = client

    async def _execute_query(self, query: str, variables: dict = None):
        """Execute a GraphQL query using the base client."""
        return await self.client.request(query, variables or {})

    async def subscribe(
        self, email: str, workspace_id: str, preferences: Optional[Dict[str, Any]] = None  # noqa: E501
    ) -> Dict[str, Any]:
        """
        Subscribe an email to the newsletter.

        Args:
            email: Email address to subscribe
            workspace_id: The ID of the workspace
            preferences: Optional subscription preferences

        Returns:
            Dict[str, Any]: Subscription details
        """
        mutation = """
            mutation Subscribe($input: SubscribeInput!) {
                subscribe(input: $input) {
                    id
                    email
                    workspaceId
                    status
                    preferences
                    subscribedAt
                }
            }
        """
        input_data = {"email": email, "workspaceId": workspace_id}
        if preferences:
            input_data["preferences"] = preferences

        result = await self._execute_query(mutation, {"input": input_data})
        return result.get("subscribe", {})

    async def unsubscribe(self, email: str, workspace_id: str) -> bool:
        """
        Unsubscribe an email from the newsletter.

        Args:
            email: Email address to unsubscribe
            workspace_id: The ID of the workspace

        Returns:
            bool: True if unsubscribed successfully
        """
        mutation = """
            mutation Unsubscribe($email: String!, $workspaceId: ID!) {
                unsubscribe(email: $email, workspaceId: $workspaceId)
            }
        """
        result = await self._execute_query(
            mutation, {"email": email, "workspaceId": workspace_id}
        )
        return result.get("unsubscribe", False)

    async def get_subscribers(
        self, workspace_id: str, status: Optional[str] = None, limit: Optional[int] = None  # noqa: E501
    ) -> List[Dict[str, Any]]:
        """
        Get newsletter subscribers for a workspace.

        Args:
            workspace_id: The ID of the workspace
            status: Optional filter by status ("active", "unsubscribed", "bounced")
            limit: Maximum number of subscribers to return

        Returns:
            List[Dict[str, Any]]: List of subscribers
        """
        query = """
            query GetSubscribers($workspaceId: ID!, $status: String, $limit: Int) {
                getSubscribers(workspaceId: $workspaceId, status: $status, limit: $limit) {  # noqa: E501
                    id
                    email
                    workspaceId
                    status
                    preferences
                    subscribedAt
                    unsubscribedAt
                }
            }
        """
        variables = {"workspaceId": workspace_id, "status": status, "limit": limit}
        result = await self._execute_query(query, variables)
        return result.get("getSubscribers", [])

    async def update_subscription_preferences(
        self, email: str, workspace_id: str, preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update subscription preferences for an email.

        Args:
            email: Email address
            workspace_id: The ID of the workspace
            preferences: New preferences

        Returns:
            Dict[str, Any]: Updated subscription details
        """
        mutation = """
            mutation UpdateSubscriptionPreferences($input: UpdatePreferencesInput!) {
                updateSubscriptionPreferences(input: $input) {
                    id
                    email
                    preferences
                    updatedAt
                }
            }
        """
        input_data = {"email": email, "workspaceId": workspace_id, "preferences": preferences}  # noqa: E501
        result = await self._execute_query(mutation, {"input": input_data})
        return result.get("updateSubscriptionPreferences", {})

    async def create_campaign(
        self,
        workspace_id: str,
        name: str,
        subject: str,
        content: str,
        schedule_at: Optional[str] = None,
        segment: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a newsletter campaign.

        Args:
            workspace_id: The ID of the workspace
            name: Campaign name
            subject: Email subject line
            content: Email content (HTML)
            schedule_at: Optional scheduled send time (ISO 8601 format)
            segment: Optional subscriber segment filter

        Returns:
            Dict[str, Any]: Campaign details
        """
        mutation = """
            mutation CreateCampaign($input: CreateCampaignInput!) {
                createCampaign(input: $input) {
                    id
                    workspaceId
                    name
                    subject
                    content
                    status
                    scheduleAt
                    segment
                    createdAt
                }
            }
        """
        input_data = {
            "workspaceId": workspace_id,
            "name": name,
            "subject": subject,
            "content": content,
        }
        if schedule_at:
            input_data["scheduleAt"] = schedule_at
        if segment:
            input_data["segment"] = segment

        result = await self._execute_query(mutation, {"input": input_data})
        return result.get("createCampaign", {})

    async def get_campaigns(self, workspace_id: str) -> List[Dict[str, Any]]:
        """
        Get all campaigns for a workspace.

        Args:
            workspace_id: The ID of the workspace

        Returns:
            List[Dict[str, Any]]: List of campaigns
        """
        query = """
            query GetCampaigns($workspaceId: ID!) {
                getCampaigns(workspaceId: $workspaceId) {
                    id
                    workspaceId
                    name
                    subject
                    status
                    scheduleAt
                    sentAt
                    createdAt
                }
            }
        """
        result = await self._execute_query(query, {"workspaceId": workspace_id})
        return result.get("getCampaigns", [])

    async def get_campaign_by_id(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific campaign by ID.

        Args:
            campaign_id: The ID of the campaign

        Returns:
            Optional[Dict[str, Any]]: Campaign details or None if not found
        """
        query = """
            query GetCampaignById($id: ID!) {
                getCampaignById(id: $id) {
                    id
                    workspaceId
                    name
                    subject
                    content
                    status
                    scheduleAt
                    sentAt
                    segment
                    stats {
                        sent
                        delivered
                        opened
                        clicked
                        bounced
                        unsubscribed
                    }
                    createdAt
                    updatedAt
                }
            }
        """
        result = await self._execute_query(query, {"id": campaign_id})
        return result.get("getCampaignById")

    async def send_campaign(self, campaign_id: str) -> bool:
        """
        Send a campaign immediately.

        Args:
            campaign_id: The ID of the campaign to send

        Returns:
            bool: True if campaign was queued for sending
        """
        mutation = """
            mutation SendCampaign($id: ID!) {
                sendCampaign(id: $id)
            }
        """
        result = await self._execute_query(mutation, {"id": campaign_id})
        return result.get("sendCampaign", False)

    async def cancel_campaign(self, campaign_id: str) -> bool:
        """
        Cancel a scheduled campaign.

        Args:
            campaign_id: The ID of the campaign to cancel

        Returns:
            bool: True if campaign was cancelled successfully
        """
        mutation = """
            mutation CancelCampaign($id: ID!) {
                cancelCampaign(id: $id)
            }
        """
        result = await self._execute_query(mutation, {"id": campaign_id})
        return result.get("cancelCampaign", False)

    async def delete_campaign(self, campaign_id: str) -> bool:
        """
        Delete a campaign.

        Args:
            campaign_id: The ID of the campaign to delete

        Returns:
            bool: True if campaign was deleted successfully
        """
        mutation = """
            mutation DeleteCampaign($id: ID!) {
                deleteCampaign(id: $id)
            }
        """
        result = await self._execute_query(mutation, {"id": campaign_id})
        return result.get("deleteCampaign", False)

    async def get_campaign_stats(self, campaign_id: str) -> Dict[str, Any]:
        """
        Get statistics for a campaign.

        Args:
            campaign_id: The ID of the campaign

        Returns:
            Dict[str, Any]: Campaign statistics
        """
        query = """
            query GetCampaignStats($id: ID!) {
                getCampaignStats(id: $id) {
                    campaignId
                    sent
                    delivered
                    opened
                    clicked
                    bounced
                    unsubscribed
                    openRate
                    clickRate
                    bounceRate
                    unsubscribeRate
                }
            }
        """
        result = await self._execute_query(query, {"id": campaign_id})
        return result.get("getCampaignStats", {})

    async def create_template(
        self, workspace_id: str, name: str, subject: str, content: str
    ) -> Dict[str, Any]:
        """
        Create an email template.

        Args:
            workspace_id: The ID of the workspace
            name: Template name
            subject: Email subject line
            content: Email content (HTML)

        Returns:
            Dict[str, Any]: Template details
        """
        mutation = """
            mutation CreateTemplate($input: CreateTemplateInput!) {
                createTemplate(input: $input) {
                    id
                    workspaceId
                    name
                    subject
                    content
                    createdAt
                }
            }
        """
        input_data = {
            "workspaceId": workspace_id,
            "name": name,
            "subject": subject,
            "content": content,
        }
        result = await self._execute_query(mutation, {"input": input_data})
        return result.get("createTemplate", {})

    async def get_templates(self, workspace_id: str) -> List[Dict[str, Any]]:
        """
        Get all email templates for a workspace.

        Args:
            workspace_id: The ID of the workspace

        Returns:
            List[Dict[str, Any]]: List of templates
        """
        query = """
            query GetTemplates($workspaceId: ID!) {
                getTemplates(workspaceId: $workspaceId) {
                    id
                    workspaceId
                    name
                    subject
                    createdAt
                    updatedAt
                }
            }
        """
        result = await self._execute_query(query, {"workspaceId": workspace_id})
        return result.get("getTemplates", [])

    async def delete_template(self, template_id: str) -> bool:
        """
        Delete an email template.

        Args:
            template_id: The ID of the template to delete

        Returns:
            bool: True if template was deleted successfully
        """
        mutation = """
            mutation DeleteTemplate($id: ID!) {
                deleteTemplate(id: $id)
            }
        """
        result = await self._execute_query(mutation, {"id": template_id})
        return result.get("deleteTemplate", False)
