# src/universal_music_downloader/cli.py

import argparse
import os
import sys
from .exceptions import DownloaderError

from .spotify import download_spotify_track
from .youtube import download_youtube_url
from .apple import download_apple_music_track
from .tidal import download_tidal_track
from .soundcloud import download_soundcloud_track

PLATFORM_MAP = {
    "spotify": download_spotify_track,
    "youtube": download_youtube_url,
    "apple": download_apple_music_track,
    "tidal": download_tidal_track,
    "soundcloud": download_soundcloud_track,
}


def main():
    """Main entry point for the Command Line Interface."""

    parser = argparse.ArgumentParser(
        description="Universal Music Downloader: Download songs from various platforms."
    )

    parser.add_argument(
        "platform",
        help="The platform to download from.",
        choices=PLATFORM_MAP.keys()
    )

    parser.add_argument(
        "url",
        help="The URL of the track to download."
    )

    parser.add_argument(
        "-o", "--output",
        help="The output folder to save the file. (default: current directory)",
        default="."
    )

    args = parser.parse_args()

    # Get the download function based on the platform
    download_function = PLATFORM_MAP[args.platform]

    try:
        print(f"Starting download for platform: {args.platform}")
        print(f"URL: {args.url}")

        mp3_path = download_function(args.url, args.output)

        print("\n--- SUCCESS! ---")
        print(f"File saved to: {os.path.abspath(mp3_path)}")

    except DownloaderError as e:
        print(f"\n--- FAILED! ---", file=sys.stderr)
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n--- UNEXPECTED FAILED! ---", file=sys.stderr)
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
