from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime


class DownloaderConfig(BaseModel):
    """Configuration settings for the document downloader."""
    max_retries: int = 3
    timeout: int = 30
    min_file_size: Optional[int] = None
    max_file_size: Optional[int] = None
    allowed_extensions: List[str] = ['.pdf', '.doc',
                                     '.docx', '.xls', '.xlsx', '.ppt', '.pptx']
    verify_ssl: bool = True
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"


class DownloadReport(BaseModel):
    """Report containing download operation statistics and details."""
    success_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    successful_files: List[str] = []
    failed_files: Dict[str, str] = {}
    skipped_files: List[str] = []
    total_size: int = 0
    start_time: datetime
    end_time: Optional[datetime] = None

    @property
    def duration(self) -> float:
        """Calculate duration of download operation in seconds."""
        if self.end_time is None:
            return 0.0
        return (self.end_time - self.start_time).total_seconds()
