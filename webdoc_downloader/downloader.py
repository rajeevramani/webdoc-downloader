import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from urllib.parse import urlparse, urljoin  # Add urlparse here

import requests
from bs4 import BeautifulSoup
from pydantic import HttpUrl, DirectoryPath

from .models import DownloaderConfig, DownloadReport
from .exceptions import DownloadError, InvalidURLError, NetworkError
from .utils import setup_logging, is_valid_file, sanitize_filename


class DocumentDownloader:
    """Main class for downloading documents from web pages."""

    def __init__(
        self,
        output_dir: Optional[str] = None,
        config: Optional[DownloaderConfig] = None
    ):
        self.output_dir = Path(output_dir or "out")
        self.config = config or DownloaderConfig()
        self.logger = setup_logging()
        self.session = self._setup_session()

    def _setup_session(self) -> requests.Session:
        """Configure requests session with retry handling."""
        session = requests.Session()

        # Always set a User-Agent
        session.headers.update({
            'User-Agent': self.config.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        })

        # Configure SSL verification
        session.verify = self.config.verify_ssl

        return session

    def download_from_url(self, url: str) -> DownloadReport:
        """Download all documents from the specified URL."""
        self.logger.info(f"Starting download from: {url}")
        report = DownloadReport(start_time=datetime.now())

        try:
            # Ensure output directory exists
            self.output_dir.mkdir(parents=True, exist_ok=True)

            # Fetch and parse the webpage
            self.logger.info("Fetching webpage...")
            response = self._make_request(url)
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find all links in the page
            links = soup.find_all('a', href=True)
            self.logger.info(f"Found total of {len(links)} links on the page")

            file_links = []
            for link in links:
                href = link['href']
                if self._is_downloadable_link(href):
                    # Convert relative URL to absolute URL
                    absolute_url = self._normalize_url(url, href)
                    file_links.append(absolute_url)
                    self.logger.info(
                        f"Found downloadable link: {absolute_url}")
                else:
                    self.logger.debug(
                        f"Skipping non-downloadable link: {href}")

            self.logger.info(
                f"Found {len(file_links)} potential document links")

            # Download each file
            for file_url in file_links:
                try:
                    # Don't need to normalize URL here since it's already done
                    filename = sanitize_filename(
                        Path(urlparse(file_url).path).name)

                    # Skip if file exists
                    if (self.output_dir / filename).exists():
                        self.logger.info(f"Skipping existing file: {filename}")
                        report.skipped_files.append(filename)
                        report.skipped_count += 1
                        continue

                    # Download the file
                    file_response = self._make_request(file_url, stream=True)
                    file_size = int(
                        file_response.headers.get('content-length', 0))

                    # Save the file
                    output_path = self.output_dir / filename
                    bytes_written = self._save_file(file_response, output_path)

                    # Update report
                    report.successful_files.append(filename)
                    report.success_count += 1
                    report.total_size += bytes_written

                except Exception as e:
                    self.logger.error(f"Failed to download {
                                      file_url}: {str(e)}")
                    report.failed_files[file_url] = str(e)
                    report.failed_count += 1

        except Exception as e:
            self.logger.error(f"Download failed: {str(e)}")
            raise DownloadError(f"Failed to download from {url}: {str(e)}")
        finally:
            report.end_time = datetime.now()

        return report

    def _make_request(self, url: str, stream: bool = False) -> requests.Response:
        """Make HTTP request with retry logic."""
        for attempt in range(self.config.max_retries):
            try:
                response = self.session.get(
                    url,
                    timeout=self.config.timeout,
                    stream=stream
                )
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                if attempt == self.config.max_retries - 1:
                    raise NetworkError(f"Failed to fetch {url} after {
                                       self.config.max_retries} attempts: {str(e)}")
                self.logger.warning(
                    f"Attempt {attempt + 1} failed, retrying...")

    def _is_downloadable_link(self, href: str) -> bool:
        """Check if the link points to a downloadable file."""
        if not href or href.startswith('#') or href.startswith('javascript:'):
            return False

        # Get the URL path without query parameters
        parsed_url = urlparse(href)
        path = parsed_url.path.lower()

        # Check file extensions
        return any(path.endswith(ext.lower()) for ext in self.config.allowed_extensions)

    def _normalize_url(self, base_url: str, file_url: str) -> str:
        """Convert relative URLs to absolute URLs."""
        from urllib.parse import urljoin
        return urljoin(base_url, file_url)

    def _is_valid_file_size(self, size: int) -> bool:
        """Check if file size meets configured constraints."""
        if self.config.min_file_size and size < self.config.min_file_size:
            return False
        if self.config.max_file_size and size > self.config.max_file_size:
            return False
        return True

    def _save_file(self, response: requests.Response, output_path: Path) -> int:
        """Save downloaded file to disk and return bytes written."""
        bytes_written = 0
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    bytes_written += len(chunk)
        return bytes_written
