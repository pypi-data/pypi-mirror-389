# src/music_downloader/exceptions.py

"""
Custom exceptions for the universal-music-downloader library.
"""


class DownloaderError(Exception):
    """Base exception for all errors in this library."""
    pass


class InvalidURLError(DownloaderError):
    """Raised when an invalid or unsupported URL is provided."""
    pass


class DownloadFailedError(DownloaderError):
    """Raised when the external download tool (e.g., yt-dlp, spotdl) fails."""
    pass


class MetadataError(DownloaderError):
    """Raised when fetching track metadata (title, artist) fails."""
    pass
