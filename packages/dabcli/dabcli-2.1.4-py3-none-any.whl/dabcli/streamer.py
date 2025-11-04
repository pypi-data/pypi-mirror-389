# streamer.py

import subprocess
import time
import tempfile
import os
import socket
import json
import threading
import itertools
from dabcli.api import get
from dabcli.config import config
from dabcli.utils import require_login

# ----------------- Track fetching -----------------

def get_track_info(track, quality: str = None, search_if_missing=True):
    """
    Fetch metadata + stream URL for a track.
    'track' can be:
      - int/str: track ID only
      - dict: may already contain 'id', 'title', 'artist'
    search_if_missing: whether to search for metadata if missing (False for album/library)
    Returns dict with 'stream_url' populated, or None on failure.
    """
    if not require_login(config):
        return None

    # Normalize track to dict
    if isinstance(track, (int, str)):
        track_id = str(track)
        track = {"id": track_id}
    elif isinstance(track, dict):
        track_id = str(track.get("id"))
        if not track_id:
            return None
    else:
        return None

    # Only search if metadata missing and allowed
    if search_if_missing and ("title" not in track or "artist" not in track):
        result = get("/search", params={"q": track_id})
        if not result or not result.get("tracks"):
            print(f"Could not find any tracks via search for ID {track_id}")
            return None
        match = next((t for t in result["tracks"] if str(t.get("id")) == track_id), None)
        if not match:
            print(f"Track ID {track_id} not found in search results")
            return None
        track.update(match)

    # Always fetch stream URL
    quality = quality or config.stream_quality
    stream_result = get("/stream", params={"trackId": track_id, "quality": quality})
    stream_url = stream_result.get("url") if stream_result else None
    if not stream_url:
        print(f"Could not get stream URL for track {track_id}")
        return None

    track["stream_url"] = stream_url
    return track

def get_library_tracks(library_id: str):
    if not require_login(config):
        return []

    result = get(f"/libraries/{library_id}")
    if not result or "library" not in result:
        print("Could not load library.")
        return []

    return result["library"].get("tracks", [])

# ----------------- IPC-based playback -----------------

def play_ipc_queue(tracks, quality=None):
    """Play a list of tracks via MPV IPC, using stream_url from track dict."""
    if not require_login(config):
        return

    print("\n============ DAB CLI Player ============")
    print("Loading playlist...", end="", flush=True)

    spinner_running = True

    def spinner():
        for frame in itertools.cycle([".", "..", "...", " ..", "  .", "   "]):
            if not spinner_running:
                break
            print(f"\rLoading playlist{frame}", end="", flush=True)
            time.sleep(0.4)

    spin_t = threading.Thread(target=spinner)
    spin_t.start()

    # Ensure every track has stream_url
    track_infos = []
    for t in tracks:
        if "stream_url" not in t:
            info = get_track_info(t, quality)
            if info:
                track_infos.append(info)
        else:
            track_infos.append(t)

    spinner_running = False
    spin_t.join()

    if not track_infos:
        print("\rNo playable stream URLs.")
        return

    print("\rLoading playlist... Done.     ")
    print("=========================================")

    sock_path = os.path.join(tempfile.gettempdir(), "dab_mpv.sock")
    try:
        os.remove(sock_path)
    except FileNotFoundError:
        pass

    cmd = [
        "mpv",
        "--no-video",
        "--force-window=no",
        "--audio-display=no",
        "--msg-level=all=no",
        "--term-playing-msg=",
        f"--input-ipc-server={sock_path}"
    ] + [t["stream_url"] for t in track_infos]

    print("\n[SPACE]=Play/Pause | > Next | < Prev | q Quit")

    # Player state
    state = {"elapsed": 0, "paused": False, "started": False}

    def ipc_listener():
        time.sleep(0.4)
        attempts = 0
        while attempts < 10:
            try:
                s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                s.connect(sock_path)
                break
            except FileNotFoundError:
                attempts += 1
                time.sleep(0.3)
        else:
            return

        s.send(b'{"command": ["observe_property", 1, "playlist-pos"]}\n')
        s.send(b'{"command": ["observe_property", 2, "playback-time"]}\n')
        s.send(b'{"command": ["observe_property", 3, "pause"]}\n')

        def timer_loop():
            while True:
                if state["started"]:
                    out = "(Paused)" if state["paused"] else "[" + time.strftime("%H:%M:%S", time.gmtime(state["elapsed"])) + "]"
                    print(f"\r{out}", end="", flush=True)
                time.sleep(1)

        threading.Thread(target=timer_loop, daemon=True).start()

        while True:
            data = s.recv(4096)
            if not data:
                break
            for raw in data.splitlines():
                try:
                    msg = json.loads(raw.decode())
                except Exception:
                    continue

                if msg.get("event") == "property-change":
                    name = msg.get("name")
                    value = msg.get("data")

                    if name == "playlist-pos":
                        idx = value if isinstance(value, int) else 0
                        if idx < len(track_infos):
                            t = track_infos[idx]
                            state["elapsed"] = 0
                            state["started"] = True
                            print(f"\nNow Playing: {t.get('artist', '—')} — {t.get('title', '—')}")
                    elif name == "playback-time":
                        state["elapsed"] = int(value or 0)
                    elif name == "pause":
                        state["paused"] = bool(value)

    threading.Thread(target=ipc_listener, daemon=True).start()

    try:
        subprocess.run(cmd)
    except Exception as e:
        print("mpv error:", e)

    try:
        os.remove(sock_path)
    except Exception:
        pass

# ----------------- Unified play interface -----------------

def play_tracks(tracks: list, quality: str = None, search_if_missing=True):
    """
    Fetch info & play via IPC for a list of tracks.
    - search_if_missing=False for albums/libraries
    """
    track_infos = []
    for t in tracks:
        info = t if "stream_url" in t else get_track_info(t, quality, search_if_missing=search_if_missing)
        if info:
            track_infos.append(info)

    if not track_infos:
        print("No playable tracks.")
        return

    play_ipc_queue(track_infos, quality=quality)

# ----------------- CLI entry -----------------

def stream_cli_entry(args):
    tracks_to_play = []

    if getattr(args, "track_id", None):
        tracks_to_play.append({"id": args.track_id})
        play_tracks(tracks_to_play, quality=getattr(args, "quality", None), search_if_missing=True)

    elif getattr(args, "album_id", None):
        result = get("/album", params={"albumId": args.album_id})
        tracks_to_play = result.get("album", {}).get("tracks", [])
        play_tracks(tracks_to_play, quality=getattr(args, "quality", None), search_if_missing=False)

    elif getattr(args, "queue", None):
        tracks_to_play = [{"id": tid} for tid in args.queue]
        play_tracks(tracks_to_play, quality=getattr(args, "quality", None), search_if_missing=True)

    elif getattr(args, "library_id", None):
        tracks_to_play = get_library_tracks(args.library_id)
        play_tracks(tracks_to_play, quality=getattr(args, "quality", None), search_if_missing=False)
