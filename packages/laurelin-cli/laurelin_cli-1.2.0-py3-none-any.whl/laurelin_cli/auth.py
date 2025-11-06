"""Authentication and token management for Laurelin CLI."""
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from .config import CREDENTIALS_FILE, CONFIG_FILE, DEFAULT_API_URL, PRODUCTION_API_URL


class AuthManager:
    """Manages authentication tokens and credentials."""

    def __init__(self):
        self.credentials_file = CREDENTIALS_FILE
        self.config_file = CONFIG_FILE

    def save_tokens(self, access_token: str, refresh_token: str) -> None:
        """Save authentication tokens to credentials file."""
        credentials = {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'saved_at': datetime.now().isoformat()
        }

        with open(self.credentials_file, 'w') as f:
            json.dump(credentials, f, indent=2)

        # Set file permissions to user-only read/write
        self.credentials_file.chmod(0o600)

    def load_tokens(self) -> Optional[Dict[str, str]]:
        """Load authentication tokens from credentials file."""
        if not self.credentials_file.exists():
            return None

        try:
            with open(self.credentials_file, 'r') as f:
                credentials = json.load(f)
            return credentials
        except (json.JSONDecodeError, IOError):
            return None

    def get_access_token(self) -> Optional[str]:
        """Get the current access token."""
        tokens = self.load_tokens()
        return tokens.get('access_token') if tokens else None

    def get_refresh_token(self) -> Optional[str]:
        """Get the current refresh token."""
        tokens = self.load_tokens()
        return tokens.get('refresh_token') if tokens else None

    def update_access_token(self, new_access_token: str) -> None:
        """Update only the access token (after refresh)."""
        tokens = self.load_tokens()
        if tokens:
            tokens['access_token'] = new_access_token
            tokens['refreshed_at'] = datetime.now().isoformat()

            with open(self.credentials_file, 'w') as f:
                json.dump(tokens, f, indent=2)

    def clear_tokens(self) -> None:
        """Clear all stored tokens."""
        if self.credentials_file.exists():
            self.credentials_file.unlink()

    def is_authenticated(self) -> bool:
        """Check if user has valid tokens stored."""
        return self.get_access_token() is not None

    def save_config(self, config: Dict[str, Any]) -> None:
        """Save CLI configuration."""
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)

    def load_config(self) -> Dict[str, Any]:
        """Load CLI configuration."""
        if not self.config_file.exists():
            # Default configuration
            return {
                'api_url': DEFAULT_API_URL,
                'use_production': False
            }

        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {'api_url': DEFAULT_API_URL, 'use_production': False}

    def get_api_url(self) -> str:
        """Get the configured API URL."""
        config = self.load_config()
        if config.get('use_production', False):
            return PRODUCTION_API_URL
        return config.get('api_url', DEFAULT_API_URL)

    def set_production_mode(self, enabled: bool = True) -> None:
        """Enable or disable production mode."""
        config = self.load_config()
        config['use_production'] = enabled
        self.save_config(config)
