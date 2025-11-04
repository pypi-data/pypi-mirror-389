# Copyright (c) 2025 Apala Cap. All rights reserved.
# This software is proprietary and confidential.

"""
Main client for interacting with the Phoenix Message Analysis API.
"""

import time
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin

import requests

from .metadata import CustomerMetadata
from .models import (
    AuthResponse,
    BulkFeedbackResponse,
    FeedbackResponse,
    Message,
    MessageFeedback,
    MessageHistory,
    MessageOptimizationResponse,
    MessageProcessingResponse,
    RefreshResponse,
)


class ApalaClient:
    """
    Client for Phoenix Message Analysis Services.

    Provides authentication and methods for message processing and feedback.
    """

    def __init__(self, api_key: str, base_url: str = "http://localhost:4000"):
        """
        Initialize the client.

        Args:
            api_key: Your API key for authentication
            base_url: Base URL of the Phoenix server
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expires_at: Optional[float] = None
        self._session = requests.Session()

    def authenticate(self) -> AuthResponse:
        """
        Exchange API key for JWT tokens.

        Returns:
            Authentication response data

        Raises:
            requests.HTTPError: If authentication fails
            requests.RequestException: For network-related errors
        """
        url = urljoin(self.base_url, "/api/auth/token")
        payload = {"api_key": self.api_key}

        response = self._session.post(url, json=payload)
        response.raise_for_status()

        data = AuthResponse(**response.json())
        self.access_token = data.access_token
        self.refresh_token = data.refresh_token

        # Set expiration time (subtract 60 seconds for safety margin)
        self.token_expires_at = time.time() + data.expires_in - 60

        return data

    def refresh_access_token(self) -> RefreshResponse:
        """
        Refresh the access token using the refresh token.

        Returns:
            Refresh response data

        Raises:
            requests.HTTPError: If token refresh fails
            requests.RequestException: For network-related errors
        """
        if not self.refresh_token:
            raise ValueError("No refresh token available. Please authenticate first.")

        url = urljoin(self.base_url, "/api/auth/refresh")
        payload = {"refresh_token": self.refresh_token}

        response = self._session.post(url, json=payload)
        response.raise_for_status()

        data = RefreshResponse(**response.json())
        self.access_token = data.access_token

        # Update expiration time
        self.token_expires_at = time.time() + data.expires_in - 60

        return data

    def _ensure_valid_token(self) -> None:
        """Ensure we have a valid access token, refreshing if necessary."""
        current_time = time.time()

        if not self.access_token:
            self.authenticate()
        elif self.token_expires_at and current_time >= self.token_expires_at:
            try:
                self.refresh_access_token()
            except requests.RequestException:
                # If refresh fails, try full authentication
                self.authenticate()

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get headers with authentication token."""
        self._ensure_valid_token()
        return {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}

    def optimize_message(
        self,
        message_history: List[Message],
        candidate_message: Message,
        customer_id: str,
        zip_code: str,
        company_guid: str,
        metadata: Optional[CustomerMetadata] = None,
    ) -> MessageOptimizationResponse:
        """
        Optimize a message for maximum customer engagement.

        Args:
            message_history: List of customer messages
            candidate_message: The candidate message to optimize
            customer_id: Customer UUID
            zip_code: Customer's 5-digit zip code
            company_guid: Company UUID
            metadata: Optional customer metadata for enhanced personalization

        Returns:
            Optimization response with optimized_message and recommended_channel

        Raises:
            requests.HTTPError: If the request fails
            requests.RequestException: For network-related errors

        Example:
            >>> from apala_client import CustomerMetadata, CreditScoreBin, ApplicationReason
            >>> metadata = CustomerMetadata(
            ...     is_repeat_borrower=1,
            ...     credit_score_bin=CreditScoreBin.SCORE_650_700,
            ...     application_reason=ApplicationReason.HOME_IMPROVEMENT
            ... )
            >>> result = client.optimize_message(
            ...     message_history=messages,
            ...     candidate_message=candidate,
            ...     customer_id=customer_id,
            ...     zip_code="90210",
            ...     company_guid=company_guid,
            ...     metadata=metadata
            ... )
        """
        # Create MessageHistory object for validation
        history = MessageHistory(
            messages=message_history,
            candidate_message=candidate_message,
            customer_id=customer_id,
            zip_code=zip_code,
            company_guid=company_guid,
        )

        url = urljoin(self.base_url, "/api/message_optimizer")
        headers = self._get_auth_headers()
        payload = history.to_optimization_dict()

        # Add metadata if provided
        if metadata is not None:
            payload.update(metadata.to_dict())

        response = self._session.post(url, json=payload, headers=headers)
        response.raise_for_status()

        return MessageOptimizationResponse(**response.json())

        return self.submit_feedback_bulk(feedback_list)

    def submit_single_feedback(
        self,
        message_id: str,
        customer_responded: bool,
        score: str,
        actual_sent_message: Optional[str] = None
    ) -> FeedbackResponse:
        """
        Submit feedback for a single processed message.

        Args:
            message_id: The message UUID from optimization response
            customer_responded: Whether the customer responded
            score: Quality rating - must be one of: "good", "bad", "neutral"
            actual_sent_message: Optional - The actual message content sent to the customer.
                Useful if you modified the optimized message before sending.

        Returns:
            Feedback submission response

        Raises:
            requests.HTTPError: If the request fails
            requests.RequestException: For network-related errors

        Example:
            >>> result = client.submit_single_feedback(
            ...     message_id="770e8400-e29b-41d4-a716-446655440002",
            ...     customer_responded=True,
            ...     score="good",
            ...     actual_sent_message="Hi! Ready to help with your loan."
            ... )
        """
        # Validate using MessageFeedback model
        feedback = MessageFeedback(
            message_id=message_id,
            customer_responded=customer_responded,
            score=score,
            actual_sent_message=actual_sent_message
        )

        url = urljoin(self.base_url, "/api/feedback")
        headers = self._get_auth_headers()
        payload = feedback.to_dict()

        response = self._session.post(url, json=payload, headers=headers)
        response.raise_for_status()

        return FeedbackResponse(**response.json())

    def submit_feedback_bulk(self, feedback_list: List[Dict[str, any]]) -> BulkFeedbackResponse:
        """
        Submit feedback for multiple messages in bulk.

        Args:
            feedback_list: List of feedback dictionaries, each containing:
                - message_id: str - The message UUID
                - customer_responded: bool - Whether customer responded
                - score: str - Quality rating: "good", "bad", or "neutral"
                - actual_sent_message: str (optional) - The actual message content sent to customer

        Returns:
            Bulk feedback submission response with success status, count, and individual feedback items

        Raises:
            requests.HTTPError: If the request fails
            requests.RequestException: For network-related errors

        Example:
            >>> feedback_list = [
            ...     {
            ...         "message_id": "550e8400-e29b-41d4-a716-446655440000",
            ...         "customer_responded": True,
            ...         "score": "good",
            ...         "actual_sent_message": "Hi! Ready to help with your loan."
            ...     },
            ...     {
            ...         "message_id": "660e8400-e29b-41d4-a716-446655440001",
            ...         "customer_responded": False,
            ...         "score": "neutral"
            ...     }
            ... ]
            >>> response = client.submit_feedback_bulk(feedback_list)
            >>> print(f"Submitted {response.count} feedback items")
        """
        # Validate each feedback item using MessageFeedback model
        validated_feedback = []
        for feedback_data in feedback_list:
            feedback = MessageFeedback(**feedback_data)
            validated_feedback.append(feedback.to_dict())

        url = urljoin(self.base_url, "/api/feedback/bulk")
        headers = self._get_auth_headers()
        payload = {"feedback": validated_feedback}

        response = self._session.post(url, json=payload, headers=headers)
        response.raise_for_status()

        return BulkFeedbackResponse(**response.json())

    def close(self) -> None:
        """Close the HTTP session."""
        self._session.close()
