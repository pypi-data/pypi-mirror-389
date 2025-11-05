"""API client for Laurelin backend communication."""
import requests
from typing import Optional, Dict, Any, List
from .auth import AuthManager
from .config import CLI_TOKEN_HEADER


class APIClient:
    """Client for communicating with Laurelin backend API."""

    def __init__(self, auth_manager: Optional[AuthManager] = None):
        self.auth_manager = auth_manager or AuthManager()
        self.base_url = self.auth_manager.get_api_url()
        self.session = requests.Session()

    def _get_headers(self) -> Dict[str, str]:
        """Get headers with authentication token."""
        headers = {
            'Content-Type': 'application/json'
        }

        access_token = self.auth_manager.get_access_token()
        if access_token:
            headers[CLI_TOKEN_HEADER] = access_token

        return headers

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle API response and check for errors."""
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                # Token expired, try to refresh
                if self._refresh_token():
                    # Retry the request with new token
                    return None  # Signal to retry
                else:
                    raise Exception("Authentication failed. Please run 'laurelin login' again.")
            elif response.status_code == 403:
                raise Exception("Access denied. You may need a paid subscription or be in a restricted location.")
            else:
                try:
                    error_data = response.json()
                    raise Exception(error_data.get('message', str(e)))
                except:
                    raise Exception(f"API error: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {str(e)}")

    def _refresh_token(self) -> bool:
        """Refresh the access token using refresh token."""
        refresh_token = self.auth_manager.get_refresh_token()
        if not refresh_token:
            return False

        try:
            response = self.session.post(
                f"{self.base_url}/cli-tokens/refresh",
                json={'refresh_token': refresh_token},
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    new_access_token = data.get('access_token')
                    self.auth_manager.update_access_token(new_access_token)
                    return True

            return False
        except Exception:
            return False

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make an API request with automatic retry on token refresh."""
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()

        response = self.session.request(method, url, headers=headers, **kwargs)
        result = self._handle_response(response)

        # If result is None, token was refreshed - retry once
        if result is None:
            headers = self._get_headers()
            response = self.session.request(method, url, headers=headers, **kwargs)
            result = self._handle_response(response)

        return result

    def test_connection(self) -> bool:
        """Test connection to API."""
        try:
            response = self.session.get(f"{self.base_url.rsplit('/api', 1)[0]}/health", timeout=5)
            return response.status_code == 200
        except:
            return False

    def send_message(self, message: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Send a chat message to the API."""
        if not session_id:
            # Create a new session
            session_response = self._make_request('POST', '/chat/sessions', json={
                'title': 'CLI Chat'
            })

            if not session_response.get('success'):
                raise Exception("Failed to create chat session")

            session_id = session_response.get('data', {}).get('session_id')

        # Send the message
        response = self._make_request(
            'POST',
            f'/chat/sessions/{session_id}/messages',
            json={'message': message}
        )

        return response

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all chat sessions."""
        response = self._make_request('GET', '/chat/sessions')
        if response.get('success'):
            return response.get('data', [])
        return []

    def get_session(self, session_id: str) -> Dict[str, Any]:
        """Get a specific chat session."""
        response = self._make_request('GET', f'/chat/sessions/{session_id}')
        return response.get('data', {})

    def list_cli_tokens(self) -> List[Dict[str, Any]]:
        """List all CLI tokens for the user."""
        response = self._make_request('GET', '/cli-tokens')
        if response.get('success'):
            return response.get('tokens', [])
        return []

    def revoke_cli_token(self, token_id: str) -> bool:
        """Revoke a CLI token."""
        response = self._make_request('DELETE', f'/cli-tokens/{token_id}')
        return response.get('success', False)
