"""
TestRunGroup model class for TestZeus test run group entities.
"""

from typing import Any, Dict, List, Optional

from testzeus_sdk.models.base import BaseModel


class TestRunGroup(BaseModel):
    """
    Model class for TestZeus test run group entities.

    This class represents a test run group entity in TestZeus, which contains
    information about a collection of test runs executed together.
    """

    def __init__(self, data: Dict[str, Any]):
        """
        Initialize a TestRunGroup model with data from the API.

        Args:
            data: Dictionary containing test run group data
        """
        super().__init__(data)

        self.name: str = data.get("name")
        self.display_name: Optional[str] = data.get("display_name")
        self.metadata: Optional[Dict[str, Any]] = data.get("metadata")
        self.tenant: str = data.get("tenant")
        self.created_by: str = data.get("created_by")
        self.execution_mode: str = data.get("execution_mode")
        self.tags: Optional[List[str]] = data.get("tags", [])
        self.test_ids: Optional[List[str]] = data.get("test_ids", [])
        self.environment: Optional[str] = data.get("environment")
        self.notification_channels: Optional[List[str]] = data.get("notification_channels", [])
        self.test_report_run: Optional[str] = data.get("test_report_run")
        self.test_runs_status: Optional[Dict[str, Any]] = data.get("test_runs_status")
        self.test_runs_ctrf_status: Optional[Dict[str, Any]] = data.get("test_runs_ctrf_status")
        self.test_runs_is_ctrf_generated: Optional[Dict[str, Any]] = data.get("test_runs_is_ctrf_generated")
        self.status: Optional[str] = data.get("status")
        self.ctrf_status: Optional[str] = data.get("ctrf_status")
        self.isCtrf_generated: Optional[bool] = data.get("isCtrf_generated", False)
        self.is_live_trigger: Optional[bool] = data.get("is_live_trigger", False)

    def is_running(self) -> bool:
        """
        Check if the test run group is currently running.

        Returns:
            True if test run group is in running status
        """
        return self.status == "running"

    def is_completed(self) -> bool:
        """
        Check if the test run group has completed.

        Returns:
            True if test run group is in completed status
        """
        return self.status == "completed"

    def is_failed(self) -> bool:
        """
        Check if the test run group has failed.

        Returns:
            True if test run group is in failed status
        """
        return self.status == "failed"

    def is_crashed(self) -> bool:
        """
        Check if the test run group has crashed.

        Returns:
            True if test run group is in crashed status
        """
        return self.status == "crashed"

    def is_cancelled(self) -> bool:
        """
        Check if the test run group was cancelled.

        Returns:
            True if test run group is in cancelled status
        """
        return self.status == "cancelled"

    def is_pending(self) -> bool:
        """
        Check if the test run group is pending.

        Returns:
            True if test run group is in pending status
        """
        return self.status == "pending"

    def get_test_count(self) -> int:
        """
        Get the number of tests in this group.

        Returns:
            Number of tests in the group
        """
        return len(self.test_ids) if self.test_ids else 0

    def is_strict_mode(self) -> bool:
        """
        Check if the group is configured to run in strict execution mode.

        Returns:
            True if execution_mode is 'strict'
        """
        return self.execution_mode == "strict"

    def is_lenient_mode(self) -> bool:
        """
        Check if the group is configured to run in lenient execution mode.

        Returns:
            True if execution_mode is 'lenient'
        """
        return self.execution_mode == "lenient"

