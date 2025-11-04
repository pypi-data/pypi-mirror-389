# dabcli.py

import argparse
import os
import sys
import requests
import zipfile
import io
from tabulate import tabulate
from importlib.resources import files
import subprocess

from dabcli.api import login, get_current_user
from dabcli.search import search_and_print, get_artist_discography, get_track_metadata_by_id
from dabcli.downloader import download_track
from dabcli.tagger import tag_audio
from dabcli.album import download_album, find_album_by_title
from dabcli.config import config, clear_credentials
from dabcli.streamer import stream_cli_entry
from dabcli.cover import download_cover_image
from dabcli.utils import require_login

# ====================== ASCII Art & Credits ======================
ASCII_ART = r"""
  _____          ____  __  __           _         _____ _      _____
 |  __ \   /\   |  _ \|  \/  |         (_)       / ____| |    |_   _|
 | |  | | /  \  | |_) | \  / |_   _ ___ _  ___  | |    | |      | |
 | |  | |/ /\ \ |  _ <| |\/| | | | / __| |/ __| | |    | |      | |
 | |__| / ____ \| |_) | |  | | |_| \__ \ | (__  | |____| |____ _| |_
 |_____/_/    \_\____/|_|  |_|\__,_|___/_|\___|  \_____|______|_____|
"""

CREDITS = """
Developed By: sherlockholmesat221b (sherlockholmesat221b@proton.me)
Special Thanks To: His Majesty superadmin0 (Creator of DABMusic)
Happy Birthday sherlockholmes221b (06 July)
"""

COMMANDS_HELP = """
Available Commands:

  dabcli.py login "<email>" "<password>"
      → Login with your DAB account

  dabcli.py status
      → Check login/authentication status

  dabcli.py logout
      → Clear saved credentials

  dabcli.py search "<query>" [--type track|album|artist]
      → Search for tracks, albums, or artists

  dabcli.py discography <artist-id or artist name> [--view-only]
      → Downloads all albums by a specific artist

  dabcli.py track <track-id> [--format mp3|flac] [--title ...] [--artist ...] [--album ...] [--genre ...] [--date ...] [--path ...]
      → Download and tag a single track

  dabcli.py album "<album-id or title>" [--format mp3|flac] [--title ...] [--artist ...] [--album ...] [--genre ...] [--date ...] [--path ...]
      → Download an entire album by ID or title

  dabcli.py play --track-id <id> | --album-id <id> | --queue <ids...> | --library-id <id>
      → Stream tracks, albums, or libraries

  dabcli.py library [<library-id>] [--view-only] [--quality ...] [--format mp3|flac] [--title ...] [--artist ...] [--album ...] [--genre ...] [--date ...] [--path ...]
      → If <library-id> is provided, downloads the library or prints tracks with --view-only
      → If no ID is provided, lists all user libraries

  dabcli.py favorites
      → Lists all user favorites in a table

  dabcli.py config [--path]
      → Configure dabcli interactively or show config path

  dabcli.py update
      → Update DAB CLI to latest version from GitHub

  dabcli.py --version
      → Check version of DABMusic CLI and compare with GitHub
"""

# ====================== VERSION & UPDATE ======================
GITHUB_VERSION_URL = "https://raw.githubusercontent.com/sherlockholmesat221b/dabcli/main/VERSION"
def get_installed_version() -> str:
    """Return the installed version of dabcli (using modern methods)."""
    try:
        # Preferred modern way (Python 3.8+)
        from importlib.metadata import version, PackageNotFoundError
    except ImportError:
        # Older Python fallback
        from importlib_metadata import version, PackageNotFoundError

    try:
        return version("dabcli")
    except PackageNotFoundError:
        # fallback: try pip show
        try:
            python_exe = sys.executable or "python"
            result = subprocess.run(
                [python_exe, "-m", "pip", "show", "dabcli"],
                capture_output=True,
                text=True
            )
            for line in result.stdout.splitlines():
                if line.startswith("Version:"):
                    return line.split(":", 1)[1].strip()
        except Exception:
            pass
    return "unknown"
def check_version():
    """Prints installed version and compares with GitHub version."""
    local_version = get_installed_version()
    print(f"DAB CLI installed version: {local_version}")

    try:
        r = requests.get(GITHUB_VERSION_URL, timeout=5)
        if r.status_code == 200:
            latest_version = r.text.strip()
        else:
            latest_version = None
    except Exception:
        latest_version = None

    if latest_version:
        if latest_version == local_version:
            print("[Version] You are up to date ✅")
        else:
            print(f"[Version] Outdated! Latest version: {latest_version}. Run 'dabcli.py update' to upgrade.")
    else:
        print("[Version] Could not fetch latest version info from GitHub.")

import subprocess
import sys

def update_dabcli():
    """Update dabcli via pip."""
    print("[Update] Attempting to update DAB CLI via pip...")

    try:
        python_exe = sys.executable or "python"
        result = subprocess.run(
            [python_exe, "-m", "pip", "install", "--upgrade", "dabcli"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print("[Update] DAB CLI successfully updated via pip!")
            print("Please restart the CLI to use the new version.")
        else:
            print("[Update] Failed to update DAB CLI via pip.")
            print(result.stderr)
            print(f"Try running manually: {python_exe} -m pip install --upgrade dabcli")
    except Exception as e:
        print(f"[Update] Exception occurred: {e}")
        print("Try running: pip install --upgrade dabcli")

# ====================== MAIN CLI ======================
def main():
    parser = argparse.ArgumentParser(
        description="DAB CLI — Download and Browse music from DAB Music Player",
        add_help=False
    )
    subparsers = parser.add_subparsers(dest="command", required=False)

    # ---------------- Global Args ----------------
    parser.add_argument("--version", action="store_true", help="Show current version")
    parser.add_argument("--help", "-h", action="store_true", help="Show detailed help for a command")

    # ---------------- Subcommands ----------------
    subparsers.add_parser("status", help="Check login/authentication status")
    subparsers.add_parser("logout", help="Clear token and credentials")
    subparsers.add_parser("update", help="Update DAB CLI to latest version")

    login_parser = subparsers.add_parser("login", help="Login with your DAB account")
    login_parser.add_argument("email", help="Your DAB account email")
    login_parser.add_argument("password", help="Your DAB account password")

    search_parser = subparsers.add_parser("search", help="Search tracks, albums, and artists")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--type", choices=["track", "album", "artist"], default=None, help="Type of search")

    discog_parser = subparsers.add_parser("discography", help="Download or view all albums by an artist")
    discog_parser.add_argument("artist", help="Artist name or ID")
    discog_parser.add_argument("--sort-by", choices=["year", "title", "popularity"], default="year", help="Sort albums by this field")
    discog_parser.add_argument("--sort-order", choices=["asc", "desc"], default="desc", help="Sort order")
    discog_parser.add_argument("--view-only", action="store_true", help="Only view albums, do not download")
    discog_parser.add_argument("--limit", type=int, help="Limit number of albums to download")

    for arg, desc in [("--format", "mp3|flac"), ("--title", "Override track title"),
                      ("--artist", "Override artist name"), ("--album", "Override album name"),
                      ("--genre", "Override genre"), ("--date", "Override release date"),
                      ("--path", "Custom download directory")]:
        discog_parser.add_argument(arg, help=desc)

    track_parser = subparsers.add_parser("track", help="Download and tag a single track")
    track_parser.add_argument("track_id", help="Track ID")
    for arg, desc in [("--format", "mp3|flac"), ("--title", "Override track title"),
                      ("--artist", "Override artist name"), ("--album", "Override album name"),
                      ("--genre", "Override genre"), ("--date", "Override release date"),
                      ("--path", "Custom download directory")]:
        track_parser.add_argument(arg, help=desc)

    album_parser = subparsers.add_parser("album", help="Download an album by ID or title")
    album_parser.add_argument("album_id_or_title", help="Album ID or title")

    play_parser = subparsers.add_parser("play", help="Stream tracks, albums, or libraries")
    play_parser.add_argument("--track-id", help="Track ID to play")
    play_parser.add_argument("--album-id", help="Album ID to play")
    play_parser.add_argument("--queue", nargs="+", help="Queue of track IDs")
    play_parser.add_argument("--library-id", help="Library ID to play")
    play_parser.add_argument("--quality", help="Streaming quality")
    play_parser.add_argument("--mode", choices=["stream", "download"], default="stream", help="Mode")

    library_parser = subparsers.add_parser("library", help="View or download libraries")
    library_parser.add_argument("library_id", nargs="?", default=None, help="Library ID to view/download. Omit to list all libraries")
    library_parser.add_argument("--view-only", action="store_true", help="Only view library info and tracks")
    library_parser.add_argument("--quality", help="Preferred quality when downloading")

    subparsers.add_parser("favorites", help="Show your favorite tracks")

    config_parser = subparsers.add_parser("config", help="Configure dabcli settings interactively or show config path")
    config_parser.add_argument("--path", action="store_true", help="Print the path of config.json")

    help_parser = subparsers.add_parser("help", help="Show help for a specific command")
    help_parser.add_argument("command_name", nargs="?", help="Command to get help for")

    # ====================== Parse args ======================
    args = parser.parse_args()

    # ---------- Global help ----------
    if args.help and args.command:
        if args.command in subparsers.choices:
            subparsers.choices[args.command].print_help()
        else:
            print(f"No such command: {args.command}")
        return
    elif args.help and not args.command:
        print(ASCII_ART)
        print(CREDITS)
        print(COMMANDS_HELP)
        return

    if args.version:
        check_version()
        return

    if not args.command:
        print(ASCII_ART)
        print(CREDITS)
        print(COMMANDS_HELP)
        return

    # ====================== Command handlers ======================
    if args.command == "update":
        update_dabcli()
        return

    elif args.command == "help":
        if args.command_name:
            if args.command_name in subparsers.choices:
                subparsers.choices[args.command_name].print_help()
            else:
                print(f"No such command: {args.command_name}")
        else:
            print(COMMANDS_HELP)
        return

    elif args.command == "login":
        login(args.email, args.password)
        config._load_config()  # refresh after login

    elif args.command == "status":
        print("=== DAB CLI Authentication Status ===")
        user_info = get_current_user()
        if user_info is None:
            print("Login status  : Not logged in")
            return
        if "error" in user_info and user_info["error"] == 500:
            print("Server error (500). Try again later.")
            return
        if not user_info.get("user"):
            print("Login status  : Not logged in")
        else:
            u = user_info["user"]
            print("Login status  : Logged in")
            print("User ID       :", u.get("id"))
            print("Email         :", u.get("email"))

    elif args.command == "logout":
        clear_credentials()
        print("You are now logged out.")

    elif args.command == "search":
        if not require_login(config):
            return
        search_and_print(args.query, args.type)

    elif args.command == "discography":
        from artist import download_discography
        download_discography(
            artist_query=args.artist,
            sort_by=args.sort_by,
            sort_order=args.sort_order,
            view_only=args.view_only,
            limit=args.limit,
            cli_args=args  # pass args for metadata overrides
        )

    elif args.command == "track":
        if not require_login(config):
            return
        from downloader import _sanitize_filename
        output_format = args.format or config.output_format
        directory = args.path or config.output_directory

        track_meta_raw = get_track_metadata_by_id(args.track_id)
        if not track_meta_raw:
            print("Track not found.")
            return

        track_meta = {
            "title": args.title or track_meta_raw.get("title", ""),
            "artist": args.artist or track_meta_raw.get("artist", ""),
            "albumTitle": args.album or track_meta_raw.get("albumTitle", ""),
            "genre": args.genre or track_meta_raw.get("genre", ""),
            "releaseDate": args.date or track_meta_raw.get("releaseDate", "")
        }

        raw_path = download_track(
            track_id=args.track_id,
            quality="27" if output_format == "flac" else "5",
            directory=directory,
            track_meta=track_meta_raw
        )
        if not raw_path:
            return

        final_path = raw_path
        cover_url = track_meta_raw.get("albumCover")
        cover_path = None
        if cover_url:
            clean_title = _sanitize_filename(track_meta["title"] or "cover")
            cover_path = download_cover_image(
                cover_url, os.path.join(directory, f"{clean_title}.jpg")
            )

        tag_audio(
            final_path,
            {
                "title": track_meta["title"],
                "artist": track_meta["artist"],
                "album": track_meta["albumTitle"],
                "genre": track_meta["genre"],
                "date": track_meta["releaseDate"][:4]
            },
            cover_path=cover_path
        )

        if cover_path and os.path.exists(cover_path) and not config.keep_cover_file:
            try:
                os.remove(cover_path)
            except:
                pass

        print(f"[download] Completed: {final_path}")

    elif args.command == "album":
        if not require_login(config):
            return
        inp = args.album_id_or_title.strip()

        if inp.startswith("al") and len(inp) > 5:
            print(f"Fetching album by ID: {inp}")
            download_album(inp, cli_args=args)
            return

        print(f"Searching for album titled '{inp}'...")
        matches = find_album_by_title(inp)

        if not matches:
            print("No albums found.")
            return

        if len(matches) == 1:
            album = matches[0]
            print(f"Selected: {album['title']} by {album['artist']} (ID: {album['id']})")
            download_album(album["id"], cli_args=args)
            return

        table = [
            [i, a["title"], a["artist"], a.get("releaseDate", "")[:4], a["id"]]
            for i, a in enumerate(matches, 1)
        ]
        print(tabulate(table, headers=["No", "Title", "Artist", "Year", "Album ID"], tablefmt="fancy_grid"))
        try:
            choice = int(input("\nEnter the number of the album to download: "))
            download_album(matches[choice - 1]["id"], cli_args=args)
        except:
            print("Invalid selection.")

    elif args.command == "play":
        if not require_login(config):
            return
        stream_cli_entry(args)

    elif args.command == "library":
        from library import view_library, list_user_libraries, download_library

        if args.library_id:
            if args.view_only:
                view_library(args.library_id)
            else:
                download_library(args.library_id, quality=args.quality, cli_args=args)
        else:
            list_user_libraries()

    elif args.command == "favorites":
        from library import get_favorites
        get_favorites()

    elif args.command == "config":
        if args.path:
            print(f"Config file path: {config.config_path}")
        else:
            config.interactive_setup()
        return

    else:
        print("Unknown command.\n")
        print(ASCII_ART)
        print(COMMANDS_HELP)


if __name__ == "__main__":
    main()
