"""
Pytest configuration and fixtures.
"""

import uuid

import pytest

from apala_client import ApalaClient
from apala_client.models import Message, MessageFeedback, MessageHistory


@pytest.fixture
def api_key():
    """Sample API key for testing."""
    return "test-api-key-12345"


@pytest.fixture
def base_url():
    """Sample base URL for testing."""
    return "http://localhost:4000"


@pytest.fixture
def company_guid():
    """Sample company GUID."""
    return str(uuid.uuid4())


@pytest.fixture
def customer_id():
    """Sample customer ID."""
    return str(uuid.uuid4())


@pytest.fixture
def zip_code():
    """Sample zip code."""
    return "90210"


@pytest.fixture
def sample_messages():
    """Sample message history."""
    return [
        Message(
            content="Hi, I have a question about my loan application.",
            channel="EMAIL",
            message_id="msg001",
            reply_or_not=False,
        ),
        Message(
            content="When can I expect to hear back?",
            channel="SMS",
            message_id="msg002",
            reply_or_not=False,
        ),
    ]


@pytest.fixture
def candidate_message():
    """Sample candidate message."""
    return Message(
        content="Thank you for your inquiry. We'll respond within 2 business days.",
        channel="EMAIL",
        message_id="candidate001",
    )


@pytest.fixture
def message_feedback():
    """Sample message feedback."""
    return MessageFeedback(
        message_id="candidate001",
        customer_responded=True,
        score="good",
        actual_sent_message="Thank you for your inquiry. We'll respond within 2 business days.",
    )


@pytest.fixture
def message_history(sample_messages, candidate_message, customer_id, zip_code, company_guid):
    """Sample message history object."""
    return MessageHistory(
        messages=sample_messages,
        candidate_message=candidate_message,
        customer_id=customer_id,
        zip_code=zip_code,
        company_guid=company_guid,
    )


@pytest.fixture
def client(api_key, base_url):
    """ApalaClient instance for testing."""
    return ApalaClient(api_key=api_key, base_url=base_url)


@pytest.fixture
def authenticated_client(client):
    """Authenticated ApalaClient with mocked tokens."""
    client.access_token = "mock-access-token"
    client.refresh_token = "mock-refresh-token"
    client.token_expires_at = 9999999999  # Far future
    return client


@pytest.fixture
def mock_auth_response():
    """Mock authentication response."""
    return {
        "access_token": "mock-access-token",
        "refresh_token": "mock-refresh-token",
        "token_type": "Bearer",
        "expires_in": 3600,
        "company_id": "550e8400-e29b-41d4-a716-446655440000",
        "company_name": "Test Company",
    }


@pytest.fixture
def mock_processing_response(company_guid, customer_id):
    """Mock message processing response."""
    return {
        "company": company_guid,
        "customer_id": customer_id,
        "candidate_message": {
            "content": "Thank you for your inquiry. We'll respond within 2 business days.",
            "channel": "EMAIL",
            "message_id": "candidate001",
        },
    }


@pytest.fixture
def mock_optimization_response():
    """Mock message optimization response."""
    return {
        "message_id": "550e8400-e29b-41d4-a716-446655440000",
        "optimized_message": "Hi! Quick update on your loan - we'll have an answer by end of week. Thanks!",
        "recommended_channel": "SMS",
        "original_message": "Thank you for your inquiry. We'll respond within 2 business days.",
    }


@pytest.fixture
def mock_feedback_response():
    """Mock feedback submission response."""
    return {
        "success": True,
        "message": "Feedback received successfully",
        "feedback_id": 456,
        "received_at": "2024-01-15T10:30:00Z",
    }
