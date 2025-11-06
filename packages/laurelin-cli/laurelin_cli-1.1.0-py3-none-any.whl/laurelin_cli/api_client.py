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

    # ==========================================================================
    # NIMROD SIMULATION METHODS
    # ==========================================================================

    def create_nimrod_simulation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new NIMROD simulation."""
        return self._make_request('POST', '/nimrod/simulations', json=params)

    def list_nimrod_simulations(self, limit: Optional[int] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List NIMROD simulations for the current user."""
        params = {}
        if limit:
            params['limit'] = limit
        if status:
            params['status'] = status

        response = self._make_request('GET', '/nimrod/simulations', params=params)
        if response.get('success'):
            return response.get('data', [])
        return []

    def get_nimrod_status(self, simulation_id: str) -> Dict[str, Any]:
        """Get status of a NIMROD simulation."""
        return self._make_request('GET', f'/nimrod/simulations/{simulation_id}')

    def cancel_nimrod_simulation(self, simulation_id: str) -> Dict[str, Any]:
        """Cancel a running NIMROD simulation."""
        return self._make_request('DELETE', f'/nimrod/simulations/{simulation_id}')

    def get_nimrod_results(self, simulation_id: str) -> Dict[str, Any]:
        """Get results from a completed NIMROD simulation."""
        return self._make_request('GET', f'/nimrod/simulations/{simulation_id}/results')

    def estimate_nimrod_cost(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate cost for a NIMROD simulation."""
        return self._make_request('POST', '/nimrod/estimate-cost', json=params)

    # ==========================================================================
    # NIMROD ANALYSIS METHODS (nimpy)
    # ==========================================================================

    def list_nimrod_analyses(self, simulation_id: str) -> Dict[str, Any]:
        """List available analyses for a NIMROD simulation."""
        return self._make_request('GET', f'/nimrod/simulations/{simulation_id}/analyses')

    def analyze_nimrod_field(self, simulation_id: str, field_name: str, time_step: Optional[int] = None) -> Dict[str, Any]:
        """Analyze a specific field from NIMROD simulation results."""
        data = {'field_name': field_name}
        if time_step is not None:
            data['time_step'] = time_step

        return self._make_request('POST', f'/nimrod/simulations/{simulation_id}/analyze/field', json=data)

    def analyze_nimrod_equilibrium(self, simulation_id: str) -> Dict[str, Any]:
        """Compute equilibrium quantities for NIMROD simulation."""
        return self._make_request('POST', f'/nimrod/simulations/{simulation_id}/analyze/equilibrium')

    def compute_nimrod_growth_rate(self, simulation_id: str) -> Dict[str, Any]:
        """Compute growth rate and frequency from NIMROD simulation time series."""
        return self._make_request('POST', f'/nimrod/simulations/{simulation_id}/analyze/growth-rate')

    def compute_nimrod_fsa(self, simulation_id: str, field_name: str) -> Dict[str, Any]:
        """Compute flux-surface averaged quantities for NIMROD simulation."""
        data = {'field_name': field_name}
        return self._make_request('POST', f'/nimrod/simulations/{simulation_id}/analyze/flux-surface-average', json=data)

    def generate_nimrod_visualization(self, simulation_id: str, field_name: str, plot_type: str = 'contour', time_step: Optional[int] = None) -> Dict[str, Any]:
        """Generate visualization plot of NIMROD simulation data."""
        data = {
            'field_name': field_name,
            'plot_type': plot_type
        }
        if time_step is not None:
            data['time_step'] = time_step

        return self._make_request('POST', f'/nimrod/simulations/{simulation_id}/visualize', json=data)

    # ==========================================================================
    # STORAGE METHODS
    # ==========================================================================

    def get(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Generic GET request."""
        return self._make_request('GET', endpoint, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Generic DELETE request."""
        return self._make_request('DELETE', endpoint, **kwargs)

    def download_file(self, url: str, output_path: str, chunk_size: int = 8192) -> bool:
        """
        Download a file from a URL with progress bar.

        Args:
            url: URL to download from (typically a signed GCS URL)
            output_path: Local path to save the file
            chunk_size: Size of chunks to download (default: 8KB)

        Returns:
            True if download successful, False otherwise
        """
        try:
            import click

            # Make request with streaming enabled
            response = self.session.get(url, stream=True)
            response.raise_for_status()

            # Get file size from headers
            total_size = int(response.headers.get('content-length', 0))

            # Download with progress bar
            with open(output_path, 'wb') as f:
                if total_size == 0:
                    # No content length header, download without progress
                    f.write(response.content)
                    return True

                with click.progressbar(length=total_size,
                                     label='Downloading',
                                     fill_char='█',
                                     empty_char='░') as bar:
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)
                            bar.update(len(chunk))

            return True

        except Exception as e:
            print(f"Download error: {str(e)}")
            return False
