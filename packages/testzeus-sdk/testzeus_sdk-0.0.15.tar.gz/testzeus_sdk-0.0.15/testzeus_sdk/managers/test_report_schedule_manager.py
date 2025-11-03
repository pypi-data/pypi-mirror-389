"""
TestReportSchedule manager class for TestZeus test report schedule operations.
"""

from testzeus_sdk.client import TestZeusClient
from testzeus_sdk.managers.base import BaseManager
from testzeus_sdk.models.test_report_schedule import TestReportSchedule
from datetime import datetime, timezone
from dateutil import parser
from typing import TypedDict

class FilterTimeIntervals(TypedDict):
    start_time: str
    end_time: str

class TestReportScheduleManager(BaseManager[TestReportSchedule]):
    """
    Manager class for TestZeus test report schedule entities.

    This class provides CRUD operations for working with test report schedule entities.
    """

    def __init__(self, client: TestZeusClient) -> None:
        """
        Initialize a TestReportScheduleManager.

        Args:
            client: TestZeus client instance
        """
        super().__init__(client, "test_report_schedule", TestReportSchedule)
    
    async def create_test_report_schedule(
            self, 
            name: str, 
            is_active: bool = True,
            filter_name_pattern: str = None, 
            filter_time_intervals: FilterTimeIntervals = None, 
            cron_expression: str = None, 
            filter_tags: list[str] = None, 
            filter_tag_pattern: str = None,
            filter_env: list[str] = None, 
            filter_env_pattern: str = None,
            filter_test_data: list[str] = None, 
            filter_test_data_pattern: str = None, 
            notification_channels: list[str] = None
        ) -> TestReportSchedule:
        """
        Create a new test report schedule.
        Args:
            name: Name of the test report schedule
            is_active: Set as active test report schedule (default: True)
            filter_name_pattern: Filter using TestRun name pattern
            filter_time_intervals: Filter using time intervals (mutually exclusive with cron_expression)
            example: {"start_time": "2025-01-01 00:00:00", "end_time": "2025-01-01 01:00:00"}
            cron_expression: Cron expression (mutually exclusive with filter_time_intervals)
            filter_tags: Filter using tags (mutually exclusive with filter_tag_pattern)
            filter_tag_pattern: Filter using tag pattern (mutually exclusive with filter_tags)
            filter_env: Filter using environments (mutually exclusive with filter_env_pattern)
            filter_env_pattern: Filter using environment pattern (mutually exclusive with filter_env)
            filter_test_data: Filter using test data (mutually exclusive with filter_test_data_pattern)
            filter_test_data_pattern: Filter test data pattern (mutually exclusive with filter_test_data)
            notification_channels: Filter notification channels
        Returns:
            TestReportSchedule: The created test report schedule
        Raises:
            ValueError: If validation rules are violated or creation fails
        """
    
        if not name:
            raise ValueError("Name is required to create a test report schedule")
            
        # --- Validate filters ---
        # Rule 1: either filter_time_intervals or cron_expression could be provided
        if filter_time_intervals and cron_expression:
            raise ValueError("Cannot provide both filter_time_intervals and cron_expression. Choose one.")
        
        # Rule 2: either filter_tags or filter_tag_pattern could be provided
        if filter_tags and filter_tag_pattern:
            raise ValueError("Cannot provide both filter_tags and filter_tag_pattern. Choose one.")
        
        # Rule 3: either filter_env or filter_env_pattern could be provided
        if filter_env and filter_env_pattern:
            raise ValueError("Cannot provide both filter_env and filter_env_pattern. Choose one.")
        
        # Rule 4: either filter_test_data or filter_test_data_pattern could be provided
        if filter_test_data and filter_test_data_pattern:
            raise ValueError("Cannot provide both filter_test_data and filter_test_data_pattern. Choose one.")

        # Check that at least one filter is provided
        has_filters = any([
            filter_name_pattern,
            filter_time_intervals,
            cron_expression,
            filter_tags,
            filter_tag_pattern,
            filter_env,
            filter_env_pattern,
            filter_test_data,
            filter_test_data_pattern,
        ])

        if not has_filters:
            raise ValueError("At least one filter is required to create a test report schedule")
        
        data = {
            "name": name,
            "created_by": self.client.get_user_id() or await self.client.get_user_id_async(),
        }

        # Handle async lookups for tags, environments, and test_data
        if filter_tags:
            data["filter_tags"] = await self._find_record_id_by_name(filter_tags, "tags")

        if filter_env:
            data["filter_env"] = await self._find_record_id_by_name(filter_env, "environments")

        if filter_test_data:
            data["filter_test_data"] = await self._find_record_id_by_name(filter_test_data, "test_data")
        
        if notification_channels:
            data["notification_channels"] = await self._find_record_id_by_name(notification_channels, "notification_channels")

        # Add other optional fields
        optional_fields = {
            "is_active": is_active,
            "filter_name_pattern": filter_name_pattern,
            "filter_time_intervals": self._built_time_interval(filter_time_intervals["start_time"], filter_time_intervals["end_time"]) if filter_time_intervals else None,
            "cron_expression": cron_expression,
            "filter_tag_pattern": filter_tag_pattern,
            "filter_env_pattern": filter_env_pattern,
            "filter_test_data_pattern": filter_test_data_pattern,
        }

        # Add only non-empty values
        for key, value in optional_fields.items():
            if value:
                data[key] = value

        # --- Create entity ---
        try:
            result = await super().create(data)
            return result
        except Exception as e:
            raise ValueError(f"Failed to create test report schedule: {str(e)}") from e


    async def update_test_report_schedule(
        self,
        id_or_name: str,
        name: str = None,
        is_active: bool = True,
        filter_name_pattern: str = None,
        filter_time_intervals: FilterTimeIntervals = None,
        cron_expression: str = None,
        filter_tags: list[str] = None,
        filter_tag_pattern: str = None,
        filter_env: list[str] = None,
        filter_env_pattern: str = None,
        filter_test_data: list[str] = None,
        filter_test_data_pattern: str = None,
        notification_channels: list[str] = None
    ) -> TestReportSchedule:
        """
        Update a test report schedule.
        Args:
            id_or_name: ID or name of the test report schedule
            name: Name of the test report schedule
            is_active: Set as active test report schedule (default: True)
            filter_name_pattern: Filter using TestRun name pattern
            filter_time_intervals: Filter using time intervals (mutually exclusive with cron_expression)
            example: {"start_time": "2025-01-01 00:00:00", "end_time": "2025-01-01 01:00:00"}
            cron_expression: Cron expression (mutually exclusive with filter_time_intervals)
            filter_tags: Filter using tags (mutually exclusive with filter_tag_pattern)
            filter_tag_pattern: Filter using tag pattern (mutually exclusive with filter_tags)
            filter_env: Filter using environments (mutually exclusive with filter_env_pattern)
            filter_env_pattern: Filter using environment pattern (mutually exclusive with filter_env)
            filter_test_data: Filter using test data (mutually exclusive with filter_test_data_pattern)
            filter_test_data_pattern: Filter using test data pattern (mutually exclusive with filter_test_data)
            notification_channels: Filter notification channels
        Returns:
            TestReportSchedule: The updated test report schedule
        Raises:
            ValueError: If validation rules are violated or update fails
        """
        
        # --- Validate filters ---
        # Rule 1: either filter_time_intervals or cron_expression could be provided
        if filter_time_intervals and cron_expression:
            raise ValueError("Cannot provide both filter_time_intervals and cron_expression. Choose one.")
        
        # Rule 2: either filter_tags or filter_tag_pattern could be provided
        if filter_tags and filter_tag_pattern:
            raise ValueError("Cannot provide both filter_tags and filter_tag_pattern. Choose one.")
        
        # Rule 3: either filter_env or filter_env_pattern could be provided
        if filter_env and filter_env_pattern:
            raise ValueError("Cannot provide both filter_env and filter_env_pattern. Choose one.")
        
        # Rule 4: either filter_test_data or filter_test_data_pattern could be provided
        if filter_test_data and filter_test_data_pattern:
            raise ValueError("Cannot provide both filter_test_data and filter_test_data_pattern. Choose one.")
        
        data = {}
        
        # Handle async lookups for tags, environments, and test_data
        if filter_tags:
            data["filter_tags"] = await self._find_record_id_by_name(filter_tags, "tags")

        if filter_env:
            data["filter_env"] = await self._find_record_id_by_name(filter_env, "environments")

        if filter_test_data:
            data["filter_test_data"] = await self._find_record_id_by_name(filter_test_data, "test_data")

        # Add other optional fields
        optional_fields = {
            "name": name,
            "created_by": self.client.get_user_id() or await self.client.get_user_id_async(),
            "is_active": is_active,
            "filter_name_pattern": filter_name_pattern,
            "filter_time_intervals": self._built_time_interval(filter_time_intervals["start_time"], filter_time_intervals["end_time"]) if filter_time_intervals else None,
            "cron_expression": cron_expression,
            "filter_tag_pattern": filter_tag_pattern,
            "filter_env_pattern": filter_env_pattern,
            "filter_test_data_pattern": filter_test_data_pattern,
            "notification_channels": notification_channels,
        }

        for key, value in optional_fields.items():
            if value:
                data[key] = value

        try:
            result = await super().update(id_or_name, data)
            return result
        except Exception as e:
            raise ValueError(f"Failed to update test report schedule: {str(e)}") from e

    def _built_time_interval(
        self,
        start_time: str | datetime,
        end_time: str | datetime,
        tz: timezone = timezone.utc
    ) -> dict[str, str]:
        """
        Convert user-provided start and end times into a normalized UTC ISO-8601 format.

        Args:
            start_time (str | datetime): Start time (can be datetime or string) in format YYYY-MM-DD HH:MM:SS
            end_time (str | datetime): End time (can be datetime or string) in format YYYY-MM-DD HH:MM:SS
            tz (timezone, optional): Target timezone (default UTC)

        Returns:
            dict: {
                "start_time": "<ISO-8601 UTC>",
                "end_time": "<ISO-8601 UTC>"
            }

        Raises:
            ValueError: If parsing fails or times are invalid
        """
        def parse_time(value):
            if isinstance(value, datetime):
                dt = value
            else:
                # Handle various date formats
                dt = parser.parse(value)
            # Convert to UTC and format as ISO string with Z suffix
            return dt.astimezone(tz).isoformat().replace("+00:00", "Z")

        try:
            parsed_start = parse_time(start_time)
            parsed_end = parse_time(end_time)
        except Exception as e:
            raise ValueError(f"Invalid time input: {e}")

        # Validate time range
        if parser.parse(parsed_start.replace("Z", "+00:00")) >= parser.parse(parsed_end.replace("Z", "+00:00")):
            raise ValueError("start_time must be before end_time")

        return {
            "start_time": parsed_start,
            "end_time": parsed_end
        }
    
    async def _find_record_id_by_name(self, names: list[str], collection: str) -> list[str]:
        """
        Find a record by name.
        """
        if collection == "tags":
            tag_ids = []
            for name in names:
                record = await self.client.tags.get_one(name)
                tag_ids.append(record.id)
            return tag_ids
        elif collection == "environments":
            env_ids = []
            for name in names:
                record = await self.client.environments.get_one(name)
                env_ids.append(record.id)
            return env_ids
        elif collection == "test_data":
            test_data_ids = []
            for name in names:
                record = await self.client.test_data.get_one(name)
                test_data_ids.append(record.id)
            return test_data_ids
        elif collection == "notification_channels":
            notification_channel_ids = []
            for name in names:
                record = await self.client.notification_channels.get_one(name)
                notification_channel_ids.append(record.id)
            return notification_channel_ids
        else:
            raise ValueError(f"Invalid collection: {collection}")
