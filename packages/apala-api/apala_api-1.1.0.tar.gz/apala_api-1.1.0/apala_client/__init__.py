# Copyright (c) 2025 Apala Cap. All rights reserved.
# This software is proprietary and confidential.

"""
Apala API - Python SDK for Phoenix Message Analysis Services

A Python SDK that provides a clean interface to interact with the Phoenix-based
message analysis services for loan/financial AI applications.
"""

from .client import ApalaClient
from .metadata import (
    AgeBin,
    ApplicationReason,
    CreditScoreBin,
    CustomerMetadata,
    LoanAmountBin,
    MonthlyIncomeBin,
)
from .models import (
    AuthResponse,
    BulkFeedbackResponse,
    CandidateMessageResponse,
    FeedbackItemResponse,
    FeedbackResponse,
    Message,
    MessageFeedback,
    MessageHistory,
    MessageOptimizationResponse,
    MessageProcessingResponse,
    RefreshResponse,
)

__version__ = "0.1.0"
__all__ = [
    # Client
    "ApalaClient",
    # Request Models
    "Message",
    "MessageFeedback",
    "MessageHistory",
    # Response Models
    "AuthResponse",
    "RefreshResponse",
    "MessageProcessingResponse",
    "MessageOptimizationResponse",
    "FeedbackResponse",
    "BulkFeedbackResponse",
    "FeedbackItemResponse",
    "CandidateMessageResponse",
    # Metadata
    "CustomerMetadata",
    "CreditScoreBin",
    "LoanAmountBin",
    "AgeBin",
    "MonthlyIncomeBin",
    "ApplicationReason",
]
