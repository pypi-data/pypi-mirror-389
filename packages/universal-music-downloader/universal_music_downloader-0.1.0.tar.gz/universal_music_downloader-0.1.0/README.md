# Universal Music Downloader

A Python library and command-line tool to download songs from various streaming platforms.

This tool works by fetching track metadata (artist, title) from platforms like Apple Music, Tidal, and Spotify, and then uses that metadata to find and download the corresponding track from YouTube. For YouTube and SoundCloud, it downloads directly.

---

## ⚙️ How it Works

The library provides a unified function for each platform, handling the different download strategies automatically.

* **Direct Download (YouTube, SoundCloud):** Uses `yt-dlp` to download and convert the audio to MP3.
* **Metadata-Based Download (Spotify, Apple Music, Tidal):**
    1.  Scrapes the provided URL to get the track's **Artist** and **Title**.
    2.  Performs a search on YouTube for `"Artist - Title audio"`.
    3.  Downloads the first search result as an MP3.

---

## 🚀 Installation

You can install the package directly from PyPI:

```bash
pip install universal-music-downloader
```

-----

## Usage

You can use this project in two ways: as a command-line tool or as a Python library.

### 1\. As a Command-Line Tool (CLI)

After installation, the `umd` command will be available in your terminal.

#### Format

```bash
umd <platform> <url> [options]
```

#### Arguments

  * `<platform>`: The source platform.
      * `spotify`
      * `apple`
      * `tidal`
      * `youtube`
      * `soundcloud`
  * `<url>`: The full URL of the track (it's best to use quotes).

#### Options

  * `-o, --output <folder>`: Specify a folder to save the MP3. (Default: current directory)

#### Examples

```bash
# Download a Spotify track to the current folder
umd spotify "https://open.spotify.com/intl-es/track/0FIDCNYYjNvPVimz5icugS?si=e83ededc95564c0a"

# Download an Apple Music track to a specific 'downloads' folder
umd apple "https://music.apple.com/es/song/timeless/1770380890" -o ./my-music

# Download a YouTube video
umd youtube "https://youtu.be/16jA-6hiSUo?si=pBhCn4ezIj7917E2"
```

-----

### 2\. As a Python Library

You can import and use the download functions directly in your Python code for full control.

#### Available Functions

```python
from universal_music_downloader.spotify import download_spotify_track
from universal_music_downloader.youtube import download_youtube_url, download_youtube_search
from universal_music_downloader.apple import download_apple_music_track
from universal_music_downloader.tidal import download_tidal_track
from universal_music_downloader.soundcloud import download_soundcloud_track
```

#### Example: Downloading a Spotify Track

```python
import os
from universal_music_downloader.spotify import download_spotify_track
from universal_music_downloader.exceptions import DownloaderError

DOWNLOAD_FOLDER = "my_song_collection"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

url = "[https://open.spotify.com/track/](https://open.spotify.com/track/)..."

try:
    print(f"Downloading from {url}...")
    # All download functions follow the same (url, folder) signature
    mp3_path = download_spotify_track(url, DOWNLOAD_FOLDER)
    print(f"\nSuccess! File saved to: {mp3_path}")

except DownloaderError as e:
    print(f"\nDownload Failed: {e}")
```

#### Error Handling

The library uses custom exceptions for easy error management. It is highly recommended to wrap your calls in a `try...except` block.

  * `exceptions.DownloaderError`: The base exception for all errors.
  * `exceptions.InvalidURLError`: The provided URL is invalid or malformed.
  * `exceptions.MetadataError`: Failed to scrape/fetch metadata (e.g., from Tidal/Apple).
  * `exceptions.DownloadFailedError`: The download process itself failed (e.g., `yt-dlp` or `spotdl` failed).

<!-- end list -->

```python
from universal_music_downloader import exceptions

try:
    # ... call a download function ...
except exceptions.InvalidURLError:
    print("That URL doesn't look right.")
except exceptions.MetadataError:
    print("Could not find that song's details.")
except exceptions.DownloadFailedError as e:
    print(f"The download failed: {e}")
except exceptions.DownloaderError as e:
    print(f"A general error occurred: {e}")
```

-----

## ⚖️ License

This project is licensed under the **MIT License**. See the `LICENSE` file for details.
