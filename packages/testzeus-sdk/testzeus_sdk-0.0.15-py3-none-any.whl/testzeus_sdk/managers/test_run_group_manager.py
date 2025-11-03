"""
TestRunGroup manager class for TestZeus test run group operations.
"""

from typing import Any, Dict, List, Literal, Optional
from pathlib import Path
import asyncio

from testzeus_sdk.client import TestZeusClient
from testzeus_sdk.managers.base import BaseManager
from testzeus_sdk.models.test_run_group import TestRunGroup


class TestRunGroupManager(BaseManager[TestRunGroup]):
    """
    Manager class for TestZeus test run group entities.

    This class provides CRUD operations and specialized methods
    for working with test run group entities.
    """

    def __init__(self, client: TestZeusClient) -> None:
        """
        Initialize a TestRunGroupManager.

        Args:
            client: TestZeus client instance
        """
        super().__init__(client, "test_run_group", TestRunGroup)

    async def create_and_execute(
        self,
        name: str,
        test_ids: Optional[List[str]] = None,
        execution_mode: Literal["lenient", "strict"] = "lenient",
        environment: Optional[str] = None,
        tags: Optional[List[str]] = None,
        notification_channels: Optional[List[str]] = None,
        tenant: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> TestRunGroup:
        """
        Create a test run group and prepare it for execution.

        Args:
            name: Name for the test run group
            test_ids: List of test IDs to include in the group (use either test_ids OR tags, not both)
            execution_mode: Execution mode for the tests (lenient or strict)
            environment: Optional environment ID
            tags: Optional list of tag IDs to filter tests (use either test_ids OR tags, not both)
            notification_channels: Optional list of notification channel IDs
            tenant: Tenant ID (optional, will use authenticated tenant if not provided)
            created_by: User ID who is creating the group (optional, will use authenticated user if not provided)

        Returns:
            Created test run group instance
        
        Raises:
            ValueError: If both test_ids and tags are specified, or if neither is specified
        """
        if not name:
            raise ValueError("Name is required to create a test run group")
        
        # Validate that only one of test_ids or tags is specified
        if test_ids and tags:
            raise ValueError("Cannot specify both test_ids and tags - use only one")
        
        if not test_ids and not tags:
            raise ValueError("Must specify either test_ids or tags")

        # Build the group data
        group_data: Dict[str, Any] = {
            "name": name,
            "execution_mode": execution_mode,
            "status": "pending",
        }

        # Add test_ids or tags (mutually exclusive)
        if test_ids:
            group_data["test_ids"] = test_ids
        if tags:
            group_data["tags"] = tags
        
        if environment:
            group_data["environment"] = environment
        if notification_channels:
            group_data["notification_channels"] = notification_channels
        if tenant:
            group_data["tenant"] = tenant
        if created_by:
            group_data["created_by"] = created_by
            group_data["modified_by"] = created_by
        else:
            group_data["created_by"] = self.client.get_user_id()

        # Create the test run group
        return await self.create(group_data)
    

    async def cancel_group(
        self,
        id_or_name: str,
    ) -> TestRunGroup:
        """
        Cancel all running test runs in a group.

        Args:
            id_or_name: Test run group ID or name

        Returns:
            Updated test run group instance
        """
        # Get the test run group
        group = await self.get_one(id_or_name)

        if group.status not in ["pending", "running"]:
            raise ValueError(f"Test run group must be in 'pending' or 'running' status to cancel, but is in '{group.status}'")

        # Cancel all test runs
        if group.test_runs_status:
            for test_run_id in group.test_runs_status.keys():
                try:
                    test_run = await self.client.test_runs.get_one(test_run_id)
                    if test_run.status in ["pending", "running"]:
                        await self.client.test_runs.cancel(test_run_id)
                        print(f"Cancelled test run: {test_run_id}")
                except Exception as e:
                    print(f"Error cancelling test run {test_run_id}: {e}")

        # Update group status to cancelled
        return await self.update(str(group.id), {"status": "cancelled"})
    
    async def download_report(self, id_or_name: str, output_dir: str = "downloads", format: Literal["ctrf", "pdf", "csv", "zip"] = "pdf") -> Optional[Path]:
        """
        Download the report for a test run group.
        """
        # Create output directory if it doesn't exist
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        test_run_group = await self.get_one(id_or_name)

        if not test_run_group.ctrf_status == "completed":
            print(f"Test run group {id_or_name} is not completed")
            return None
        
        if not test_run_group.test_report_run:
            print(f"Test run group {id_or_name} has no test report run")
            return None

        return await self.client.test_report_runs.download_report(test_run_group.test_report_run, output_dir, format)

    async def download_all_attachments(self, id_or_name: str, output_dir: str = "downloads") -> Dict[str, List[str]]:
        """
        Download all attachments for all test runs in a test run group.
        Each test run will have its own folder within the test run group folder.

        Args:
            id_or_name: Test run group ID or name
            output_dir: Base directory to save attachments (default: "downloads")

        Returns:
            Dictionary mapping test run names to lists of downloaded attachment filenames
            
        Directory structure: downloads/<test-run-group-name>/<test-run-name>/
        """
        # Create base output directory if it doesn't exist
        base_output_path = Path(output_dir)
        base_output_path.mkdir(parents=True, exist_ok=True)

        test_run_group = await self.get_one(id_or_name)
        
        if not test_run_group.test_runs_status:
            print(f"Test run group {id_or_name} has no test runs")
            return {}

        # Create test run group directory
        test_run_group_name = test_run_group.name or f"test_run_group_{test_run_group.id}"
        group_output_path = base_output_path / test_run_group_name
        group_output_path.mkdir(parents=True, exist_ok=True)

        downloaded_attachments = {}

        # Download attachments for each test run
        for test_run_id in test_run_group.test_runs_status.keys():
            try:
                # Get test run details to get the name
                test_run = await self.client.test_runs.get_one(test_run_id)
                test_run_name = test_run.name or f"test_run_{test_run_id}"
                
                # Create test run specific directory within the group directory
                test_run_dir = group_output_path / test_run_name
                test_run_dir.mkdir(parents=True, exist_ok=True)
                
                # Download all attachments for this test run
                downloaded_files = await self.client.test_runs.download_all_attachments(
                    test_run_id, 
                    str(test_run_dir)
                )
                
                downloaded_attachments[test_run_name] = downloaded_files
                
                if downloaded_files:
                    print(f"Downloaded {len(downloaded_files)} attachments for test run '{test_run_name}' to {test_run_dir}")
                else:
                    print(f"No attachments found for test run '{test_run_name}'")
                    
            except Exception as e:
                print(f"Error downloading attachments for test run {test_run_id}: {e}")
                continue

        return downloaded_attachments
    
    async def execute_and_monitor(
        self,
        name: str,
        test_ids: Optional[List[str]] = None,
        execution_mode: Literal["lenient", "strict"] = "lenient",
        environment: Optional[str] = None,
        tags: Optional[List[str]] = None,
        notification_channels: Optional[List[str]] = None,
        tenant: Optional[str] = None,
        created_by: Optional[str] = None,
        sleep_interval: int = 30,
        output_dir: str = "downloads",
        format: Literal["ctrf", "pdf", "csv", "zip"] = "ctrf",
        filename: str = "ctrf-report.json",
    ) -> TestRunGroup:
        """
        Create a test run group and prepare it for execution.

        Args:
            name: Name for the test run group
            test_ids: List of test IDs to include in the group (use either test_ids OR tags, not both)
            execution_mode: Execution mode for the tests (lenient or strict)
            environment: Optional environment ID
            tags: Optional list of tag IDs to filter tests (use either test_ids OR tags, not both)
            notification_channels: Optional list of notification channel IDs
            tenant: Tenant ID (optional, will use authenticated tenant if not provided)
            created_by: User ID who is creating the group (optional, will use authenticated user if not provided)

        Returns:
            Created test run group instance
        
        Raises:
            ValueError: If both test_ids and tags are specified, or if neither is specified
        """
        print("Creating and executing test run group...")
        test_run_group = await self.create_and_execute(
            name=name,
            test_ids=test_ids,
            execution_mode=execution_mode,
            environment=environment,
            tags=tags,
            notification_channels=notification_channels,
            tenant=tenant,
            created_by=created_by,
        )

        print("Monitoring test run group...")
        while True:
            print("Checking test run group status...")
            test_run_group = await self.get_one(test_run_group.id)
            if test_run_group.status == "completed" and test_run_group.ctrf_status == "completed":
                break
            if test_run_group.status in ["cancelled", "failed", "error"]:
                return None
            print(f"Test run group is not completed, waiting for {sleep_interval} seconds...")
            await asyncio.sleep(sleep_interval)
        
        print("Downloading report...")
        report_path = await self.download_report(test_run_group.id, output_dir=output_dir, format=format)
        print("Report downloaded successfully")

        if not report_path:
            raise ValueError(f"Failed to download report for test run group {test_run_group.id}")

        # Rename the report file to "ctrf-report.json"
        output_path = Path(output_dir)
        new_report_path = output_path / filename
        
        if report_path != new_report_path:
            report_path.rename(new_report_path)
            print(f"Report renamed to: {new_report_path}")

        print("Test run group executed and monitored successfully")

        return test_run_group, report_path