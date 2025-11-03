"""
TestReportDashRun model class for TestZeus test report dash run entities.
"""

from typing import Any, Dict, Optional

from testzeus_sdk.models.base import BaseModel


class TestReportDashRun(BaseModel):
    """
    Model class for TestZeus test report dash run entities.

    This class represents a test report dash run instance in TestZeus.
    """

    def __init__(self, data: Dict[str, Any]):
        """
        Initialize a TestReportDashRun model with data from the API.

        Args:
            data: Dictionary containing test report dash run data
        """
        super().__init__(data)

        self.metadata: Optional[Dict[str, Any]] = data.get("metadata")
        self.name: str = data.get("name")
        self.display_name: Optional[str] = data.get("display_name")
        self.status: str = data.get("status")
        self.tenant: str = data.get("tenant")
        self.modified_by: str = data.get("modified_by")
        self.schedule: Optional[str] = data.get("schedule")
        self.test_report_run: Optional[str] = data.get("test_report_run")
        self.test_run_dash: Optional[str] = data.get("test_run_dash")
        self.ai_findings: Optional[str] = data.get("ai_findings")
        self.isCtrf_generated: Optional[bool] = data.get("isCtrf_generated", False)
        self.ctrf_report: Optional[Dict[str, Any]] = data.get("ctrf_report")
        self.ctrf_status: Optional[str] = data.get("ctrf_status")

    def is_completed(self) -> bool:
        """Check if the dash run is completed."""
        return self.status == "completed"

    def is_running(self) -> bool:
        """Check if the dash run is currently running."""
        return self.status == "running"

    def is_pending(self) -> bool:
        """Check if the dash run is pending."""
        return self.status == "pending"

    def has_error(self) -> bool:
        """Check if the dash run has an error."""
        return self.status == "error"

    def has_ctrf_report(self) -> bool:
        """Check if CTRF report is generated."""
        return self.isCtrf_generated and self.ctrf_report is not None

