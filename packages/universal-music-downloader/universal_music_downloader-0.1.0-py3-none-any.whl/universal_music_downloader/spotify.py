# src/universal_music_downloader/spotify.py

import os
import shutil
import subprocess
# Custom exceptions
from .exceptions import InvalidURLError, DownloadFailedError, DownloaderError


def _spotdl_cmd() -> list[str]:
    """
    Determines the command to run spotdl.
    Checks if 'spotdl' is in PATH, otherwise defaults to 'python -m spotdl'.

    Returns:
        list[str]: The command as a list of strings.
    """
    if shutil.which("spotdl"):
        return ["spotdl"]
    return ["python", "-m", "spotdl"]


def download_spotify_track(url: str, folder: str) -> str:
    """
    Downloads a single track from Spotify using spotdl.

    Args:
        url (str): The URL of the Spotify track.
        folder (str): The directory where the file should be saved.

    Returns:
        str: The full path to the downloaded MP3 file.

    Raises:
        InvalidURLError: If the URL is not a valid Spotify track URL.
        DownloadFailedError: If the spotdl subprocess fails to execute.
        FileNotFoundError: (Standard) If spotdl runs, but no MP3 file is found.
        DownloaderError: If the 'spotdl' command itself cannot be found.
    """
    os.makedirs(folder, exist_ok=True)

    if "track/" not in url:
        raise InvalidURLError(f"Invalid Spotify URL. Must contain '/track/': {url}")

    env = os.environ.copy()
    cmd = _spotdl_cmd() + ["--output", folder, url]

    # Run the spotdl command
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,  # Capture stdout/stderr
            text=True,  # Decode output as text (UTF-8)
            env=env,
            check=True,  # Raises CalledProcessError if returncode is not 0
            encoding="utf-8"
        )
    except subprocess.CalledProcessError as e:
        # If spotdl fails, re-raise custom exception
        error_message = f"spotdl failed with code {e.returncode}: {e.stderr}"
        raise DownloadFailedError(error_message) from e
    except FileNotFoundError as e:
        # This happens if 'python' or 'spotdl' isn't found in the PATH
        raise DownloaderError(f"spotdl command not found: {e}")

    # Find the first .mp3 file downloaded in the folder
    for root, _, files in os.walk(folder):
        for file in files:
            if file.lower().endswith(".mp3"):
                return os.path.join(root, file)

    # If we get here, the process succeeded, but we couldn't find the file
    raise FileNotFoundError(
        f"Download successful, but no .mp3 file was found in {folder}."
        f"\n--- spotdl STDOUT ---\n{result.stdout}"
    )
