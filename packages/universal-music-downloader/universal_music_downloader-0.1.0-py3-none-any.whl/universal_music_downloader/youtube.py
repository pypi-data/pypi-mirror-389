# src/universal_music_downloader/youtube.py

import os
import yt_dlp
from .exceptions import DownloadFailedError, InvalidURLError
from .utils import _get_ydl_opts


def download_youtube_url(url: str, folder: str) -> str:
    """
    Downloads a single video from a YouTube URL as an MP3.

    Args:
        url (str): The direct URL to the YouTube video.
        folder (str): The directory where the file should be saved.

    Returns:
        str: The full path to the downloaded MP3 file.

    Raises:
        InvalidURLError: If the URL contains 'list=' (playlists are not supported).
        DownloadFailedError: If the yt-dlp download process fails.
    """
    # One song validation
    if "list=" in url:
        raise InvalidURLError("Playlist URLs are not supported. Please provide a single video URL.")

    os.makedirs(folder, exist_ok=True)

    output_template = f"{folder}/%(title).200B.%(ext)s"
    ydl_opts = _get_ydl_opts(output_template)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

            # prepare_filename gives the path before conversion
            filename = ydl.prepare_filename(info)

            mp3_filename = filename.rsplit(".", 1)[0] + ".mp3"

            if not os.path.exists(mp3_filename):
                raise DownloadFailedError(f"File not found after download: {mp3_filename}")

            return mp3_filename

    except yt_dlp.utils.DownloadError as e:
        # Catch yt-dlp's specific download error
        raise DownloadFailedError(f"yt-dlp failed to download URL ({url}): {e}")
    except Exception as e:
        # Catch any other unexpected error
        raise DownloadFailedError(f"An unexpected error occurred during YouTube download: {e}")


def download_youtube_search(query: str, folder: str) -> str:
    """
    Searches YouTube for a query and downloads the first result as an MP3.

    Args:
        query (str): The search query (e.g., "Artist - Title").
        folder (str): The directory where the file should be saved.

    Returns:
        str: The full path to the downloaded MP3 file.

    Raises:
        DownloadFailedError: If the search finds no results or the download fails.
    """
    os.makedirs(folder, exist_ok=True)

    output_template = f"{folder}/%(title).200B.%(ext)s"
    ydl_opts = _get_ydl_opts(output_template)

    search_query = f"ytsearch1:{query}"  # 'ytsearch1:' = first result

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_query, download=True)

            # When using 'ytsearch', info contains an 'entries' list
            if "entries" not in info or not info["entries"]:
                raise DownloadFailedError(f"No search results found for query: {query}")

            # Get info for the first (and only) result
            first_result_info = info["entries"][0]

            filename = ydl.prepare_filename(first_result_info)
            mp3_filename = filename.rsplit(".", 1)[0] + ".mp3"

            if not os.path.exists(mp3_filename):
                raise DownloadFailedError(f"File not found after download: {mp3_filename}")

            return mp3_filename

    except yt_dlp.utils.DownloadError as e:
        raise DownloadFailedError(f"yt-dlp failed to download search query ({query}): {e}")
    except Exception as e:
        raise DownloadFailedError(f"An unexpected error occurred during YouTube search: {e}")
