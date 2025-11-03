"""
NotificationChannel model class for TestZeus notification channel entities.
"""

from testzeus_sdk.models.base import BaseModel


class NotificationChannel(BaseModel):
    """
    Model class for TestZeus notification channel entities.

    This class represents a notification channel entity in TestZeus, which contains
    configuration for various notification types (email, webhook, slack, jira).
    """

    def __init__(self, data: dict[str, any]):
        """
        Initialize a NotificationChannel model with data from the API.

        Args:
            data: Dictionary containing notification channel data
        """
        super().__init__(data)

        self.tenant: str = data.get("tenant")
        self.name: str = data.get("name")
        self.display_name: str = data.get("display_name")
        self.emails: dict[str, any] = data.get("emails", {})
        self.webhooks: dict[str, any] = data.get("webhooks")
        self.slack: dict[str, any] = data.get("slack")
        self.jira: dict[str, any] = data.get("jira")
        self.modified_by: str = data.get("modified_by")
        self.created_by: str = data.get("created_by")
        self.is_active: bool = data.get("is_active", False)
        self.is_default: bool = data.get("is_default", False)

    def has_email_config(self) -> bool:
        """
        Check if channel has email configuration.

        Returns:
            True if emails are configured
        """
        return bool(self.emails)

    def has_webhook_config(self) -> bool:
        """
        Check if channel has webhook configuration.

        Returns:
            True if webhooks are configured
        """
        return bool(self.webhooks)

    def has_slack_config(self) -> bool:
        """
        Check if channel has Slack configuration.

        Returns:
            True if Slack is configured
        """
        return bool(self.slack)

    def has_jira_config(self) -> bool:
        """
        Check if channel has Jira configuration.

        Returns:
            True if Jira is configured
        """
        return bool(self.jira)

    def get_enabled_channels(self) -> list:
        """
        Get list of enabled channel types.

        Returns:
            List of enabled channel type names
        """
        channels = []
        if self.has_email_config():
            channels.append("email")
        if self.has_webhook_config():
            channels.append("webhook")
        if self.has_slack_config():
            channels.append("slack")
        if self.has_jira_config():
            channels.append("jira")
        return channels

