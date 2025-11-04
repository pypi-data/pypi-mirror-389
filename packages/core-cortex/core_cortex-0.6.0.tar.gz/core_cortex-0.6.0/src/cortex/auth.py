"""Implementation of OAuth 2.0 using MSAL for authentication.

This module contains classes and functions that support authentication 
to Cortex using OAuth 2.0 and Microsoft Authentication Library (MSAL).
"""

import msal
import platform
import os
from pathlib import Path
from typing import Optional, Literal
from msal_extensions import FilePersistence, PersistedTokenCache
import time

class AuthMode:
    INTERACTIVE = "interactive"
    HEADLESS = "headless"

class PathController:
    """
    Determines and prepares a persistent cache path for auth tokens.

    - Windows: %APPDATA%\\Cortex\\Auth\\token_cache.bin
    - macOS:   ~/Library/Application Support/Cortex/Auth/token_cache.bin
    - Linux:   $XDG_DATA_HOME/Cortex/Auth/token_cache.bin (fallback: ~/.local/share/Cortex/Auth/token_cache.bin)

    You can override the filename if needed.
    """

    def __init__(self, filename: str = "token_cache.bin") -> None:
        system = platform.system()

        if system == "Windows":
            base = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming"))
            cache_dir = base / "Cortex" / "Auth"
        elif system == "Darwin":  # macOS
            cache_dir = Path.home() / "Library" / "Application Support" / "Cortex" / "Auth"
        else:  # Linux and everything else
            xdg_data_home = os.getenv("XDG_DATA_HOME")
            if xdg_data_home:
                base = Path(xdg_data_home)
            else:
                base = Path.home() / ".local" / "share"
            cache_dir = base / "Cortex" / "Auth"

        cache_dir.mkdir(parents=True, exist_ok=True)

        # Build the full path
        self.CACHE_DIR: Path = cache_dir
        self.CACHE_FILENAME: str = filename
        self.CACHE_FULL_PATH: Path = cache_dir / self.CACHE_FILENAME

    def ensure_path(self, path: str) -> Path:
        p = Path(path).expanduser()
        p = (p if p.is_absolute() else (Path.cwd() / p)).resolve()
        if not p.is_dir():
            raise ValueError("Must be a directory path. Filepaths are not supported")
        p.mkdir(parents=True, exist_ok=True)

    @property
    def msal_cache_directory(self) -> str:
        return str(self.CACHE_DIR)
    
    @property
    def msal_cache_filename(self) -> str:
        return self.CACHE_FILENAME

    @property
    def msal_cache_full_path(self) -> str:
        return str(self.CACHE_FULL_PATH)
    
class AuthProvider:
    def __init__(self, 
                 mode: Literal["interactive", "headless"],
                 client_id: str = "589b3bdf-97eb-46b8-b958-7e1746c9e678", 
                 tenant_id: str = "2bb5a4ff-858f-4409-93a6-f114d90bf0ab",
                 api_scopes: str = "api://c64dc5f6-c919-42ee-acae-b922588f5f84/access_as_user"):
        
        self.mode = mode
        self.path_controller = PathController()
        self.persistence = FilePersistence(self.path_controller.msal_cache_full_path)
        self.cache = PersistedTokenCache(persistence=self.persistence)
        self.client_id = client_id
        self.tenant_id = tenant_id

        self.app = msal.PublicClientApplication(
            client_id=client_id,
            authority=f"https://login.microsoftonline.com/{tenant_id}",
            token_cache=self.cache,
        )

        self.scopes = [api_scopes]
        self._result: Optional[dict] = None  # last token response
        self._skew = 300  # seconds of safety margin for expiry

        # Initial bootstrap
        if not self._acquire_token_silent():
            if mode == AuthMode.INTERACTIVE:
                self._acquire_token_interactive()
            elif mode == AuthMode.HEADLESS:
                self._acquire_token_device_code()
            else:
                raise ValueError(f"Invalid mode: {mode} | must be one of [{AuthMode.INTERACTIVE}, {AuthMode.HEADLESS}]")
        
    @property
    def access_token(self) -> Optional[str]:
        return self._result.get("access_token") if self._result else None
    
    @property
    def is_logged_in(self) -> bool:
        """
        True if we can obtain a valid access token from the cache without
        user interaction (MSAL will transparently use a refresh token if needed).
        """
        accounts = self.app.get_accounts()
        if not accounts:
            return False

        result = self.app.acquire_token_silent(self.scopes, account=accounts[0])
        if result and "access_token" in result:
            # keep your cached token up to date
            self._result = result
            return True

        return False

    def _token_expiring(self) -> bool:
        if not self._result:
            return True
        # MSAL returns 'expires_on' as epoch seconds (string or int)
        exp = int(self._result.get("expires_on", "0"))
        return time.time() >= (exp - self._skew)

    def get_access_token(self) -> str:
        """
        Call this right before any API call. It will:
          - Use the cached access token if still valid
          - Silently refresh via refresh token when expiring/expired
          - Fall back to interactive/device flow if silent fails
        """
        # Proactive refresh if token is near expiry
        if self._token_expiring():
            if not self._acquire_token_silent(force_refresh=True):
                # Silent failed (e.g., no RT, revoked, password change…)
                if self.mode == AuthMode.INTERACTIVE:
                    self._acquire_token_interactive()
                else:
                    self._acquire_token_device_code()

        if not self.access_token:
            raise RuntimeError("Failed to obtain an access token.")

        return self.access_token

    def _pick_account(self):
        accounts = self.app.get_accounts()
        return accounts[0] if accounts else None  # or pick by username/home_account_id

    def _acquire_token_silent(self, force_refresh: bool = False) -> bool:
        result = self.app.acquire_token_silent(self.scopes, account=self._pick_account(), force_refresh=force_refresh)
        if result and "access_token" in result:
            self._result = result
            return True
        return False

    def _acquire_token_interactive(self) -> bool:
        result = self.app.acquire_token_interactive(scopes=self.scopes)
        if result and "access_token" in result:
            self._result = result
            return True
        return False

    def _acquire_token_device_code(self) -> bool:
        flow = self.app.initiate_device_flow(scopes=self.scopes)
        if "user_code" not in flow:
            raise RuntimeError(flow.get("error_description", "Failed to start device flow"))
        print(flow["message"])
        result = self.app.acquire_token_by_device_flow(flow)
        if result and "access_token" in result:
            self._result = result
            return True
        return False
    
    def sign_out(self):
        """
        Signs out by removing cached tokens.
        """
        accounts = self.app.get_accounts()

        for acct in accounts:
            self.app.remove_account(acct)

        self._result = None

        try:
            os.remove(self.path_controller.msal_cache_full_path)
        except FileNotFoundError:
            pass

        if self.mode == AuthMode.INTERACTIVE:
            import webbrowser
            url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/logout"
            webbrowser.open(url)

