"""
Integration tests for the Apala API client.

These tests require a running Phoenix server and valid API credentials.
Use environment variables to configure test settings.
"""

import os
import uuid

import pytest

from apala_client import ApalaClient
from apala_client.models import Message, MessageFeedback

# Skip integration tests if not explicitly enabled
pytestmark = pytest.mark.skipif(
    not os.getenv("RUN_INTEGRATION_TESTS"),
    reason="Integration tests disabled. Set RUN_INTEGRATION_TESTS=1 to enable.",
)


@pytest.fixture
def integration_client():
    """Client configured for integration testing."""
    api_key = os.getenv("APALA_API_KEY")
    base_url = os.getenv("APALA_BASE_URL", "http://localhost:4000")

    if not api_key:
        pytest.skip("APALA_API_KEY environment variable not set")

    return ApalaClient(api_key=api_key, base_url=base_url)


@pytest.fixture
def test_company_guid():
    """Company GUID for testing."""
    guid = os.getenv("APALA_COMPANY_GUID")
    if not guid:
        pytest.skip("APALA_COMPANY_GUID environment variable not set")
    return guid


@pytest.fixture
def test_data():
    """Test data for integration tests."""
    return {
        "customer_id": str(uuid.uuid4()),
        "zip_code": "90210",
        "messages": [
            Message(
                content="Hi, I'm interested in your loan products.",
                channel="EMAIL",
                reply_or_not=False,
            ),
            Message(
                content="What are your current interest rates?", channel="EMAIL", reply_or_not=False
            ),
        ],
        "candidate_message": Message(
            content="Thank you for your interest! Our current rates start at 3.5% APR. Would you like to schedule a consultation?",
            channel="EMAIL",
        ),
    }


class TestIntegrationAuthentication:
    """Integration tests for authentication."""

    def test_authenticate_with_real_api(self, integration_client):
        """Test authentication with real API."""
        response = integration_client.authenticate()

        assert "access_token" in response
        assert "refresh_token" in response
        assert "expires_in" in response
        assert integration_client.access_token is not None
        assert integration_client.refresh_token is not None

    def test_token_refresh(self, integration_client):
        """Test token refresh functionality."""
        # First authenticate
        integration_client.authenticate()
        original_token = integration_client.access_token

        # Force refresh
        refresh_response = integration_client.refresh_access_token()

        assert "access_token" in refresh_response
        assert integration_client.access_token != original_token


class TestIntegrationMessageProcessing:
    """Integration tests for message processing."""

    def test_message_processing_flow(self, integration_client, test_company_guid, test_data):
        """Test the complete message processing flow."""
        # Authenticate first
        integration_client.authenticate()

        # Process messages
        response = integration_client.message_process(
            message_history=test_data["messages"],
            candidate_message=test_data["candidate_message"],
            customer_id=test_data["customer_id"],
            zip_code=test_data["zip_code"],
            company_guid=test_company_guid,
        )

        assert "company" in response
        assert "customer_id" in response
        assert "candidate_message" in response
        assert response["company"] == test_company_guid
        assert response["customer_id"] == test_data["customer_id"]

    def test_message_optimization(self, integration_client, test_company_guid, test_data):
        """Test message optimization."""
        # Authenticate first
        integration_client.authenticate()

        # Optimize message
        response = integration_client.optimize_message(
            message_history=test_data["messages"],
            candidate_message=test_data["candidate_message"],
            customer_id=test_data["customer_id"],
            zip_code=test_data["zip_code"],
            company_guid=test_company_guid,
        )

        assert "optimized_message" in response
        assert "recommended_channel" in response
        assert isinstance(response["optimized_message"], str)
        assert response["recommended_channel"] in ["SMS", "EMAIL", "OTHER"]


class TestIntegrationFeedback:
    """Integration tests for feedback submission."""

    def test_feedback_submission(self, integration_client, test_company_guid, test_data):
        """Test feedback submission after message processing."""
        # Authenticate first
        integration_client.authenticate()

        # Process messages first to get a valid message ID
        process_response = integration_client.message_process(
            message_history=test_data["messages"],
            candidate_message=test_data["candidate_message"],
            customer_id=test_data["customer_id"],
            zip_code=test_data["zip_code"],
            company_guid=test_company_guid,
        )

        # Submit feedback
        feedback_response = integration_client.submit_single_feedback(
            message_id=process_response["candidate_message"]["message_id"],
            customer_responded=True,
            score="good",
            actual_sent_message=process_response["candidate_message"]["content"],
        )

        assert "success" in feedback_response or "message" in feedback_response
        # Response format may vary, but should indicate successful submission


class TestIntegrationEndToEnd:
    """End-to-end integration tests."""

    def test_complete_workflow(self, integration_client, test_company_guid, test_data):
        """Test the complete workflow from authentication to feedback."""
        # Step 1: Authenticate
        auth_response = integration_client.authenticate()
        assert "access_token" in auth_response

        # Step 2: Process messages
        process_response = integration_client.message_process(
            message_history=test_data["messages"],
            candidate_message=test_data["candidate_message"],
            customer_id=test_data["customer_id"],
            zip_code=test_data["zip_code"],
            company_guid=test_company_guid,
        )
        assert "candidate_message" in process_response

        # Step 3: Optimize message
        optimize_response = integration_client.optimize_message(
            message_history=test_data["messages"],
            candidate_message=test_data["candidate_message"],
            customer_id=test_data["customer_id"],
            zip_code=test_data["zip_code"],
            company_guid=test_company_guid,
        )
        assert "optimized_message" in optimize_response

        # Step 4: Submit feedback
        feedback_response = integration_client.submit_single_feedback(
            message_id=process_response["candidate_message"]["message_id"],
            customer_responded=True,
            score="good",
            actual_sent_message=optimize_response["optimized_message"],
        )

        # Verify the complete workflow succeeded
        assert auth_response["access_token"] == integration_client.access_token
        assert process_response["company"] == test_company_guid
        assert len(optimize_response["optimized_message"]) > 0
        assert "success" in feedback_response or "message" in feedback_response


class TestIntegrationErrorHandling:
    """Integration tests for error scenarios."""

    def test_invalid_api_key(self):
        """Test behavior with invalid API key."""
        client = ApalaClient(
            api_key="invalid-key", base_url=os.getenv("APALA_BASE_URL", "http://localhost:4000")
        )

        with pytest.raises(Exception):  # Should raise HTTPError or similar
            client.authenticate()

    def test_invalid_data_validation(self, integration_client, test_company_guid):
        """Test server-side validation with invalid data."""
        integration_client.authenticate()

        invalid_message = Message(content="", channel="INVALID_CHANNEL")

        with pytest.raises(Exception):  # Should raise HTTPError or similar
            integration_client.message_process(
                message_history=[invalid_message],
                candidate_message=invalid_message,
                customer_id="invalid-uuid",
                zip_code="123",  # Invalid zip
                company_guid=test_company_guid,
            )
