import os
from tabulate import tabulate
from dabcli.api import get
from dabcli.config import config
from dabcli.utils import require_login
from dabcli.downloader import download_track
from dabcli.tagger import tag_audio
from dabcli.cover import download_cover_image

def sanitize_filename(name):
    return ''.join(c for c in name if c.isalnum() or c in ' _-').rstrip()

def view_library(library_id: str):
    """Print library info and all tracks in tabulate format, using full pagination"""
    if not require_login(config):
        return

    # Fetch library metadata (first page)
    first_page = get(f"/libraries/{library_id}?page=1&limit=1")
    if not first_page or "library" not in first_page:
        print("[Library] Failed to fetch library info.")
        return

    lib = first_page["library"]
    print("=== Library Info ===")
    print("ID      :", lib.get("id"))
    print("Name    :", lib.get("name"))
    print("Public  :", lib.get("isPublic"))
    print("Created :", lib.get("createdAt"))

    # Fetch all tracks via pagination
    tracks = []
    page = 1
    page_size = 100  # adjust if API allows more per page
    while True:
        result = get(f"/libraries/{library_id}?page={page}&limit={page_size}")
        if not result or "library" not in result:
            break
        page_tracks = result["library"].get("tracks", [])
        if not page_tracks:
            break
        tracks.extend(page_tracks)
        page += 1

    if not tracks:
        print("[Library] No tracks found.")
        return

    # tabulate tracks
    table = [
        [i + 1, t.get("id"), t.get("title"), t.get("artist"), t.get("albumTitle"), t.get("releaseDate")[:4]]
        for i, t in enumerate(tracks)
    ]
    print(tabulate(table, headers=["#", "ID", "Title", "Artist", "Album", "Year"], tablefmt="fancy_grid"))

def list_user_libraries():
    """List all libraries belonging to the current user"""
    if not require_login(config):
        return

    result = get("/libraries")
    if not result or "libraries" not in result:
        print("[Library] Failed to fetch libraries.")
        return

    libraries = result["libraries"]
    if not libraries:
        print("[Library] No libraries found.")
        return

    table = [
        [
            lib.get("id"),
            lib.get("name"),
            lib.get("trackCount"),
            "Yes" if lib.get("isPublic") else "No",
            lib.get("createdAt")[:10]  # date only
        ]
        for lib in libraries
    ]

    print("=== User Libraries ===")
    print(tabulate(table, headers=["ID", "Name", "Tracks", "Public", "Created"], tablefmt="fancy_grid"))


def get_favorites():
    """Fetch and print user's favorite tracks"""
    if not require_login(config):
        return

    result = get("/favorites")
    if not result or "favorites" not in result:
        print("[Favorites] No favorites found or failed to fetch.")
        return

    favorites = result["favorites"]
    table = [
        [f["id"], f.get("title"), f.get("artist"), f.get("albumTitle"), f.get("releaseDate")[:4]]
        for f in favorites
    ]
    print("=== Favorites ===")
    print(tabulate(table, headers=["ID", "Title", "Artist", "Album", "Year"], tablefmt="fancy_grid"))

def download_library(library_id: str, quality: str = None, cli_args=None):
    if not require_login(config):
        return

    # get first page (also used for metadata)
    first_page = get(f"/libraries/{library_id}?page=1&limit=1")
    if not first_page or "library" not in first_page:
        print("[Library] Failed to load library.")
        return

    library = first_page["library"]

    # collect all tracks via pagination
    tracks = []
    page = 1
    limit = 100  # adjust if API has a different max allowed
    while True:
        result = get(f"/libraries/{library_id}?page={page}&limit={limit}")
        if not result or "library" not in result:
            break

        page_tracks = result["library"].get("tracks", [])
        if not page_tracks:
            break

        tracks.extend(page_tracks)
        page += 1

    if not tracks:
        print("[Library] No tracks found.")
        return

    title = sanitize_filename(library.get("name", f"library_{library_id}"))
    output_format = config.output_format
    quality = quality or ("27" if output_format == "flac" else "5")

    lib_folder = os.path.join(config.output_directory, f"{title} [{output_format.upper()}]")
    os.makedirs(lib_folder, exist_ok=True)

    print(f"[Library] Downloading: {title} ({len(tracks)} tracks)")

    playlist_paths = []
    for idx, track in enumerate(tracks, 1):
        print(f"[{idx}/{len(tracks)}] {track['title']} — {track['artist']}")

        raw_path = download_track(
            track_id=track["id"],
            quality=quality,
            directory=lib_folder,
            track_meta=track
        )
        if not raw_path:
            print("[Library] Skipping: download failed.")
            continue

        converted_path = raw_path  # same format assumption

        metadata = {
            "title": getattr(cli_args, "title", None) or track.get("title", ""),
            "artist": getattr(cli_args, "artist", None) or track.get("artist", ""),
            "album": getattr(cli_args, "album", None) or track.get("albumTitle", ""),
            "genre": getattr(cli_args, "genre", None) or track.get("genre", ""),
            "date": getattr(cli_args, "date", None) or track.get("releaseDate", "")[:4]
        }

        from downloader import _sanitize_filename
        cover_url = track.get("albumCover")
        cover_path = None
        if cover_url:
            clean_title = _sanitize_filename(track.get("title", "cover"))
            cover_path = download_cover_image(
                cover_url, os.path.join(lib_folder, f"{clean_title}.jpg")
            )

        tag_audio(converted_path, metadata, cover_path=cover_path)

        if cover_path and os.path.exists(cover_path) and not config.keep_cover_file:
            try:
                os.remove(cover_path)
            except Exception:
                pass

        if config.delete_raw_files and raw_path != converted_path:
            try:
                os.remove(raw_path)
            except Exception as e:
                print(f"[Library] Could not delete raw file: {e}")

        playlist_paths.append(os.path.basename(converted_path))

    m3u_path = os.path.join(lib_folder, "library.m3u8")
    with open(m3u_path, "w", encoding="utf-8") as m3u:
        for filename in playlist_paths:
            m3u.write(filename + "\n")

    print(f"[Library] Finished: {len(playlist_paths)} tracks saved to {lib_folder}")
    print(f"[Library] Playlist written to: {m3u_path}")
