"""Type definitions for Switchport SDK."""

from typing import Any, Dict, Union, Optional
from pydantic import BaseModel, Field


# Subject can be either a dict or a string for subject identification
Subject = Union[Dict[str, Any], str]


class PromptResponse(BaseModel):
    """Response from executing a prompt."""

    text: str = Field(..., description="The generated prompt text from the LLM")
    model: str = Field(..., description="The model used (e.g., 'gpt-5', 'claude-3-5-sonnet-20241022', 'gemini-1.5-pro')")
    version_id: str = Field(..., description="UUID of the prompt version used")
    version_name: str = Field(..., description="Name of the version (e.g., 'v1', 'v2')")
    prompt_config_id: str = Field(..., description="UUID of the prompt config")
    request_id: str = Field(..., description="Unique request ID for tracking")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata (temperature, max_tokens, etc.)"
    )


class MetricRecordResponse(BaseModel):
    """Response from recording a metric."""

    success: bool = Field(..., description="Whether the metric was recorded successfully")
    metric_event_id: str = Field(..., description="UUID of the metric event")
