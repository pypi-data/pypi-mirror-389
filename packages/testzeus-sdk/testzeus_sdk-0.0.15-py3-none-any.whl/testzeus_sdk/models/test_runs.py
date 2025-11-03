"""
Model for test_runs collection.
"""

from typing import Any, Dict

from .base import BaseModel


class TestRuns(BaseModel):
    """
    TestRuns model for test_runs collection
    """

    def __init__(self, data: Dict[str, Any]):
        """
        Initialize a TestRuns instance

        Args:
            data: Dictionary containing model data
        """
        super().__init__(data)
        self.metadata = data.get("metadata")
        self.name = data.get("name")
        self.display_name = data.get("display_name")
        self.status = data.get("status")
        self.tenant = data.get("tenant")
        self.modified_by = data.get("modified_by")
        self.test = data.get("test")
        self.test_run_group = data.get("test_run_group")
        self.test_report_run = data.get("test_report_run")
        self.end_time = data.get("end_time")
        self.config = data.get("config")
        self.test_params = data.get("test_params")
        self.test_data = data.get("test_data")
        self.test_feature = data.get("test_feature")
        self.test_run_stage = data.get("test_run_stage")
        self.test_status = data.get("test_status")
        self.tags = data.get("tags")
        self.environment = data.get("environment")
        self.execution_mode = data.get("execution_mode")
        self.isCtrf_generated = data.get("isCtrf_generated")
        self.ctrf_status = data.get("ctrf_status")
        self.ctrf_data = data.get("ctrf_data")
        self.is_live_trigger = data.get("is_live_trigger")
        self.test_feature_reference = data.get("test_feature_reference")
        self.start_time = data.get("start_time")
