"""Main Switchport client."""

import os
from typing import Optional

from .prompts import PromptsClient
from .metrics import MetricsClient


class Switchport:
    """
    Main Switchport SDK client.

    Example:
        >>> from switchport import Switchport
        >>> client = Switchport(api_key="sp_xxx")
        >>> response = client.prompts.execute("welcome-message", variables={"name": "Alice"})
        >>> print(response.text)
    """

    # Production URL - hardcoded, can be overridden via env var for testing
    DEFAULT_BASE_URL = "https://switchport-api.vercel.app"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Switchport client.

        Args:
            api_key: Switchport API key (starts with 'sp_').
                     If not provided, reads from SWITCHPORT_API_KEY environment variable.

        Raises:
            ValueError: If no API key is provided or found in environment
        """
        # Get API key from parameter or environment
        self.api_key = api_key or os.getenv("SWITCHPORT_API_KEY")

        if not self.api_key:
            raise ValueError(
                "API key is required. Provide it as a parameter or set SWITCHPORT_API_KEY environment variable."
            )

        if not self.api_key.startswith("sp_"):
            raise ValueError("Invalid API key format. Switchport API keys start with 'sp_'")

        # Allow base URL override for development/testing
        self.base_url = os.getenv("SWITCHPORT_API_URL", self.DEFAULT_BASE_URL)

        # Initialize sub-clients
        self.prompts = PromptsClient(self.api_key, self.base_url)
        self.metrics = MetricsClient(self.api_key, self.base_url)
