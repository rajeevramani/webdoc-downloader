class DownloadError(Exception):
    """Base exception for download-related errors."""
    pass


class InvalidURLError(DownloadError):
    """Raised when the provided URL is invalid or inaccessible."""
    pass


class NetworkError(DownloadError):
    """Raised when network-related issues occur."""
    pass


class FileSystemError(DownloadError):
    """Raised when file system operations fail."""
    pass


class ValidationError(DownloadError):
    """Raised when validation checks fail."""
    pass
