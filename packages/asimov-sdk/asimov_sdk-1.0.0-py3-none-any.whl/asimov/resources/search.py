"""Search endpoint for Asimov SDK"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator

from ..core import APIClient


class SearchParams(BaseModel):
    """Parameters for search query"""

    query: str = Field(..., min_length=1, description="The search query string (required)")
    limit: Optional[int] = Field(
        None, ge=1, le=1000, description="Maximum number of results to return (default: 10, max: 1000)"
    )
    id: Optional[str] = Field(None, description="Filter results by document ID")
    params: Optional[Dict[str, Any]] = Field(None, description="Filter results by parameter key-value pairs")
    recall: Optional[int] = Field(
        None, ge=1, le=10000, description="Number of candidates for vector search (default: 100, max: 10000)"
    )

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()


class SearchResult(BaseModel):
    """Single search result"""

    content: str


class SearchResponse(BaseModel):
    """Response from search query"""

    success: bool
    results: List[SearchResult]
    count: int


class Search:
    """Search resource for querying content"""

    def __init__(self, client: APIClient):
        """
        Initialize search resource

        Args:
            client: API client instance
        """
        self.client = client

    def query(self, params: SearchParams) -> SearchResponse:
        """
        Perform a search query

        Args:
            params: Search parameters

        Returns:
            SearchResponse with results

        Raises:
            APIError: If the API request fails
            ValidationError: If parameters are invalid
        """
        # Pydantic validates automatically when creating the model
        validated_params = params.model_dump(exclude_none=True)

        response_data = self.client.post("/api/search", validated_params)
        return SearchResponse(**response_data)

