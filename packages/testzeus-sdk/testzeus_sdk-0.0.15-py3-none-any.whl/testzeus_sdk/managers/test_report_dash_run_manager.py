"""
TestReportDashRun manager class for TestZeus test report dash run operations.
"""

from testzeus_sdk.client import TestZeusClient
from testzeus_sdk.managers.base import BaseManager
from testzeus_sdk.models.test_report_dash_run import TestReportDashRun

class TestReportDashRunManager(BaseManager[TestReportDashRun]):
    """
    Manager class for TestZeus test report dash run entities.

    This class provides CRUD operations for working with test report dash run entities.
    """

    def __init__(self, client: TestZeusClient) -> None:
        """
        Initialize a TestReportDashRunManager.

        Args:
            client: TestZeus client instance
        """
        super().__init__(client, "test_report_dash_run", TestReportDashRun)

