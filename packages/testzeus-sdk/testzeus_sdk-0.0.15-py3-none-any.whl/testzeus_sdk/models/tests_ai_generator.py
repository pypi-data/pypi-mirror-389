"""
TestsAIGenerator model class for TestZeus tests AI generator entities.
"""

from typing import Any, Dict, List, Optional

from testzeus_sdk.models.base import BaseModel


class TestsAIGenerator(BaseModel):
    """
    Model class for TestZeus tests AI generator entities.

    This class represents a tests AI generator instance in TestZeus.
    """

    def __init__(self, data: Dict[str, Any]):
        """
        Initialize a TestsAIGenerator model with data from the API.

        Args:
            data: Dictionary containing tests AI generator data
        """
        super().__init__(data)

        self.tenant: Optional[str] = data.get("tenant")
        self.modified_by: Optional[str] = data.get("modified_by")
        self.test: Optional[str] = data.get("test")
        self.test_data: Optional[List[str]] = data.get("test_data", [])
        self.environment: Optional[str] = data.get("environment")
        self.test_feature: Optional[str] = data.get("test_feature")
        self.user_prompt: Optional[str] = data.get("user_prompt")
        self.reasoning_effort: Optional[str] = data.get("reasoning_effort")
        self.num_of_testcases: Optional[float] = data.get("num_of_testcases")
        self.submit: Optional[bool] = data.get("submit", False)
        self.metadata: Optional[Dict[str, Any]] = data.get("metadata")
        self.new_test_feature: Optional[str] = data.get("new_test_feature")

    def is_submitted(self) -> bool:
        """Check if the AI generator is submitted."""
        return self.submit is True

    def has_test_feature(self) -> bool:
        """Check if test feature is provided."""
        return self.test_feature is not None and len(self.test_feature) > 0

    def get_reasoning_level(self) -> str:
        """Get the reasoning effort level."""
        return self.reasoning_effort or "medium"

