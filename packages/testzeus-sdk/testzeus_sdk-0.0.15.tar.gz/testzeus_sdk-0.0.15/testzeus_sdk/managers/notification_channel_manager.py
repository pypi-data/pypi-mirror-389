"""
NotificationChannel manager class for TestZeus notification channel operations.
"""

from testzeus_sdk.client import TestZeusClient
from testzeus_sdk.managers.base import BaseManager
from testzeus_sdk.models.notification_channel import NotificationChannel
from typing import Literal, TypedDict

class SlackConfig(TypedDict):
    token: str
    channel_id: str

class NotificationChannelManager(BaseManager[NotificationChannel]):
    """
    Manager class for TestZeus notification channel entities.

    This class provides CRUD operations for working with notification channel entities.
    """

    def __init__(self, client: TestZeusClient) -> None:
        """
        Initialize a NotificationChannelManager.

        Args:
            client: TestZeus client instance
        """
        super().__init__(client, "notification_channels", NotificationChannel)


    async def create_notification_channel(
            self, 
            name: str,
            emails: list[str], 
            display_name: str = None,
            tenant: str = None, 
            created_by: str = None, 
            webhooks: list[str] = None, 
            slack: SlackConfig = None, 
            jira: dict[str, any] = None,
            is_active: bool = True,
            is_default: bool = True
        ) -> NotificationChannel:
        """
        Create a new notification channel.
        Args:
            name: Name of the notification channel
            display_name: Display name of the notification channel
            tenant: Tenant ID (optional, will use authenticated tenant if not provided)
            created_by: user ID (optional, will use authenticated user if not provided)
            emails: list of emails
            webhooks: list of webhooks
            slack: dictionary of slack config with token and channel_id
            example: {"token": "xoxb-your-token", "channel_id": "C0605HWSGNN"}
            jira: dictionary of jira config with project_key and issue_type
            example: {"project_key": "TEST", "issue_type": "Task"}
            is_active: Set as active notification channel (default: True)
            is_default: Set as default notification channel (default: True)
        Returns:
            NotificationChannel: The created notification channel
        """
        data = {}
        if name:
            data["name"] = name
        else:
            raise ValueError(f"Name is required to create a notification channel")
        if display_name:
            data["display_name"] = display_name
        if tenant:
            data["tenant"] = tenant
        if created_by:
            data["created_by"] = created_by
            data["modified_by"] = created_by
        else:
            data["created_by"] = self.client.get_user_id()
        if emails:
            data["emails"] = {"emails": emails}
        if webhooks:
            data["webhooks"] = {"webhooks": webhooks}
        if slack:
            data["slack"] = {"slack_configs": [slack]}
        if jira:
            data["jira"] = jira
        if is_active:
            data["is_active"] = is_active
        if is_default:
            data["is_default"] = is_default
        return await super().create(data)
    
    async def update_notification_channel(
        self,
        id_or_name: str,
        name: str = None,
        display_name: str = None,
        tenant: str = None,
        created_by: str = None,
        emails: list[str] = None,
        webhooks: list[str] = None,
        slack: SlackConfig = None,
        jira: dict[str, any] = None,
        is_active: bool = True,
        is_default: bool = True
    ) -> NotificationChannel:
        """
        Update a notification channel.
        Args:
            id_or_name: ID or name of the notification channel
            name: Name of the notification channel
            display_name: Display name of the notification channel
            tenant: Tenant ID (optional, will use authenticated tenant if not provided)
            created_by: user ID (optional, will use authenticated user if not provided)
            emails: list of emails
            webhooks: list of webhooks
            slack: dictionary of slack config with token and channel_id
            example: {"token": "xoxb-your-token", "channel_id": "C0605HWSGNN"}
            jira: dictionary of jira config with project_key and issue_type
            example: {"project_key": "TEST", "issue_type": "Task"}
            is_active: Set as active notification channel (default: True)
            is_default: Set as default notification channel (default: True)
        Returns:
            NotificationChannel: The updated notification channel
        """
        data = {}
        if name:
            data["name"] = name
        if display_name:
            data["display_name"] = display_name
        if tenant:
            data["tenant"] = tenant
        if created_by:
            data["created_by"] = created_by
            data["modified_by"] = created_by
        else:
            data["created_by"] = self.client.get_user_id()
        if emails:
            data["emails"] = {"emails": emails}
        if webhooks:
            data["webhooks"] = {"webhooks": webhooks}
        if slack:
            data["slack"] = {"slack_configs": [slack]}
        if jira:
            data["jira"] = jira
        if is_active:
            data["is_active"] = is_active
        if is_default:
            data["is_default"] = is_default
        return await super().update(id_or_name, data)
    
    async def remove_config(
        self,
        id_or_name: str,
        config_type: Literal["webhook", "slack", "jira"]
    ) -> NotificationChannel:
        """
        Remove a configuration from a notification channel.
        Args:
            id_or_name: ID or name of the notification channel
            config_type: Type of configuration to remove
        Returns:
            NotificationChannel: The updated notification channel
        """
        data = {}
        if config_type == "webhook":
            data["webhooks"] = None
        elif config_type == "slack":
            data["slack"] = None
        elif config_type == "jira":
            data["jira"] = None
        return await super().update(id_or_name, data)