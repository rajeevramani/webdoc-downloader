# src/webdoc_downloader/cli.py
import typer
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich import print as rprint

from .downloader import DocumentDownloader
from .models import DownloaderConfig
from .exceptions import DownloadError
import logging
from .utils import setup_logging

app = typer.Typer()
console = Console()


def main():
    app()


# In cli.py
@app.command()
def download(
    url: str = typer.Argument(
        ...,
        help="URL to download documents from",
        metavar="URL"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging"
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Output directory for downloaded files"
    ),
    max_retries: int = typer.Option(
        3,
        "--max-retries",
        "-r",
        help="Maximum number of retry attempts"
    ),
    timeout: int = typer.Option(
        30,
        "--timeout",
        "-t",
        help="Request timeout in seconds"
    ),
    allowed_extensions: str = typer.Option(
        ".pdf,.doc,.docx",
        "--allowed-extensions",
        "-e",
        help="Comma-separated list of allowed file extensions"
    )
):
    """Download documents from a webpage."""
    try:
        # Set logging level based on verbose flag
        log_level = logging.DEBUG if verbose else logging.INFO
        setup_logging(level=log_level)

        # Convert comma-separated extensions to list
        extension_list = [ext.strip() for ext in allowed_extensions.split(",")]

        config = DownloaderConfig(
            max_retries=max_retries,
            timeout=timeout,
            allowed_extensions=extension_list
        )

        downloader = DocumentDownloader(
            output_dir=str(output_dir) if output_dir else None,
            config=config
        )

        with console.status("Downloading documents..."):
            report = downloader.download_from_url(url)

        rprint("[green]Download completed!")
        rprint(f"Successfully downloaded: {report.success_count} files")
        rprint(f"Failed: {report.failed_count} files")
        rprint(f"Skipped: {report.skipped_count} files")
        rprint(f"Total size: {report.total_size / 1024:.2f} KB")
        rprint(f"Duration: {report.duration:.2f} seconds")

    except DownloadError as e:
        rprint(f"[red]Error: {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        rprint(f"[red]Unexpected error: {str(e)}")
        raise typer.Exit(1)


if __name__ == "__main__":
    main()
