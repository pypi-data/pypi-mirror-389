# src/universal_music_downloader/utils.py

from .exceptions import DownloadFailedError
import html
import re
import unicodedata

"""
Shared utility functions for the downloader.
"""


def _get_ydl_opts(output_template: str) -> dict:
    """
    Returns the base yt-dlp options for MP3 extraction.

    Args:
        output_template (str): The 'outtmpl' path for yt-dlp.

    Returns:
        dict: A dictionary of yt-dlp options.
    """

    class WarningsSuppressor:
        """Suppress yt-dlp's warnings."""

        def warning(self):
            pass

        def debug(self):
            pass

        def error(self):
            raise DownloadFailedError(f"yt-dlp failed to download URL: {self}")

    return {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "noplaylist": True,
        "quiet": True,
        "noprogress": True,
        "logger": WarningsSuppressor,
    }


def _normalize_text(s: str) -> str:
    """
    Cleans and normalizes a string.
    Unescapes HTML, normalizes Unicode, and removes common suffixes.
    """
    if not s:
        return ""

    s = html.unescape(s).strip()
    s = unicodedata.normalize("NFC", s)

    # Anti-mojibake heuristic: "MÃ¡s" -> "Más"
    if "Ã" in s or "" in s:
        try:
            s = s.encode("latin1", errors="ignore").decode("utf-8", errors="ignore")
        except Exception:
            pass

    # Remove typical suffixes
    s = re.sub(r"\s*\|\s*TIDAL$", "", s, flags=re.I)
    s = re.sub(r"\s*on\s*TIDAL$", "", s, flags=re.I)
    return s.strip()
