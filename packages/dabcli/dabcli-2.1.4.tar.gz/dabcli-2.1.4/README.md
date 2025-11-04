# 🎧 DAB CLI

**DAB CLI** is an advanced, extensible, and user-friendly command-line tool for accessing [DABMusic](https://dabmusic.xyz) — a free, open-source digital music library and streaming service.  
It supports searching, downloading, metadata tagging, artist discography downloads, local streaming, and more — all from your terminal.



---
## 🚀 What's New in v2.0

- **Smarter Downloader**: Skips existing files; supports pause/resume/stop  
- **Artist Discography Download**: Fetch all albums by artist name or ID  
- **Enhanced MPV IPC Player**: Stream tracks, albums, libraries, or queues with live metadata, timers, and playback controls (space=play/pause, arrows=next/prev, q=quit)  
- **Lyrics & Cover Embedding**: Auto-download covers and lyrics  
- **Metadata Overrides**: Customize title, artist, album, genre, date, and path during downloads  
- **Version Checking & Improved CLI Help**: Always know if your CLI is up-to-date  

> v2.0 makes downloads smarter, streaming interactive, and metadata fully customizable.



---

## 📦 Installation

### 1. Install directly from PyPI

```bash
pip install --upgrade dabcli
cd dabcli
### 2. Hurray! It's that simple.
````bash
dabcl
```



---
## 🔐 Authentication
### Login to DAB
```bash
dabcli login "<email>" "<password>" 
```
### Logout
```bash
dabcli logout
```
### Check Login Status
```bash
dabcli status
```



---
## 🔍 Search
By default, searching checks tracks, albums, and artists. Use `--type` to restrict:
```bash
dabcli search "<query>"
```
```bash
dabcli search "<query>" --type track
```
```bash
dabcli search "<query>" --type album
```
```bash
dabcli search "<query>" --type artist
```


---
## ⬇️ Downloads

All downloads support metadata overrides:
```shell
--format mp3|flac --title "<title>" --artist "<artist>" --album "<album>" --genre "<genre>" --date "<YYYY-MM-DD>" --path "<custom/path>"
```

### 1. Download a Single Track
Search by track name or ID (search first, then select):
```shell
dabcli track "<track-id or name>" [metadata overrides]
```

### 2. Download an Album
```shell
dabcli album "<album-id or title>" [metadata overrides]
```

### 3. Download a Library
#### List all user libraries
```shell
dabcli library
```
#### Download A Library 
```bash
dabcli library <library-id> [--view-only] [metadata overrides]
```

### 4. Download an Artist Discography
```bash
dabcli discography "<artist name or ID>" [--view-only] [metadata overrides]
```


---
## ▶️ Streaming
### Stream tracks, albums, libraries, or queues:
```bash
dabcli play --track-id <id>
dabcli play --album-id <id>
dabcli play --library-id <id>
dabcli play --queue <id1> <id2> <id3>
```
#### Interactive controls while streaming:
- **Space**: Play/Pause
- **< / >**: Previous/Next
- **q**: Quit


---
## ♥️ Favorites
### List all user favorites:
```bash
dabcli favorites
```


---
## 🔄 Updates & Version Check
### Check Current Version
```bash
dabcli --version
```
### Run an Update (from GitHub)
```bash
dabcli update 
```

**Note**: If update fails, run
```bash
pip install --upgrade dabcli
python3 dabcli.py --version
```


---
## ⚙️ Configuration

After first launch, a config.json file will be created automatically (usually in your platform’s app data directory).

Example:
```json
{
    "output_format": "flac",
    "output_directory": "./downloads",
    "use_metadata_tagging": true,
    "stream_quality": "27",
    "stream_player": "mpv",
    "test_mode": false,
    "delete_raw_files": true,
    "keep_cover_file": false,
    "get_lyrics": true,
    "debug": false,
    "show_progress": true
}

You can set-up configs interactively using `dabcli config` or find the config.json file location using `dabcli config --path`.
```
### Config Options

- `output_format`: `"flac"` or `"mp3"` — format for downloaded tracks  
- `output_directory`: Directory where all downloads will be saved  
- `stream_quality`: `"27"` = FLAC, `"5"` = MP3 — controls quality of streaming/downloads  
- `stream_player`: Player used for streaming (currently only `mpv` supported)  
- `delete_raw_files`: Whether to delete the raw files.
- `get_lyrics`: Download and embed lyrics into tracks if available  
- `keep_cover_file`: Keep a separate cover image file per track/album, or only embed it in metadata
- `show_progress`: Whether to show progress using `tqdm` or not.
- `test_mode`, `debug`: Developer side configurations, not intended for users.

---
## 🧩 Dependencies

- **Python 3.7+**
- Python packages: `requests`, `mutagen`, `tqdm`, `tabulate`
- External tools: `mpv` (optional, for streaming)

```bash
pip install -r requirements.txt
```

---
## 🌐 About DABMusic

DABMusic is a community-driven open-source platform providing high-quality, unrestricted music streaming and downloads.

- **Website**: [dabmusic.xyz](https://dabmusic.xyz)
- **Discord**: [Join the community](https://discord.gg/dabmusic-1347344910008979548)

---
## 👥 Credits

- **Developer:** [sherlockholmesat221b](https://github.com/sherlockholmesat221b)
- **superadmin0 (Creator of DABMusic)**
- **Contributors and Testers:** [joehacks](https://github.com/holmesisback), [uimaxbai](https://github.com/uimaxbai)

---
## 📝License
### MIT License
**Copyright (c) 2025 sherlockholmesat221b**

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---
## ⚠️ Disclaimer

This software is provided **for educational and archival purposes only**. It does **not host or distribute music files**, nor circumvent DRM.  Users are **responsible for complying with all applicable laws**. The software is distributed AS IS and the author claims no legal liability of any kind.

