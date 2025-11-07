# src/universal_music_downloader/tidal.py

import re
import json
import requests
from urllib.parse import urlparse, parse_qs
from .exceptions import MetadataError, InvalidURLError
from .utils import _normalize_text
from .youtube import download_youtube_search


def get_tidal_track_meta(url: str) -> tuple[str, str]:
    """
    Fetches the (title, artist) metadata from a Tidal track URL.
    It scrapes the track's public webpage for JSON-LD or OpenGraph data.

    Args:
        url (str): The URL of the Tidal track.

    Returns:
        tuple[str, str]: A tuple containing (title, artist).

    Raises:
        InvalidURLError: If the URL is not a valid Tidal URL, or no track ID is found.
        MetadataError: If the track metadata cannot be fetched or parsed.
    """
    if "tidal.com" not in url:
        raise InvalidURLError("Not a Tidal URL.")

    parsed = urlparse(url)
    q = parse_qs(parsed.query)

    # Find track ID from path (e.g., /track/12345) or query (e.g., ?track=12345)
    m = re.search(r"/(?:browse/)?track/(\d+)", parsed.path)
    track_id = m.group(1) if m else q.get("track", [None])[0]

    if not track_id:
        raise InvalidURLError("No track ID found in Tidal URL.")

    track_url = f"https://tidal.com/browse/track/{track_id}"
    headers = {"User-Agent": "Mozilla/5.0", "Accept-Language": "en-US,en;q=0.8"}

    try:
        r = requests.get(track_url, headers=headers, timeout=10, allow_redirects=True)
        r.raise_for_status()
        r.encoding = "utf-8"
        html_text = r.text
    except requests.exceptions.RequestException as e:
        raise MetadataError(f"Failed to fetch Tidal metadata page: {e}")

    # Strategy 1: JSON-LD (Preferred)
    jsonld_match = re.search(
        r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>',
        html_text, re.I | re.S
    )
    if jsonld_match:
        try:
            data = json.loads(jsonld_match.group(1))
            objs = data if isinstance(data, list) else [data]
            for obj in objs:
                if isinstance(obj, dict) and obj.get("@type") in ("MusicRecording", "Song"):
                    title = _normalize_text(obj.get("name"))
                    artist = None
                    by = obj.get("byArtist")
                    if isinstance(by, dict):
                        artist = _normalize_text(by.get("name"))
                    elif isinstance(by, list) and by and isinstance(by[0], dict):
                        artist = _normalize_text(by[0].get("name"))

                    if title and artist:
                        return title, artist
        except Exception:
            pass  # Failed to parse JSON-LD, fall back to OpenGraph

    # Strategy 2: OpenGraph (Fallback)
    def _meta_scrape(prop):
        m = re.search(
            rf'<meta[^>]+property=["\']{re.escape(prop)}["\'][^>]+content=["\']([^"\']+)["\']',
            html_text, re.I
        )
        return _normalize_text(m.group(1)) if m else None

    og_title = _meta_scrape("og:title")
    og_desc = _meta_scrape("og:description")
    title, artist = None, None

    if og_title and not re.search(r"\bon\s*TIDAL\b", og_title, re.I):
        title = og_title

    if og_desc:
        if "•" in og_desc:
            parts = [p.strip() for p in og_desc.split("•")]
            if len(parts) >= 2 and not artist:
                artist = parts[-1]
            if len(parts) >= 1 and not title:
                title = parts[0]
        if (not artist or not title) and re.search(r"\bby\b", og_desc, re.I):
            parts = re.split(r"\sby\s", og_desc, flags=re.I)
            if len(parts) >= 2:
                if not title:
                    title = parts[0].strip()
                if not artist:
                    artist = parts[1].strip()

    # Strategy 3: <title> tag (Last resort)
    if not (title and artist):
        ttag = re.search(r"<title>([^<]+)</title>", html_text, re.I)
        if ttag:
            ttext = _normalize_text(ttag.group(1))
            if " by " in ttext.lower():
                parts = re.split(r"\sby\s", ttext, flags=re.I)
                if len(parts) >= 2:
                    if not title:
                        title = parts[0].split("|")[0].strip()
                    if not artist:
                        artist = parts[1].split("|")[0].strip()

    if not title or not artist:
        raise MetadataError(f"Could not parse title/artist from Tidal page (Track ID: {track_id}).")

    return title, artist


def download_tidal_track(url: str, folder: str) -> str:
    """
    Downloads a track from Tidal.

    This function works by first fetching the track's metadata (artist and title)
    and then using that metadata to search and download the track from YouTube.

    Args:
        url (str): The URL of the Tidal track.
        folder (str): The directory where the file should be saved.

    Returns:
        str: The full path to the downloaded MP3 file (from YouTube).

    Raises:
        InvalidURLError: If the Tidal URL is invalid.
        MetadataError: If metadata extraction fails.
        DownloadFailedError: If the YouTube download fails.
    """
    # Obtain metadata from Tidal URL
    print(f"Fetching metadata for Tidal URL: {url}")
    title, artist = get_tidal_track_meta(url)

    print(f"Metadata found: Artist='{artist}', Title='{title}'")
    print("Proceeding to download from YouTube...")

    # Create a query string for YouTube search
    query = f"{artist} - {title} audio"

    mp3_path = download_youtube_search(query, folder)

    return mp3_path
