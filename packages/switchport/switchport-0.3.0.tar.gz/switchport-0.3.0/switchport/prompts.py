"""Prompt execution client."""

from typing import Any, Dict, Optional
import requests

from .types import PromptResponse, Subject
from .exceptions import PromptNotFoundError, APIError


class PromptsClient:
    """Client for executing prompts via Switchport."""

    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def execute(
        self,
        prompt_key: str,
        subject: Optional[Subject] = None,
        variables: Optional[Dict[str, Any]] = None,
    ) -> PromptResponse:
        """
        Execute a prompt and get the LLM response.

        Args:
            prompt_key: The unique key of the prompt config
            subject: Subject identification for routing (dict or string)
            variables: Variables to substitute in the prompt template

        Returns:
            PromptResponse containing the generated text and metadata

        Raises:
            PromptNotFoundError: If the prompt config doesn't exist
            APIError: If the API request fails
        """
        url = f"{self.base_url}/api/sdk/v1/prompts/execute"

        payload = {
            "prompt_key": prompt_key,
            "subject": subject or {},
            "variables": variables or {},
        }

        try:
            response = requests.post(url, json=payload, headers=self.headers, timeout=30)

            if response.status_code == 404:
                raise PromptNotFoundError(
                    f"Prompt config with key '{prompt_key}' not found"
                )
            elif response.status_code == 401:
                from .exceptions import AuthenticationError

                raise AuthenticationError("Invalid API key")
            elif response.status_code != 200:
                raise APIError(
                    f"API request failed: {response.text}",
                    status_code=response.status_code,
                    response_data=response.json() if response.text else None,
                )

            data = response.json()
            return PromptResponse(**data)

        except requests.RequestException as e:
            raise APIError(f"Network error: {str(e)}")
