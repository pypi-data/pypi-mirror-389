# Copyright (c) 2025 Apala Cap. All rights reserved.
# This software is proprietary and confidential.

"""
Data models for Apala API client.

All models use Pydantic for type safety and validation.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


# API Response Types
class AuthResponse(BaseModel):
    """Authentication response from the server."""

    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    company_id: str
    company_name: str


class RefreshResponse(BaseModel):
    """Token refresh response from the server."""

    access_token: str
    expires_in: int


class CandidateMessageResponse(BaseModel):
    """Candidate message in processing response."""

    content: str
    channel: str
    message_id: str


class MessageProcessingResponse(BaseModel):
    """Message processing response from the server."""

    company: str
    customer_id: str
    candidate_message: CandidateMessageResponse


class MessageOptimizationResponse(BaseModel):
    """Message optimization response from the server."""

    message_id: str
    optimized_message: str
    recommended_channel: str
    original_message: str


class FeedbackResponse(BaseModel):
    """Feedback submission response from the server."""

    id: str
    message_id: str
    customer_responded: bool
    score: Literal["good", "bad", "neutral"]
    actual_sent_message: Optional[str] = None
    inserted_at: str


class FeedbackItemResponse(BaseModel):
    """Individual feedback item in bulk response."""

    id: str
    message_id: str
    customer_responded: bool
    score: Literal["good", "bad", "neutral"]
    actual_sent_message: Optional[str] = None
    inserted_at: str


class BulkFeedbackResponse(BaseModel):
    """Bulk feedback submission response from the server."""

    success: bool
    count: int
    feedback: List[FeedbackItemResponse]


class Message(BaseModel):
    """Represents a customer message."""

    content: str
    channel: str = Field(..., description="Channel type: SMS, EMAIL, or OTHER")
    message_id: Optional[str] = None
    send_timestamp: Optional[str] = None
    reply_or_not: bool = False

    @field_validator("channel")
    @classmethod
    def validate_channel(cls, v: str) -> str:
        """Validate channel is one of the allowed values."""
        valid_channels = {"SMS", "EMAIL", "OTHER"}
        if v not in valid_channels:
            raise ValueError(f"Channel must be one of: {valid_channels}")
        return v

    def model_post_init(self, __context: Any) -> None:
        """Generate message_id and timestamp if not provided."""
        if self.message_id is None:
            self.message_id = uuid.uuid4().hex
        if self.send_timestamp is None:
            self.send_timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API requests."""
        return {
            "content": self.content,
            "message_id": self.message_id,
            "channel": self.channel,
            "send_timestamp": self.send_timestamp,
            "reply_or_not": "true" if self.reply_or_not else "false",
        }


class MessageFeedback(BaseModel):
    """Represents feedback for a processed message."""

    message_id: str
    customer_responded: bool
    score: Literal["good", "bad", "neutral"] = Field(..., description="Quality rating: good, bad, or neutral")
    actual_sent_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API requests."""
        data = {
            "message_id": self.message_id,
            "customer_responded": self.customer_responded,
            "score": self.score,
        }
        if self.actual_sent_message is not None:
            data["actual_sent_message"] = self.actual_sent_message
        return data


class MessageHistory(BaseModel):
    """Represents a collection of customer messages and a candidate response."""

    messages: List[Message]
    candidate_message: Message
    customer_id: str = Field(..., description="Customer UUID")
    zip_code: str = Field(..., pattern=r"^\d{5}$", description="5-digit zip code")
    company_guid: str = Field(..., description="Company UUID")

    @field_validator("customer_id", "company_guid")
    @classmethod
    def validate_uuid(cls, v: str) -> str:
        """Validate UUID format."""
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError(f"Invalid UUID format: {v}")
        return v

    def to_processing_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for message processing API requests."""
        return {
            "company": self.company_guid,
            "customer_id": self.customer_id,
            "zip_code": self.zip_code,
            "messages": [msg.to_dict() for msg in self.messages],
            "candidate_message": self.candidate_message.to_dict(),
        }

    def to_optimization_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for message optimization API requests."""
        return {
            "company": self.company_guid,
            "customer_id": self.customer_id,
            "zip_code": self.zip_code,
            "messages": [msg.to_dict() for msg in self.messages],
            "candidate_message": self.candidate_message.content,  # Just content for optimization
        }
