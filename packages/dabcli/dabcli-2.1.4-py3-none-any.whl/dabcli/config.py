# config.py

import json
import requests
from dataclasses import dataclass, field, asdict
from pathlib import Path
from platformdirs import user_config_dir, user_cache_dir

# === CONFIG DIRECTORIES ===
CONFIG_DIR = Path(user_config_dir("dabcli"))
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_PATH = CONFIG_DIR / "config.json"

DOWNLOAD_DIR = Path(user_cache_dir("dabcli")) / "downloads"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

CURRENT_CONFIG_VERSION = 1  # bump this when config schema changes

@dataclass
class Config:
    # === User settings ===
    email: str = ""
    password: str = ""
    output_format: str = "flac"
    output_directory: str = str(DOWNLOAD_DIR)
    use_metadata_tagging: bool = True
    token: str = ""
    stream_quality: str = "27"
    stream_player: str = "mpv"
    test_mode: bool = False
    delete_raw_files: bool = True
    keep_cover_file: bool = False
    get_lyrics: bool = True
    base_url: str = "https://dabmusic.xyz/api"

    # === Internal flags ===
    debug: bool = field(default=False, init=False)
    show_progress: bool = field(default=True, init=False)

    # === Config version ===
    config_version: int = field(default=CURRENT_CONFIG_VERSION, init=False)

    def __post_init__(self):
        if CONFIG_PATH.exists():
            self._load_config()
            self._migrate_if_needed()

    def _load_config(self):
        try:
            with CONFIG_PATH.open("r") as f:
                data = json.load(f)
        except Exception as e:
            raise ValueError(f"Invalid JSON in config file: {e}")

        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def _save_config(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self.config_version = CURRENT_CONFIG_VERSION
        with CONFIG_PATH.open("w") as f:
            json.dump(asdict(self), f, indent=4)

    def _save_token(self, token: str):
        self.token = token
        self._save_config()

    def _migrate_if_needed(self):
        if getattr(self, "config_version", 0) < CURRENT_CONFIG_VERSION:
            print(f"Migrating config from version {self.config_version} → {CURRENT_CONFIG_VERSION}")
            # Add any migration logic here
            self.config_version = CURRENT_CONFIG_VERSION
            self._save_config()

    # === Authentication Methods ===
    def _retry_login(self):
        if not self.email or not self.password:
            raise Exception("Cannot re-authenticate: Email or password missing from config")

        session = requests.Session()
        url = f"{self.base_url}/auth/login"
        payload = {"email": self.email, "password": self.password}
        resp = session.post(url, json=payload)

        if resp.status_code == 200 and "session" in session.cookies:
            token = session.cookies.get("session")
            self._save_token(token)
            print("Auto-login successful, token refreshed.")
        else:
            raise Exception("Auto-login failed. Please check credentials.")

    def get_auth_header(self):
        if not self.token:
            print("No token found, attempting login...")
            self._retry_login()
        return {"Cookie": f"session={self.token}"}

    def is_logged_in(self):
        return bool(self.token)

    def logout(self):
        self.token = ""
        self.email = ""
        self.password = ""
        self._save_config()
        print("You have been logged out.")

    # === Interactive Config Setup ===

    # Inside Config class in config.py

    def interactive_setup(self):
        """Interactive CLI setup for dabcli config"""
        print("=== DAB CLI Interactive Configuration ===")
        print(f"Config file path: {CONFIG_PATH}\n")
    
        # Download directory
        out_dir = input(f"Download directory [{self.output_directory}]: ") or self.output_directory
    
        # Default format
        fmt = input(f"Default format (mp3/flac) [{self.output_format}]: ") or self.output_format
        while fmt.lower() not in ["mp3", "flac"]:
            print("Invalid format. Choose 'mp3' or 'flac'.")
            fmt = input(f"Default format (mp3/flac) [{self.output_format}]: ") or self.output_format
    
        # Stream quality
        quality = input(f"Stream quality [{self.stream_quality}]: ") or self.stream_quality

        # Metadata tagging
        default_tag = 'yes' if self.use_metadata_tagging else 'no'
        use_tags = input(f"Enable metadata tagging? (yes/no) [{default_tag}]: ") or default_tag
        use_tags_bool = use_tags.lower() in ["yes", "y"]

        # Apply inputs
        self.output_directory = out_dir
        self.output_format = fmt.lower()
        self.stream_quality = quality
        self.use_metadata_tagging = use_tags_bool

        # Save updated config
        self._save_config()
        print(f"\nConfiguration saved to {CONFIG_PATH}")
        print("Current settings:")
        print(f"  Download directory  : {self.output_directory}")
        print(f"  Default format      : {self.output_format}")
        print(f"  Stream quality      : {self.stream_quality}")
        print(f"  Metadata tagging    : {'enabled' if self.use_metadata_tagging else 'disabled'}")

    @property  
    def config_path(self):  
        return CONFIG_PATH

# Clear credentials function
def clear_credentials():
    try:
        if CONFIG_PATH.exists():
            with CONFIG_PATH.open("r") as f:
                data = json.load(f)
        else:
            data = {}
        data.pop("token", None)
        data.pop("email", None)
        data.pop("password", None)
        with CONFIG_PATH.open("w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Failed to clear credentials: {e}")


config = Config()