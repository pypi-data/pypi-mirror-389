"""Custom exceptions for Switchport SDK."""


class SwitchportError(Exception):
    """Base exception for all Switchport SDK errors."""
    pass


class AuthenticationError(SwitchportError):
    """Raised when API key authentication fails."""
    pass


class PromptNotFoundError(SwitchportError):
    """Raised when a prompt config with the given key is not found."""
    pass


class MetricNotFoundError(SwitchportError):
    """Raised when a metric with the given key is not found."""
    pass


class APIError(SwitchportError):
    """Raised when the Switchport API returns an error."""

    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data
