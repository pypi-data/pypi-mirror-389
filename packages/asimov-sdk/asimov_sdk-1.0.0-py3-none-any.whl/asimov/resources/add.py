"""Add endpoint for Asimov SDK"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator

from ..core import APIClient


class AddParams(BaseModel):
    """Parameters for adding content"""

    content: str = Field(
        ...,
        min_length=1,
        max_length=10000000,
        description="The content to add (required, max 10MB)",
    )
    params: Optional[Dict[str, Any]] = Field(None, description="Optional parameter key-value pairs for filtering")
    name: Optional[str] = Field(
        None, max_length=500, description="Optional document name (max 500 characters)"
    )

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Content cannot be empty")
        return v.strip()


class AddResponse(BaseModel):
    """Response from add operation"""

    success: bool


class Add:
    """Add resource for adding content to the index"""

    def __init__(self, client: APIClient):
        """
        Initialize add resource

        Args:
            client: API client instance
        """
        self.client = client

    def create(self, params: AddParams) -> AddResponse:
        """
        Add content to the index

        Args:
            params: Add parameters

        Returns:
            AddResponse indicating success

        Raises:
            APIError: If the API request fails
            ValidationError: If parameters are invalid
        """
        # Pydantic validates automatically when creating the model
        validated_params = params.model_dump(exclude_none=True)

        response_data = self.client.post("/api/add", validated_params)
        return AddResponse(**response_data)

