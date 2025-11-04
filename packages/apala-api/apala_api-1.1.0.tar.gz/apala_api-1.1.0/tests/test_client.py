"""
Tests for the ApalaClient class.
"""

import time
from unittest.mock import Mock, patch

import pytest
import requests

from apala_client import ApalaClient


class TestApalaClientInit:
    """Test client initialization."""

    def test_client_init(self, api_key, base_url):
        """Test basic client initialization."""
        client = ApalaClient(api_key=api_key, base_url=base_url)

        assert client.api_key == api_key
        assert client.base_url == base_url
        assert client.access_token is None
        assert client.refresh_token is None
        assert client.token_expires_at is None

    def test_client_init_strips_trailing_slash(self, api_key):
        """Test that trailing slash is stripped from base URL."""
        client = ApalaClient(api_key=api_key, base_url="http://localhost:4000/")
        assert client.base_url == "http://localhost:4000"


class TestAuthentication:
    """Test authentication methods."""

    @patch("requests.Session.post")
    def test_authenticate_success(self, mock_post, client, mock_auth_response):
        """Test successful authentication."""
        mock_response = Mock()
        mock_response.json.return_value = mock_auth_response
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = client.authenticate()

        # Compare Pydantic model attributes instead of equality
        assert result.access_token == mock_auth_response["access_token"]
        assert result.refresh_token == mock_auth_response["refresh_token"]
        assert result.token_type == mock_auth_response["token_type"]
        assert result.expires_in == mock_auth_response["expires_in"]
        assert result.company_id == mock_auth_response["company_id"]
        assert result.company_name == mock_auth_response["company_name"]

        assert client.access_token == "mock-access-token"
        assert client.refresh_token == "mock-refresh-token"
        assert client.token_expires_at is not None

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "/api/auth/token" in call_args[0][0]
        assert call_args[1]["json"] == {"api_key": client.api_key}

    @patch("requests.Session.post")
    def test_authenticate_http_error(self, mock_post, client):
        """Test authentication HTTP error handling."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("401 Unauthorized")
        mock_post.return_value = mock_response

        with pytest.raises(requests.HTTPError):
            client.authenticate()

    @patch("requests.Session.post")
    def test_refresh_token_success(self, mock_post, client):
        """Test successful token refresh."""
        # Set up initial state
        client.refresh_token = "mock-refresh-token"

        mock_response = Mock()
        refresh_response = {"access_token": "new-access-token", "expires_in": 3600}
        mock_response.json.return_value = refresh_response
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = client.refresh_access_token()

        # Compare Pydantic model attributes
        assert result.access_token == refresh_response["access_token"]
        assert result.expires_in == refresh_response["expires_in"]
        assert client.access_token == "new-access-token"
        assert client.token_expires_at is not None

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "/api/auth/refresh" in call_args[0][0]
        assert call_args[1]["json"] == {"refresh_token": "mock-refresh-token"}

    def test_refresh_token_no_refresh_token(self, client):
        """Test refresh token without having a refresh token."""
        with pytest.raises(ValueError, match="No refresh token available"):
            client.refresh_access_token()

    @patch("requests.Session.post")
    def test_ensure_valid_token_authenticate(self, mock_post, client, mock_auth_response):
        """Test _ensure_valid_token when no token exists."""
        mock_response = Mock()
        mock_response.json.return_value = mock_auth_response
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        client._ensure_valid_token()

        assert client.access_token == "mock-access-token"
        mock_post.assert_called_once()

    @patch("requests.Session.post")
    def test_ensure_valid_token_refresh(self, mock_post, client):
        """Test _ensure_valid_token when token is expired."""
        # Set up expired token
        client.access_token = "old-token"
        client.refresh_token = "refresh-token"
        client.token_expires_at = time.time() - 100  # Expired

        mock_response = Mock()
        refresh_response = {"access_token": "new-token", "expires_in": 3600}
        mock_response.json.return_value = refresh_response
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        client._ensure_valid_token()

        assert client.access_token == "new-token"
        mock_post.assert_called_once()

    def test_get_auth_headers(self, authenticated_client):
        """Test getting authentication headers."""
        headers = authenticated_client._get_auth_headers()

        expected_headers = {
            "Authorization": "Bearer mock-access-token",
            "Content-Type": "application/json",
        }
        assert headers == expected_headers


class TestMessageProcessing:
    """Test message processing methods."""

    @patch("requests.Session.post")
    def test_optimize_message_success(
        self,
        mock_post,
        authenticated_client,
        sample_messages,
        candidate_message,
        customer_id,
        zip_code,
        company_guid,
        mock_optimization_response,
    ):
        """Test successful message optimization."""
        mock_response = Mock()
        mock_response.json.return_value = mock_optimization_response
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = authenticated_client.optimize_message(
            message_history=sample_messages,
            candidate_message=candidate_message,
            customer_id=customer_id,
            zip_code=zip_code,
            company_guid=company_guid,
        )

        # Compare Pydantic model attributes
        assert result.message_id == mock_optimization_response["message_id"]
        assert result.optimized_message == mock_optimization_response["optimized_message"]
        assert result.recommended_channel == mock_optimization_response["recommended_channel"]
        assert result.original_message == mock_optimization_response["original_message"]

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "/api/message_optimizer" in call_args[0][0]


class TestFeedback:
    """Test feedback submission methods."""

    @patch("requests.Session.post")
    def test_submit_single_feedback_success(
        self, mock_post, authenticated_client
    ):
        """Test successful single feedback submission."""
        # Mock new feedback response format
        mock_feedback_response = {
            "id": "feedback-uuid-1",
            "message_id": "msg-uuid-1",
            "customer_responded": True,
            "score": "good",
            "actual_sent_message": "Hi! Ready to help with your loan.",
            "inserted_at": "2024-01-15T10:30:00Z"
        }

        mock_response = Mock()
        mock_response.json.return_value = mock_feedback_response
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = authenticated_client.submit_single_feedback(
            message_id="msg-uuid-1",
            customer_responded=True,
            score="good",
            actual_sent_message="Hi! Ready to help with your loan."
        )

        # Compare Pydantic model attributes
        assert result.id == mock_feedback_response["id"]
        assert result.message_id == mock_feedback_response["message_id"]
        assert result.customer_responded == mock_feedback_response["customer_responded"]
        assert result.score == mock_feedback_response["score"]
        assert result.actual_sent_message == mock_feedback_response["actual_sent_message"]
        assert result.inserted_at == mock_feedback_response["inserted_at"]

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "/api/feedback" in call_args[0][0]
        assert call_args[1]["json"] == {
            "message_id": "msg-uuid-1",
            "customer_responded": True,
            "score": "good",
            "actual_sent_message": "Hi! Ready to help with your loan."
        }

    @patch("requests.Session.post")
    def test_submit_feedback_bulk_success(
        self, mock_post, authenticated_client
    ):
        """Test successful bulk feedback submission."""
        # Mock bulk feedback response
        mock_bulk_response = {
            "success": True,
            "count": 3,
            "feedback": [
                {
                    "id": "feedback-id-1",
                    "message_id": "msg-id-1",
                    "customer_responded": True,
                    "score": "good",
                    "actual_sent_message": "Hi! Ready to help with your loan.",
                    "inserted_at": "2024-01-15T10:30:00Z"
                },
                {
                    "id": "feedback-id-2",
                    "message_id": "msg-id-2",
                    "customer_responded": False,
                    "score": "neutral",
                    "actual_sent_message": "Thanks for reaching out about your account",
                    "inserted_at": "2024-01-15T10:30:00Z"
                },
                {
                    "id": "feedback-id-3",
                    "message_id": "msg-id-3",
                    "customer_responded": True,
                    "score": "good",
                    "actual_sent_message": None,
                    "inserted_at": "2024-01-15T10:30:00Z"
                }
            ]
        }

        mock_response = Mock()
        mock_response.json.return_value = mock_bulk_response
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Create feedback list
        feedback_list = [
            {"message_id": "msg-id-1", "customer_responded": True, "score": "good", "actual_sent_message": "Hi! Ready to help with your loan."},
            {"message_id": "msg-id-2", "customer_responded": False, "score": "neutral", "actual_sent_message": "Thanks for reaching out about your account"},
            {"message_id": "msg-id-3", "customer_responded": True, "score": "good"}
        ]

        result = authenticated_client.submit_feedback_bulk(feedback_list)

        # Compare Pydantic model attributes
        assert result.success == mock_bulk_response["success"]
        assert result.count == mock_bulk_response["count"]
        assert len(result.feedback) == 3
        # Check first feedback item
        assert result.feedback[0].id == mock_bulk_response["feedback"][0]["id"]
        assert result.feedback[0].message_id == mock_bulk_response["feedback"][0]["message_id"]
        assert result.feedback[0].actual_sent_message == mock_bulk_response["feedback"][0]["actual_sent_message"]
        # Check third feedback item (with None actual_sent_message)
        assert result.feedback[2].actual_sent_message is None

        # Verify API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "/api/feedback/bulk" in call_args[0][0]
        assert call_args[1]["json"] == {"feedback": feedback_list}

        # Verify headers include Bearer token (JWT authentication)
        headers = call_args[1]["headers"]
        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Bearer ")


class TestClientLifecycle:
    """Test client lifecycle methods."""

    def test_close(self, client):
        """Test client close method."""
        mock_session = Mock()
        client._session = mock_session

        client.close()

        mock_session.close.assert_called_once()
