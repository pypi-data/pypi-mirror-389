"""
Extension model class for TestZeus extension entities.
"""

from typing import Any, Dict, Optional

from testzeus_sdk.models.base import BaseModel


class Extension(BaseModel):
    """
    Model class for TestZeus extension entities.

    This class represents an extension instance in TestZeus.
    """

    def __init__(self, data: Dict[str, Any]):
        """
        Initialize an Extension model with data from the API.

        Args:
            data: Dictionary containing extension data
        """
        super().__init__(data)

        self.name: Optional[str] = data.get("name")
        self.tenant: Optional[str] = data.get("tenant")
        self.modified_by: Optional[str] = data.get("modified_by")
        self.data_content: Optional[str] = data.get("data_content")
        self.response: Optional[str] = data.get("response")
        self.metadata: Optional[Dict[str, Any]] = data.get("metadata")
        self.submit: Optional[bool] = data.get("submit", False)

    def is_submitted(self) -> bool:
        """Check if the extension is submitted."""
        return self.submit is True

    def has_response(self) -> bool:
        """Check if the extension has a response."""
        return self.response is not None and len(self.response) > 0

