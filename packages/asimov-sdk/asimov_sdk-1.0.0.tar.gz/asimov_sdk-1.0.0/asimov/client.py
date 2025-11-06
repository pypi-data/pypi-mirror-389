"""Main Asimov SDK client"""

from typing import Optional

from .core import APIClient
from .resources.search import Search
from .resources.add import Add


class Asimov:
    """
    Asimov SDK Client

    Example:
        ```python
        from asimov import Asimov

        client = Asimov(api_key="your-api-key-here")

        # Search
        results = client.search.query(
            SearchParams(query="your search query", limit=10)
        )

        # Add content
        response = client.add.create(
            AddParams(content="Your content here", name="Document Name")
        )
        ```
    """

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        """
        Initialize the Asimov client

        Args:
            api_key: Your Asimov API key
            base_url: Base URL for the API (default: https://api.asimov.mov)
            timeout: Request timeout in seconds (default: 60)

        Raises:
            ValueError: If API key is not provided
        """
        if not api_key:
            raise ValueError("API key is required")

        self._client = APIClient(api_key=api_key, base_url=base_url, timeout=timeout)
        self.search = Search(self._client)
        self.add = Add(self._client)

