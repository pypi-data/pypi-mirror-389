"""
Manager for tests collection.
"""

import datetime
from typing import Any, Dict, List, Optional, Literal

from testzeus_sdk.client import TestZeusClient
from testzeus_sdk.models.tests import Tests

from .base import BaseManager


class TestsManager(BaseManager):
    """
    Manager for Tests resources
    """

    def __init__(self, client: TestZeusClient) -> None:
        """
        Initialize the Tests manager

        Args:
            client: TestZeus client instance
        """
        super().__init__(client, "tests", Tests)

    def _process_references(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process name-based references to ID-based references

        Args:
            data: Entity data with potential name-based references

        Returns:
            Processed data with ID-based references
        """
        from testzeus_sdk.utils.helpers import convert_name_refs_to_ids

        # Define which fields are relations and what collections they reference
        ref_fields = {
            "tenant": "pbc_138639755",
            "modified_by": "_pb_users_auth_",
            "config": "pbc_383599117",
            "test_design": "pbc_3066241075",
            "test_data": "pbc_3433119540",
            "tags": "pbc_1219621782",
            "environment": "pbc_3067608406",
        }

        return convert_name_refs_to_ids(self.client, data, ref_fields)

    async def run_test(
        self, 
        ids_or_names: List[str],
        name: str,
        environment: Optional[str] = None,
        execution_mode: Optional[Literal["lenient", "strict"]] = "lenient",
        modified_by: Optional[str] = None,
        tenant: Optional[str] = None,
        tags: Optional[List[str]] = None,
        notification_channels: Optional[List[str]] = None
    ) -> Any:
        """
        Run a test

        Args:
            ids_or_names: List of test IDs or names
            name: Name for the test run group
            execution_mode: Execution mode (optional)
            environment: Environment name or ID (optional)
            tags: List of tag names or IDs (optional)
            notification_channels: List of notification channel names or IDs (optional)
            modified_by: User ID who is modifying the test run (optional)
            tenant: Tenant ID to associate with this test run (optional)
            environment: Environment name or ID (optional)

        Returns:
            Test run result
        """

        # Get the test
        test_ids = []
        for id_or_name in ids_or_names:
            test = await self.get_one(id_or_name)
            test_ids.append(str(test.id))

        return await self.client.test_run_groups.create_and_execute(
            name=f"{name}-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}",
            test_ids=test_ids,
            execution_mode=execution_mode,
            environment=environment,
            tags=tags,
            notification_channels=notification_channels,
            created_by=modified_by,
            tenant=tenant,
        )
