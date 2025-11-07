# src/universal_music_downloader/soundcloud.py

import os
import requests
import yt_dlp
from .exceptions import DownloadFailedError, InvalidURLError
from .utils import _get_ydl_opts


def _resolve_soundcloud_shortlink(url: str) -> str:
    """
    Resolves 'on.soundcloud.com' shortlinks to the full URL.
    If the URL is not a shortlink, it returns it unchanged.
    """
    if "on.soundcloud.com" not in url:
        return url

    try:
        # Use a HEAD request for efficiency, allow redirects
        response = requests.head(url, timeout=10, allow_redirects=True)
        response.raise_for_status()  # Raises HTTPError for bad responses
        return response.url  # The final URL after redirects
    except requests.exceptions.RequestException as e:
        raise InvalidURLError(f"Failed to resolve SoundCloud shortlink: {e}")


def download_soundcloud_track(url: str, folder: str) -> str:
    """
    Downloads a single track from SoundCloud as an MP3.
    Also handles resolving 'on.soundcloud.com' shortlinks.

    Args:
        url (str): The URL to the SoundCloud track (can be a shortlink).
        folder (str): The directory where the file should be saved.

    Returns:
        str: The full path to the downloaded MP3 file.

    Raises:
        InvalidURLError: If the URL (or resolved shortlink) is invalid.
        DownloadFailedError: If the yt-dlp download process fails.
    """
    try:
        # First, resolve the URL in case it's a shortlink
        resolved_url = _resolve_soundcloud_shortlink(url)
    except InvalidURLError:
        # Re-raise if resolving failed
        raise

    os.makedirs(folder, exist_ok=True)

    output_template = f"{folder}/%(title).200B.%(ext)s"
    ydl_opts = _get_ydl_opts(output_template)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(resolved_url, download=True)

            filename = ydl.prepare_filename(info)
            mp3_filename = filename.rsplit(".", 1)[0] + ".mp3"

            if not os.path.exists(mp3_filename):
                raise DownloadFailedError(f"File not found after download: {mp3_filename}")

            return mp3_filename

    except yt_dlp.utils.DownloadError as e:
        raise DownloadFailedError(f"yt-dlp failed to download SoundCloud URL ({resolved_url}): {e}")
    except Exception as e:
        raise DownloadFailedError(f"An unexpected error occurred during SoundCloud download: {e}")
