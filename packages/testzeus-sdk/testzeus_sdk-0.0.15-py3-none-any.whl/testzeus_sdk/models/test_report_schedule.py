"""
TestReportSchedule model class for TestZeus test report schedule entities.
"""

from typing import Any, Dict, List, Optional

from testzeus_sdk.models.base import BaseModel


class TestReportSchedule(BaseModel):
    """
    Model class for TestZeus test report schedule entities.

    This class represents a scheduled test report configuration in TestZeus.
    """

    def __init__(self, data: Dict[str, Any]):
        """
        Initialize a TestReportSchedule model with data from the API.

        Args:
            data: Dictionary containing test report schedule data
        """
        super().__init__(data)

        self.metadata: Optional[Dict[str, Any]] = data.get("metadata")
        self.name: str = data.get("name")
        self.is_active: Optional[bool] = data.get("is_active", False)
        self.tenant: str = data.get("tenant")
        self.modified_by: str = data.get("modified_by")
        self.created_by: str = data.get("created_by")
        self.filter_name_pattern: Optional[str] = data.get("filter_name_pattern")
        self.filter_time_intervals: Optional[Dict[str, Any]] = data.get("filter_time_intervals")
        self.cron_expression: Optional[str] = data.get("cron_expression")
        self.filter_tags: Optional[List[str]] = data.get("filter_tags", [])
        self.filter_tag_pattern: Optional[str] = data.get("filter_tag_pattern")
        self.filter_env: Optional[List[str]] = data.get("filter_env", [])
        self.filter_env_pattern: Optional[str] = data.get("filter_env_pattern")
        self.filter_test_data: Optional[List[str]] = data.get("filter_test_data", [])
        self.filter_test_data_pattern: Optional[str] = data.get("filter_test_data_pattern")
        self.notification_channels: Optional[List[str]] = data.get("notification_channels", [])
        self.next_scheduled_run: Optional[str] = data.get("next_scheduled_run")
        self.last_run_at: Optional[str] = data.get("last_run_at")
        self.is_scheduled: Optional[bool] = data.get("is_scheduled", False)
        self.idempotent_key: Optional[str] = data.get("idempotent_key")
        self.allow_overlap: Optional[bool] = data.get("allow_overlap", False)
        self.scheduled_execution_at: Optional[str] = data.get("scheduled_execution_at")

    def has_cron_schedule(self) -> bool:
        """
        Check if schedule has a cron expression.

        Returns:
            True if cron_expression is configured
        """
        return bool(self.cron_expression)

    def has_delayed_execution(self) -> bool:
        """
        Check if schedule has a delayed execution time.

        Returns:
            True if scheduled_execution_at is set
        """
        return bool(self.scheduled_execution_at)

    def has_name_filter(self) -> bool:
        """
        Check if schedule has a name pattern filter.

        Returns:
            True if filter_name_pattern is set
        """
        return bool(self.filter_name_pattern)

    def has_tag_filter(self) -> bool:
        """
        Check if schedule has tag filters.

        Returns:
            True if tags or tag pattern is configured
        """
        return bool(self.filter_tags) or bool(self.filter_tag_pattern)

    def has_env_filter(self) -> bool:
        """
        Check if schedule has environment filters.

        Returns:
            True if environments or env pattern is configured
        """
        return bool(self.filter_env) or bool(self.filter_env_pattern)

    def has_test_data_filter(self) -> bool:
        """
        Check if schedule has test data filters.

        Returns:
            True if test data or test data pattern is configured
        """
        return bool(self.filter_test_data) or bool(self.filter_test_data_pattern)

    def get_active_filters(self) -> List[str]:
        """
        Get list of active filter types.

        Returns:
            List of active filter type names
        """
        filters = []
        if self.has_name_filter():
            filters.append("name")
        if self.has_tag_filter():
            filters.append("tags")
        if self.has_env_filter():
            filters.append("environment")
        if self.has_test_data_filter():
            filters.append("test_data")
        if self.filter_time_intervals:
            filters.append("time_intervals")
        return filters

