"""
TestsAIGenerator manager class for TestZeus tests AI generator operations.
"""

from testzeus_sdk.client import TestZeusClient
from testzeus_sdk.managers.base import BaseManager
from testzeus_sdk.models.tests_ai_generator import TestsAIGenerator


class TestsAIGeneratorManager(BaseManager[TestsAIGenerator]):
    """
    Manager class for TestZeus tests AI generator entities.

    This class provides CRUD operations for working with tests AI generator entities.
    """

    def __init__(self, client: TestZeusClient) -> None:
        """
        Initialize a TestsAIGeneratorManager.

        Args:
            client: TestZeus client instance
        """
        super().__init__(client, "tests_ai_generator", TestsAIGenerator)

