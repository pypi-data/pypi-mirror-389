# src/music_downloader/__init__.py

"""
universal-music-downloader: A Python library to download songs from various streaming platforms.
"""

# Make exceptions easily accessible for users
from .exceptions import (
    DownloaderError,
    InvalidURLError,
    DownloadFailedError,
    MetadataError
)
