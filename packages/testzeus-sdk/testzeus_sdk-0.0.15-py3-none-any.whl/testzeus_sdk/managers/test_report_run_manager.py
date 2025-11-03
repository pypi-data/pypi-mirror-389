"""
TestReportRun manager class for TestZeus test report run operations.
"""

from typing import Literal
from testzeus_sdk.client import TestZeusClient
from testzeus_sdk.managers.base import BaseManager
from testzeus_sdk.models.test_report_run import TestReportRun
from pathlib import Path
import httpx

class TestReportRunManager(BaseManager[TestReportRun]):
    """
    Manager class for TestZeus test report run entities.

    This class provides CRUD operations for working with test report run entities.
    """

    def __init__(self, client: TestZeusClient) -> None:
        """
        Initialize a TestReportRunManager.

        Args:
            client: TestZeus client instance
        """
        super().__init__(client, "test_report_run", TestReportRun)

    async def download_report(self, id_or_name: str, output_dir: str = "downloads", format: str = Literal["ctrf", "pdf", "csv", "zip"]) -> Path:
        """
        Download the report for a test report run.
        """
        # Create output directory if it doesn't exist
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        test_report_run = await self.get_one(id_or_name)

        if not test_report_run.status == "completed":
            print(f"Test report run {id_or_name} is not completed")
            return None

        if format == "ctrf":
            report_file = test_report_run.ctrf_report
        elif format == "pdf":
            report_file = test_report_run.pdf_report
        elif format == "csv":
            report_file = test_report_run.csv_report
        elif format == "zip":
            report_file = test_report_run.zip_report
    
        async with httpx.AsyncClient() as client:
            file_path = output_path / report_file
            url = await self._get_file_url(test_report_run.id, report_file)

            async with client.stream("GET", url, follow_redirects=True) as response:
                response.raise_for_status()

                with open(file_path, "wb") as f:
                    async for chunk in response.aiter_bytes():
                        f.write(chunk)

        return file_path