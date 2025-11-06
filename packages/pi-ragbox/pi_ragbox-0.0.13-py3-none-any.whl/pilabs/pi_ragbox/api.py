"""API client for pi-ragbox."""

from typing import Any, Dict, List, Optional

import httpx

from .config import get_base_url, load_credentials


class APIError(Exception):
    """Base exception for API errors."""

    pass


class AuthenticationError(APIError):
    """Raised when authentication fails."""

    pass


class APIClient:
    """Client for interacting with the pi-ragbox API."""

    def __init__(
        self, cookies: Optional[Dict[str, str]] = None, base_url: Optional[str] = None
    ):
        """Initialize the API client.

        Args:
            cookies: Optional session cookies. If not provided, will try to load from config.
            base_url: Optional base URL. If not provided, will use default.
        """
        self.base_url = base_url or get_base_url()
        self.cookies = cookies or self._load_cookies()

    def _load_cookies(self) -> Optional[Dict[str, str]]:
        """Load cookies from stored credentials."""
        creds = load_credentials()
        return creds.get("cookies") if creds else None

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests.

        Returns:
            Dictionary of headers
        """
        headers = {
            "Content-Type": "application/json",
        }
        return headers

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        """Make an HTTP request to the API.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: API path (will be appended to base_url)
            **kwargs: Additional arguments to pass to httpx

        Returns:
            The response object

        Raises:
            AuthenticationError: If authentication fails
            APIError: For other API errors
        """
        url = f"{self.base_url}{path}"
        headers = self._get_headers()

        try:
            with httpx.Client(cookies=self.cookies) as client:
                response = client.request(
                    method, url, headers=headers, timeout=30.0, **kwargs
                )

                if response.status_code == 401:
                    raise AuthenticationError(
                        "Authentication failed. Please run 'pi-ragbox login' to authenticate."
                    )

                if response.status_code >= 400:
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("error", response.text)
                    except:
                        error_msg = response.text

                    raise APIError(
                        f"API request failed with status {response.status_code}: {error_msg}"
                    )

                return response

        except httpx.RequestError as e:
            raise APIError(f"Request failed: {str(e)}")

    def get_projects(self) -> List[Dict[str, Any]]:
        """Get list of projects for the authenticated user.

        Returns:
            List of project dictionaries

        Raises:
            AuthenticationError: If not authenticated
            APIError: If the request fails
        """
        if not self.cookies:
            raise AuthenticationError(
                "Not authenticated. Please run 'pi-ragbox login' first."
            )

        response = self._request("GET", "/api/projects")
        return response.json()
