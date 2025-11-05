"""
Switchport Python SDK

A Python client library for Switchport - Prompt management and A/B testing platform.
"""

from .client import Switchport
from .exceptions import (
    SwitchportError,
    AuthenticationError,
    PromptNotFoundError,
    MetricNotFoundError,
    APIError,
)

__version__ = "0.4.1"
__all__ = [
    "Switchport",
    "SwitchportError",
    "AuthenticationError",
    "PromptNotFoundError",
    "MetricNotFoundError",
    "APIError",
]
