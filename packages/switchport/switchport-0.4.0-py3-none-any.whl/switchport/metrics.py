"""Metrics recording client."""

from typing import Any, Optional, Union
import requests
from datetime import datetime

from .types import MetricRecordResponse, Subject
from .exceptions import MetricNotFoundError, APIError


class MetricsClient:
    """Client for recording metrics via Switchport."""

    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def record(
        self,
        metric_key: str,
        value: Union[float, int, bool, str],
        subject: Optional[Subject] = None,
        timestamp: Optional[datetime] = None,
    ) -> MetricRecordResponse:
        """
        Record a metric value.

        Args:
            metric_key: The unique key of the metric definition
            value: The metric value (float, int, bool, or string for enum)
            subject: Subject identification for aggregation (dict or string)
            timestamp: Optional timestamp (defaults to now)

        Returns:
            MetricRecordResponse with success status and event ID

        Raises:
            MetricNotFoundError: If the metric definition doesn't exist
            APIError: If the API request fails
        """
        url = f"{self.base_url}/api/sdk/v1/metrics/record"

        payload = {
            "metric_key": metric_key,
            "value": value,
            "subject": subject or {},
            "timestamp": timestamp.isoformat() if timestamp else None,
        }

        try:
            response = requests.post(url, json=payload, headers=self.headers, timeout=10)

            if response.status_code == 404:
                raise MetricNotFoundError(
                    f"Metric definition with key '{metric_key}' not found"
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
            return MetricRecordResponse(**data)

        except requests.RequestException as e:
            raise APIError(f"Network error: {str(e)}")
