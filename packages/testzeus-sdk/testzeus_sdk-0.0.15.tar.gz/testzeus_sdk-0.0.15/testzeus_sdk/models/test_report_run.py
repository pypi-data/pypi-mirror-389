"""
TestReportRun model class for TestZeus test report run entities.
"""

from typing import Any, Dict, List, Optional

from testzeus_sdk.models.base import BaseModel


class TestReportRun(BaseModel):
    """
    Model class for TestZeus test report run entities.

    This class represents a test report run instance in TestZeus.
    """

    def __init__(self, data: Dict[str, Any]):
        """
        Initialize a TestReportRun model with data from the API.

        Args:
            data: Dictionary containing test report run data
        """
        super().__init__(data)

        self.metadata: Optional[Dict[str, Any]] = data.get("metadata")
        self.name: str = data.get("name")
        self.display_name: Optional[str] = data.get("display_name")
        self.status: str = data.get("status")
        self.tenant: str = data.get("tenant")
        self.modified_by: str = data.get("modified_by")
        self.schedule: Optional[str] = data.get("schedule")
        self.test_run_group: Optional[str] = data.get("test_run_group")
        self.trigger_time: Optional[str] = data.get("trigger_time")
        self.end_time: Optional[str] = data.get("end_time")
        self.ctrf_report: Optional[str] = data.get("ctrf_report")
        self.test_runs: Optional[List[str]] = data.get("test_runs", [])
        self.ctrf_report_findings: Optional[str] = data.get("ctrf_report_findings")
        self.pdf_report: Optional[str] = data.get("pdf_report")
        self.csv_report: Optional[str] = data.get("csv_report")
        self.zip_report: Optional[str] = data.get("zip_report")

    def is_completed(self) -> bool:
        """Check if the report run is completed."""
        return self.status == "completed"

    def is_running(self) -> bool:
        """Check if the report run is currently running."""
        return self.status == "running"

    def is_pending(self) -> bool:
        """Check if the report run is pending."""
        return self.status == "pending"

    def has_error(self) -> bool:
        """Check if the report run has an error."""
        return self.status in ["error", "failed", "crashed"]

