"""
Extension manager class for TestZeus extension operations.
"""

from testzeus_sdk.client import TestZeusClient
from testzeus_sdk.managers.base import BaseManager
from testzeus_sdk.models.extension import Extension


class ExtensionManager(BaseManager[Extension]):
    """
    Manager class for TestZeus extension entities.

    This class provides CRUD operations for working with extension entities.
    """

    def __init__(self, client: TestZeusClient) -> None:
        """
        Initialize an ExtensionManager.

        Args:
            client: TestZeus client instance
        """
        super().__init__(client, "extension", Extension)

