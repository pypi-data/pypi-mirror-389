# src/universal_music_downloader/apple.py

import re
import requests
from urllib.parse import urlparse, parse_qs
from .exceptions import MetadataError, InvalidURLError
from .youtube import download_youtube_search


def get_apple_music_track_meta(url: str) -> tuple[str, str]:
    """
    Fetches the (title, artist) metadata from an Apple Music track URL.
    It queries the iTunes API to get the track details.

    Args:
        url (str): The URL of the Apple Music track.

    Returns:
        tuple[str, str]: A tuple containing (title, artist).

    Raises:
        InvalidURLError: If the URL is not a valid Apple Music URL, or no track ID is found.
        MetadataError: If the track metadata cannot be fetched from the iTunes API.
    """
    if "music.apple.com" not in url:
        raise InvalidURLError("Not an Apple Music URL.")

    parsed = urlparse(url)
    q = parse_qs(parsed.query)
    track_id = q.get("i", [None])[0]

    if not track_id:
        m = re.search(r"/song/[^/]+/(\d+)", parsed.path)
        if m:
            track_id = m.group(1)

    if not track_id:
        raise InvalidURLError("No track ID found in Apple Music URL.")

    try:
        # Use the iTunes lookup API
        r = requests.get("https://itunes.apple.com/lookup", params={"id": track_id}, timeout=10)
        r.raise_for_status()  # Raise HTTPError for bad responses
        data = r.json()

        if data.get("resultCount", 0) == 0:
            raise MetadataError(f"Track not found in iTunes API (Track ID: {track_id}).")

        res = data["results"][0]
        title = res.get("trackName") or res.get("collectionName")
        artist = res.get("artistName")

        if not title or not artist:
            raise MetadataError("Missing title or artist in iTunes API response.")

        return title, artist

    except requests.exceptions.RequestException as e:
        raise MetadataError(f"Failed to fetch Apple Music metadata: {e}")
    except (KeyError, IndexError, Exception) as e:
        raise MetadataError(f"Failed to parse iTunes API response: {e}")


def download_apple_music_track(url: str, folder: str) -> str:
    """
    Downloads a track from Apple Music.

    This function works by first fetching the track's metadata (artist and title)
    and then using that metadata to search and download the track from YouTube.

    Args:
        url (str): The URL of the Apple Music track.
        folder (str): The directory where the file should be saved.

    Returns:
        str: The full path to the downloaded MP3 file (from YouTube).

    Raises:
        InvalidURLError: If the Apple Music URL is invalid.
        MetadataError: If metadata extraction fails.
        DownloadFailedError: If the YouTube download fails.
    """
    # Obtain metadata from Apple Music URL
    print(f"Fetching metadata for Apple Music URL: {url}")
    title, artist = get_apple_music_track_meta(url)

    print(f"Metadata found: Artist='{artist}', Title='{title}'")
    print("Proceeding to download from YouTube...")

    # Create a query string for YouTube search
    query = f"{artist} - {title} audio"

    mp3_path = download_youtube_search(query, folder)

    return mp3_path
