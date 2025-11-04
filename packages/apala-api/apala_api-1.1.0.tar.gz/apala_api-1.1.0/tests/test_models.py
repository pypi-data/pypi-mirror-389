"""
Tests for data models.
"""


import pytest
from pydantic import ValidationError

from apala_client.models import (
    AuthResponse,
    BulkFeedbackResponse,
    FeedbackItemResponse,
    FeedbackResponse,
    Message,
    MessageFeedback,
    MessageHistory,
    MessageOptimizationResponse,
    MessageProcessingResponse,
)


class TestMessage:
    """Test the Message model."""

    def test_message_creation(self):
        """Test basic message creation."""
        msg = Message(content="Hello", channel="SMS")

        assert msg.content == "Hello"
        assert msg.channel == "SMS"
        assert msg.message_id is not None
        assert msg.send_timestamp is not None
        assert msg.reply_or_not is False

    def test_message_with_custom_id(self):
        """Test message creation with custom ID."""
        custom_id = "custom123"
        msg = Message(content="Hello", channel="EMAIL", message_id=custom_id)

        assert msg.message_id == custom_id

    def test_message_to_dict(self):
        """Test message conversion to dictionary."""
        msg = Message(
            content="Test message", channel="SMS", message_id="test123", reply_or_not=True
        )

        result = msg.to_dict()
        expected_keys = {"content", "message_id", "channel", "send_timestamp", "reply_or_not"}

        assert set(result.keys()) == expected_keys
        assert result["content"] == "Test message"
        assert result["channel"] == "SMS"
        assert result["message_id"] == "test123"
        assert result["reply_or_not"] == "true"  # Converted to string in to_dict()

    def test_message_invalid_channel(self):
        """Test message validation with invalid channel."""
        with pytest.raises(ValidationError) as exc_info:
            Message(content="Test", channel="INVALID")

        # Check that the error mentions valid channels
        assert "Channel must be one of" in str(exc_info.value)


class TestMessageFeedback:
    """Test the MessageFeedback model."""

    def test_feedback_creation(self):
        """Test basic feedback creation."""
        feedback = MessageFeedback(
            message_id="msg123",
            customer_responded=True,
            score="good",
        )

        assert feedback.message_id == "msg123"
        assert feedback.customer_responded is True
        assert feedback.score == "good"
        assert feedback.actual_sent_message is None

    def test_feedback_with_actual_message(self):
        """Test feedback creation with actual sent message."""
        feedback = MessageFeedback(
            message_id="msg123",
            customer_responded=True,
            score="good",
            actual_sent_message="Hello there",
        )

        assert feedback.actual_sent_message == "Hello there"

    def test_feedback_to_dict(self):
        """Test feedback conversion to dictionary."""
        feedback = MessageFeedback(
            message_id="msg123",
            customer_responded=False,
            score="neutral",
            actual_sent_message="Hello there",
        )

        result = feedback.to_dict()
        expected_keys = {
            "message_id",
            "customer_responded",
            "score",
            "actual_sent_message",
        }

        assert set(result.keys()) == expected_keys
        assert result["message_id"] == "msg123"
        assert result["customer_responded"] is False
        assert result["score"] == "neutral"
        assert result["actual_sent_message"] == "Hello there"

    def test_feedback_to_dict_no_actual_message(self):
        """Test feedback conversion without actual message."""
        feedback = MessageFeedback(
            message_id="msg123",
            customer_responded=True,
            score="bad",
        )

        result = feedback.to_dict()
        expected_keys = {
            "message_id",
            "customer_responded",
            "score",
        }

        assert set(result.keys()) == expected_keys
        assert "actual_sent_message" not in result

    def test_feedback_score_validation(self):
        """Test that feedback validates score values."""
        # Valid scores should work
        for score in ["good", "bad", "neutral"]:
            feedback = MessageFeedback(
                message_id="msg123",
                customer_responded=True,
                score=score,
            )
            assert feedback.score == score

        # Invalid score should raise ValidationError
        with pytest.raises(ValidationError):
            MessageFeedback(
                message_id="msg123",
                customer_responded=True,
                score="excellent",  # Invalid score
            )


class TestMessageHistory:
    """Test the MessageHistory model."""

    def test_message_history_creation(
        self, sample_messages, candidate_message, customer_id, zip_code, company_guid
    ):
        """Test basic message history creation."""
        history = MessageHistory(
            messages=sample_messages,
            candidate_message=candidate_message,
            customer_id=customer_id,
            zip_code=zip_code,
            company_guid=company_guid,
        )

        assert history.messages == sample_messages
        assert history.candidate_message == candidate_message
        assert history.customer_id == customer_id
        assert history.zip_code == zip_code
        assert history.company_guid == company_guid

    def test_invalid_customer_id(self, sample_messages, candidate_message, zip_code, company_guid):
        """Test validation of invalid customer ID."""
        with pytest.raises(ValidationError) as exc_info:
            MessageHistory(
                messages=sample_messages,
                candidate_message=candidate_message,
                customer_id="invalid-uuid",
                zip_code=zip_code,
                company_guid=company_guid,
            )
        assert "Invalid UUID format" in str(exc_info.value)

    def test_invalid_company_guid(self, sample_messages, candidate_message, customer_id, zip_code):
        """Test validation of invalid company GUID."""
        with pytest.raises(ValidationError) as exc_info:
            MessageHistory(
                messages=sample_messages,
                candidate_message=candidate_message,
                customer_id=customer_id,
                zip_code=zip_code,
                company_guid="not-a-uuid",
            )
        assert "Invalid UUID format" in str(exc_info.value)

    def test_invalid_zip_code(self, sample_messages, candidate_message, customer_id, company_guid):
        """Test validation of invalid zip code."""
        with pytest.raises(ValidationError) as exc_info:
            MessageHistory(
                messages=sample_messages,
                candidate_message=candidate_message,
                customer_id=customer_id,
                zip_code="123",  # Too short
                company_guid=company_guid,
            )
        # Pydantic pattern validation error
        assert "String should match pattern" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            MessageHistory(
                messages=sample_messages,
                candidate_message=candidate_message,
                customer_id=customer_id,
                zip_code="abcde",  # Not digits
                company_guid=company_guid,
            )
        # Pydantic pattern validation error
        assert "String should match pattern" in str(exc_info.value)

    def test_invalid_channel(self, candidate_message, customer_id, zip_code, company_guid):
        """Test validation of invalid message channels."""
        with pytest.raises(ValidationError) as exc_info:
            invalid_message = Message(content="Test", channel="INVALID")

        # The error should happen during Message creation, not MessageHistory
        assert "Channel must be one of" in str(exc_info.value)

    def test_to_processing_dict(self, message_history):
        """Test conversion to processing dictionary."""
        result = message_history.to_processing_dict()

        expected_keys = {"company", "customer_id", "zip_code", "messages", "candidate_message"}
        assert set(result.keys()) == expected_keys

        assert result["company"] == message_history.company_guid
        assert result["customer_id"] == message_history.customer_id
        assert result["zip_code"] == message_history.zip_code
        assert len(result["messages"]) == len(message_history.messages)
        assert isinstance(result["candidate_message"], dict)

    def test_to_optimization_dict(self, message_history):
        """Test conversion to optimization dictionary."""
        result = message_history.to_optimization_dict()

        expected_keys = {"company", "customer_id", "zip_code", "messages", "candidate_message"}
        assert set(result.keys()) == expected_keys

        assert result["company"] == message_history.company_guid
        assert result["customer_id"] == message_history.customer_id
        assert result["zip_code"] == message_history.zip_code
        assert len(result["messages"]) == len(message_history.messages)
        # For optimization, candidate_message should be just the content string
        assert result["candidate_message"] == message_history.candidate_message.content
