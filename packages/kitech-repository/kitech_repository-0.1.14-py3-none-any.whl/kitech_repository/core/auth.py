"""Authentication management for KITECH Repository."""

import json
from datetime import datetime

import keyring

from kitech_repository.core.config import Config

# Service name for keyring
SERVICE_NAME = "kitech-repository"
# Username for keyring (we only store one credential per service)
USERNAME = "api-key"


class AuthManager:
    """Manage authentication for KITECH Repository using system keyring."""

    def __init__(self, config: Config | None = None):
        """Initialize authentication manager."""
        self.config = config or Config.load()
        self.metadata_file = self.config.config_dir / "auth_metadata.json"

    def _save_metadata(self, metadata: dict) -> None:
        """Save metadata (non-sensitive info) to file."""
        self.config.config_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file.write_text(json.dumps(metadata, indent=2))

    def _load_metadata(self) -> dict:
        """Load metadata from file."""
        if self.metadata_file.exists():
            return json.loads(self.metadata_file.read_text())
        return {}

    def login(self, app_key: str, user_id: str = None, expires_at: str = None) -> bool:
        """Save authentication app key securely in system keyring."""
        if not app_key.startswith("kt_"):
            raise ValueError("Invalid app key format. App key should start with 'kt_'")

        try:
            # Store app key in system keyring (encrypted)
            keyring.set_password(SERVICE_NAME, USERNAME, app_key)

            # Store metadata (non-sensitive) in JSON file
            metadata = {
                "user_id": user_id,
                "created_at": datetime.now().isoformat(),
                "expires_at": expires_at,
            }
            self._save_metadata(metadata)

            return True
        except Exception as e:
            # Provide helpful error message based on the backend being used
            current_backend = keyring.get_keyring()
            backend_name = f"{current_backend.__class__.__module__}.{current_backend.__class__.__name__}"

            error_msg = f"Failed to store credentials in system keyring: {e}\n\n"

            if "fail" in backend_name.lower():
                error_msg += (
                    "❌ No keyring backend is available on your system.\n\n"
                    "To fix this on Linux:\n"
                    "  1. Install system keyring:\n"
                    "     Ubuntu/Debian: sudo apt-get install gnome-keyring python3-secretstorage\n"
                    "     Fedora/RHEL:   sudo dnf install gnome-keyring python3-secretstorage\n"
                    "     Arch Linux:    sudo pacman -S gnome-keyring python-secretstorage\n\n"
                    "  2. Or use encrypted file storage:\n"
                    "     pip install 'kitech-repository[alt-keyring]'\n"
                    "     export PYTHON_KEYRING_BACKEND=keyrings.alt.file.EncryptedKeyring\n\n"
                    "For more help, see: https://github.com/WIM-Corporation/kitech-repository-CLI#keyring-issues"
                )
            elif "prompt dismissed" in str(e).lower():
                error_msg += (
                    "❌ Keyring password prompt was dismissed.\n\n"
                    "This usually means gnome-keyring daemon is not running.\n"
                    "Try starting it:\n"
                    "  eval $(dbus-launch --sh-syntax)\n"
                    "  eval $(gnome-keyring-daemon --start --components=secrets)\n\n"
                    "Or use encrypted file storage instead:\n"
                    "  pip install 'kitech-repository[alt-keyring]'\n"
                    "  export PYTHON_KEYRING_BACKEND=keyrings.alt.file.EncryptedKeyring"
                )
            else:
                error_msg += f"Current backend: {backend_name}\n"
                error_msg += "Try using an alternative keyring backend if the issue persists."

            raise RuntimeError(error_msg) from e

    def logout(self) -> bool:
        """Remove authentication app key from system keyring."""
        try:
            # Try to delete from keyring
            try:
                keyring.delete_password(SERVICE_NAME, USERNAME)
            except keyring.errors.PasswordDeleteError:
                # Password doesn't exist, that's ok
                pass

            # Remove metadata file
            if self.metadata_file.exists():
                self.metadata_file.unlink()

            return True
        except Exception as e:
            raise RuntimeError(f"Failed to remove credentials: {e}") from e

    def get_app_key(self) -> str | None:
        """Get the stored authentication app key from system keyring."""
        try:
            return keyring.get_password(SERVICE_NAME, USERNAME)
        except Exception:
            return None

    def is_authenticated(self) -> bool:
        """Check if user is authenticated and app key is not expired."""
        # Check if key exists in keyring
        app_key = self.get_app_key()
        if not app_key:
            return False

        # Check expiry if available
        metadata = self._load_metadata()
        expires_at = metadata.get("expires_at")
        if expires_at:
            try:
                expiry = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                if datetime.now() > expiry:
                    return False
            except (ValueError, TypeError):
                # Invalid expiry format, ignore
                pass

        return True

    @property
    def headers(self) -> dict:
        """Get authentication headers for API requests."""
        app_key = self.get_app_key()
        if not app_key:
            raise ValueError("Not authenticated. Please login first.")

        return {
            "X-App-Key": app_key,
            "accept": "*/*",
        }
