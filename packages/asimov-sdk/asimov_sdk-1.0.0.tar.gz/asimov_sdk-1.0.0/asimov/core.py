"""Core API client for Asimov SDK"""

from typing import Optional, Dict, Any
import requests
from requests.adapters import HTTPAdapter

try:
    from urllib3.util.retry import Retry
except ImportError:
    # Fallback for older urllib3 versions
    from urllib3.util import Retry


class APIError(Exception):
    """Exception raised for API-related errors"""

    def __init__(
        self,
        message: str,
        status: Optional[int] = None,
        code: Optional[str] = None,
        details: Optional[str] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status = status
        self.code = code
        self.details = details

    def __str__(self) -> str:
        if self.status:
            return f"APIError {self.status}: {self.message}"
        return f"APIError: {self.message}"


class APIClient:
    """HTTP client for making requests to the Asimov API"""

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        """
        Initialize the API client

        Args:
            api_key: Your Asimov API key
            base_url: Base URL for the API (default: https://api.asimov.mov)
            timeout: Request timeout in seconds (default: 60)
        """
        if not api_key:
            raise ValueError("API key is required")

        self.api_key = api_key
        self.base_url = base_url or "https://api.asimov.mov"
        self.timeout = timeout or 60

        # Create session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set default headers
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
        )

    def post(self, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a POST request

        Args:
            path: API endpoint path
            data: Request body data

        Returns:
            Response data as dictionary

        Raises:
            APIError: If the request fails
        """
        url = f"{self.base_url}{path}"

        try:
            response = self.session.post(url, json=data, timeout=self.timeout)
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            raise APIError(f"Network error: {str(e)}")

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a GET request

        Args:
            path: API endpoint path
            params: Query parameters

        Returns:
            Response data as dictionary

        Raises:
            APIError: If the request fails
        """
        url = f"{self.base_url}{path}"

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            raise APIError(f"Network error: {str(e)}")

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Handle API response and raise appropriate errors

        Args:
            response: Response object from requests

        Returns:
            Response data as dictionary

        Raises:
            APIError: If the response indicates an error
        """
        try:
            data = response.json()
        except ValueError:
            data = {"error": response.text or "Unknown error"}

        if not response.ok:
            error_message = data.get("error", "API request failed")
            error_details = data.get("details")
            error_code = data.get("code")

            raise APIError(
                message=error_message,
                status=response.status_code,
                code=error_code,
                details=error_details,
            )

        return data

