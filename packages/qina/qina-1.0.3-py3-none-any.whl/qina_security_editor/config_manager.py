#!/usr/bin/env python3
"""
Config Manager for QINA Security Editor
Persists API key and team ID to a config file.
"""

import json
import os
import sys
import uuid
import re
from pathlib import Path
from typing import Optional, Dict, Any


class ConfigManager:
    def __init__(self, app_name: str = "qina_security_editor"):
        self.app_name = app_name
        self.config_dir = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / app_name
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "config.json"

    def load(self) -> Dict[str, Any]:
        if not self.config_file.exists():
            return {}
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                return json.load(f) or {}
        except Exception:
            return {}

    def save(self, data: Dict[str, Any]) -> None:
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def get_api_key(self) -> Optional[str]:
        return self.load().get("api_key")

    def get_team_id(self) -> Optional[str]:
        return self.load().get("team_id")

    def set_api_key(self, api_key: str) -> None:
        data = self.load()
        data["api_key"] = api_key
        self.save(data)

    def set_team_id(self, team_id: str) -> None:
        data = self.load()
        data["team_id"] = str(team_id)
        self.save(data)

    def clear_token(self) -> None:
        data = self.load()
        data.pop("token", None)
        self.save(data)

    def set_token(self, token: str) -> None:
        data = self.load()
        data["token"] = token
        self.save(data)

    def get_token(self) -> Optional[str]:
        return self.load().get("token")

    def clear_all(self) -> None:
        try:
            if self.config_file.exists():
                self.config_file.unlink()
        except Exception:
            pass


    def get_api_base_url(self) -> str:
        """Get the API base URL (QA or Production)"""
        return os.environ.get('CLOUDDEFENSE_API_BASE_URL', 'https://console.clouddefenseai.com')
    
    def get_ws_base_url(self) -> str:
        """Get the WebSocket base URL (QA or Production)"""
        return os.environ.get('CLOUDDEFENSE_WS_BASE_URL', 'wss://console.clouddefenseai.com')
    
    def get_environment(self) -> str:
        """Get the current environment (qa or prod)"""
        api_url = self.get_api_base_url()
        if 'qa.clouddefenseai.com' in api_url:
            return 'qa'
        elif 'console.clouddefenseai.com' in api_url:
            return 'prod'
        else:
            return 'prod'  # Default to Production

    # === CLI ID management ===
    def _sanitize_for_filename(self, value: str) -> str:
        try:
            sanitized = re.sub(r'[^A-Za-z0-9._-]+', '_', value)
            return sanitized.strip('_') or 'unknown'
        except Exception:
            return 'unknown'

    def _session_key(self) -> str:
        # Prefer TTY path when available (distinct per terminal window)
        tty_path = None
        try:
            tty_path = os.ttyname(sys.stdin.fileno())
        except Exception:
            tty_path = os.environ.get('TTY')
        if tty_path:
            return f"tty_{self._sanitize_for_filename(tty_path)}"

        # Fallback: use session id and parent pid
        sid = None
        try:
            sid = os.getsid(0)
        except Exception:
            sid = None
        ppid = os.getppid()
        return f"sid_{sid or 'na'}_ppid_{ppid}"

    def get_cli_id_for_session(self) -> str:
        """Get or create a stable CLI ID for the current terminal session.

        Priority:
        1) Respect CLOUDDEFENSE_CLIENT_ID if already set
        2) Persist per-terminal id under XDG_RUNTIME_DIR or /tmp keyed by TTY/session
        """
        env_id = os.environ.get('CLOUDDEFENSE_CLIENT_ID')
        if env_id:
            return env_id

        session_key = self._session_key()
        runtime_dir = Path(os.environ.get('XDG_RUNTIME_DIR', '/tmp'))
        runtime_dir.mkdir(parents=True, exist_ok=True)
        id_file = runtime_dir / f"qina_cli_id_{session_key}"

        try:
            if id_file.exists():
                value = id_file.read_text(encoding='utf-8').strip()
                if value:
                    os.environ['CLOUDDEFENSE_CLIENT_ID'] = value
                    return value
        except Exception:
            pass

        # Create new UUID and persist
        new_id = str(uuid.uuid4())
        try:
            id_file.write_text(new_id, encoding='utf-8')
        except Exception:
            # As a last resort, continue without persisting
            pass

        os.environ['CLOUDDEFENSE_CLIENT_ID'] = new_id
        return new_id

    def get_session_tmp_dir(self) -> Path:
        """Return per-session temporary directory path.

        Uses `/tmp/qina_security_scan_<session_key>` to isolate concurrent terminals.
        """
        cli_id = self.get_cli_id_for_session()
        # Prefer a human-stable key for directory naming to avoid overly long names
        session_key = self._session_key()
        base = Path('/tmp')
        return base / f"qina_security_scan_{self._sanitize_for_filename(session_key)}"
