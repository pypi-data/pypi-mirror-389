# downloader.py

import os
import sys
import time
import threading
import unicodedata
import requests

from importlib import resources
from tqdm import tqdm
from dabcli.config import config
from dabcli.api import get
from dabcli.utils import require_login

# --- State flags ---
_PAUSED = False
_STOPPED = False
_CURRENT_PBAR = None


# --- Keyboard listener (cross-platform) ---
def _keypress_listener():
    """Thread: watches keyboard input for pause/resume/stop.
    Always tries to restore terminal settings on POSIX (termios) in a finally block.
    """
    global _PAUSED, _STOPPED, _CURRENT_PBAR

    if os.name == "nt":  # Windows
        import msvcrt
        try:
            while not _STOPPED:
                try:
                    if msvcrt.kbhit():
                        key = msvcrt.getch().decode(errors="ignore").lower()
                        if key == "p":
                            _PAUSED = not _PAUSED
                            tqdm.write("[Downloader] Paused" if _PAUSED else "[Downloader] Resumed")
                            if _CURRENT_PBAR and not _PAUSED:
                                _CURRENT_PBAR.refresh()
                        elif key == "q":
                            _STOPPED = True
                            tqdm.write("[Downloader] Stopped by user")
                except Exception:
                    # keep loop alive for unexpected decode/read errors
                    pass
                time.sleep(0.1)
        except Exception:
            pass
    else:  # POSIX (Linux/macOS/Termux)
        import termios, tty, select

        fd = None
        old_settings = None
        try:
            fd = sys.stdin.fileno()
            # tcgetattr can fail if stdin is not a real tty — guard it
            try:
                old_settings = termios.tcgetattr(fd)
                tty.setcbreak(fd)
            except Exception:
                # If we can't access termios, don't crash; listener will still try to read but may not behave perfectly
                old_settings = None

            while not _STOPPED:
                try:
                    dr, _, _ = select.select([sys.stdin], [], [], 0.1)
                    if dr:
                        key = sys.stdin.read(1).lower()
                        if key == "p":
                            _PAUSED = not _PAUSED
                            tqdm.write("[Downloader] Paused" if _PAUSED else "[Downloader] Resumed")
                            if _CURRENT_PBAR and not _PAUSED:
                                _CURRENT_PBAR.refresh()
                        elif key == "q":
                            _STOPPED = True
                            tqdm.write("[Downloader] Stopped by user")
                except Exception:
                    # ignore read/select errors and continue
                    pass
                time.sleep(0.05)

        finally:
            # Always attempt to restore terminal settings; fall back to `stty sane` for safety (Termux)
            try:
                if old_settings is not None and fd is not None:
                    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                else:
                    # last-resort fix (works in Termux / many POSIX shells)
                    os.system("stty sane")
            except Exception:
                try:
                    os.system("stty sane")
                except Exception:
                    pass


def _start_controls():
    """Start the keyboard listener as a non-daemon thread and return the thread."""
    t = threading.Thread(target=_keypress_listener, daemon=False)
    t.start()
    return t


def _wait_if_paused():
    global _PAUSED, _STOPPED
    while _PAUSED and not _STOPPED:
        time.sleep(0.2)


# --- Filename utilities ---
def _sanitize_filename(name: str) -> str:
    name = unicodedata.normalize("NFKC", name)
    return "".join(c for c in name if c.isalnum() or c in " -_()[]{}.,").strip() or "untitled"


def _format_filename(track: dict, output_format: str, index: int = None, include_album: bool = False) -> str:
    """Generate a sanitized filename for a track."""
    title = _sanitize_filename(track.get("title") or "untitled")
    artist = _sanitize_filename(track.get("artist") or "unknown artist")
    
    if include_album:
        album = _sanitize_filename(track.get("albumTitle") or "unknown album")
        base = f"{artist} - {album} - {title}"
    else:
        base = f"{artist} - {title}"
    
    if index is not None:
        base = f"{index:02d} - {base}"
    
    return f"{base}.{output_format}"


def get_stream_url(track_id: str, quality: str = "27"):  
    if not require_login(config):  
        return None  
    result = get("/stream", params={"trackId": track_id, "quality": quality})  
    if not result:  
        return None  
    return result.get("url")  
  
  
# --- Main download ---  
def download_track(track_id: str, filename: str = None, quality: str = None,  
                   directory: str = None, index: int = None, track_meta: dict = None):  
    global _CURRENT_PBAR, _PAUSED, _STOPPED  
    _PAUSED = False  
    _STOPPED = False  
    _CURRENT_PBAR = None  
  
    if not require_login(config):  
        return None  
  
    quality = quality or ("27" if config.output_format == "flac" else "5")  
    directory = directory or config.output_directory  
    os.makedirs(directory, exist_ok=True)  
  
    if not filename and track_meta:  
        filename = _format_filename(track_meta, config.output_format, index)  
  
    filename = _sanitize_filename(filename)  
    filepath = os.path.join(directory, filename)  
  
    # Skip any existing file  
    if os.path.exists(filepath):  
        tqdm.write(f"[Downloader] Skipped (exists): {filepath}")  
        return filepath  

    if config.test_mode:
        tqdm.write(f"[TEST MODE] Would download track {track_id} → {filepath}")

        import shutil
        from pathlib import Path

        # Safely locate the bundled sample audio using importlib.resources
        try:
            with resources.files("dabcli.assets").joinpath("silence.flac").open("rb") as src:
                with open(filepath, "wb") as dst:
                    shutil.copyfileobj(src, dst)
            tqdm.write(f"[TEST MODE] Copied sample FLAC → {filepath}")
        except (FileNotFoundError, ModuleNotFoundError, OSError) as e:
            tqdm.write(f"[TEST MODE] Could not find silence.flac ({e}), creating empty placeholder.")
            with open(filepath, "wb") as f:
                f.write(b"")  # harmless fallback

        return filepath

    stream_url = get_stream_url(track_id, quality)  
    if not stream_url:  
        return None  
  
    tqdm.write(f"[Downloader] Downloading: {filepath}")  
    tqdm.write("[Controls] Press 'p' = Pause/Resume | 'q' = Stop")  
  
    _start_controls()  # launch keyboard thread  
  
    try:  
        with requests.get(stream_url, stream=True, timeout=30) as r:  
            r.raise_for_status()  
            total = int(r.headers.get("content-length", 0))  
            with open(filepath, "wb") as f, tqdm(  
                total=total,  
                unit="B",  
                unit_scale=True,  
                unit_divisor=1024,  
                desc="Downloading",  
                ncols=70,  
                disable=not getattr(config, "show_progress", True)  
            ) as pbar:  
                _CURRENT_PBAR = pbar  
                for chunk in r.iter_content(chunk_size=8192):  
                    if _STOPPED:  
                        tqdm.write("[Downloader] Download stopped before completion.")  
                        _CURRENT_PBAR = None  
                        return None  
                    _wait_if_paused()  
                    if chunk:  
                        f.write(chunk)  
                        pbar.update(len(chunk))  
  
            tqdm.write("[Downloader] Download completed.")  
            return filepath  
  
    except requests.RequestException as e:  
        tqdm.write(f"[Downloader] Download failed: {e}")  
        return None  
    except OSError as e:  
        tqdm.write(f"[Downloader] File write error: {e}")  
        return None
