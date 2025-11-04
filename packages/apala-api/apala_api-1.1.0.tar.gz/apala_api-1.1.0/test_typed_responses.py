#!/usr/bin/env python3
"""
Demonstration of typed API responses working with real server.
Shows how mypy can provide type safety and IDE completion.
"""

from apala_client import ApalaClient, Message
from apala_client.models import AuthResponse, MessageProcessingResponse


def demonstrate_typed_responses() -> None:
    """Demonstrate typed responses with the Phoenix server."""

    # Initialize client
    api_key = "IjU50unIfiSfO3txKLWpRDugelb9SGbsi6KShkLzeOM="
    company_guid = "550e8400-e29b-41d4-a716-446655440001"
    customer_id = "550e8400-e29b-41d4-a716-446655440002"

    client = ApalaClient(api_key=api_key, base_url="http://localhost:4000")

    print("🔐 Testing Typed Authentication Response...")

    # This returns AuthResponse type - mypy knows the structure!
    auth_response: AuthResponse = client.authenticate()

    # IDE will provide autocomplete for these fields:
    print(f"✅ Company: {auth_response['company_name']}")
    print(f"   Company ID: {auth_response['company_id']}")
    print(f"   Token Type: {auth_response['token_type']}")
    print(f"   Expires In: {auth_response['expires_in']} seconds")

    # mypy knows access_token is a str
    token_length: int = len(auth_response["access_token"])
    print(f"   Access Token Length: {token_length}")

    print("\n📤 Testing Typed Message Processing Response...")

    # Create typed messages
    messages = [
        Message(content="Hi, I need information about loans.", channel="EMAIL"),
        Message(content="What are your rates?", channel="SMS"),
    ]

    candidate = Message(content="Thank you! Our rates start at 3.5% APR.", channel="EMAIL")

    # This returns MessageProcessingResponse type
    processing_response: MessageProcessingResponse = client.message_process(
        message_history=messages,
        candidate_message=candidate,
        customer_id=customer_id,
        zip_code="90210",
        company_guid=company_guid,
    )

    # IDE provides autocomplete and mypy enforces types:
    print(f"✅ Company: {processing_response['company']}")
    print(f"   Customer: {processing_response['customer_id']}")

    # Access nested typed structure
    candidate_msg = processing_response["candidate_message"]
    print(f"   Message ID: {candidate_msg['message_id']}")
    print(f"   Channel: {candidate_msg['channel']}")
    print(f"   Content: {candidate_msg['content'][:50]}...")

    print("\n🎉 Type Safety Verification Complete!")
    print("\nBenefits of Typed Responses:")
    print("✅ IDE autocomplete for response fields")
    print("✅ mypy catches type errors at development time")
    print("✅ Better code documentation through types")
    print("✅ Refactoring safety - mypy catches breaking changes")
    print("✅ No more runtime KeyError surprises")


if __name__ == "__main__":
    demonstrate_typed_responses()
