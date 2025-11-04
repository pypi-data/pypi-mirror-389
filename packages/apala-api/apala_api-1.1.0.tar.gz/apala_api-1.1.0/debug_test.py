#!/usr/bin/env python3
"""
Debug script to test individual API calls and see exact error responses.
"""

import json

from apala_client import ApalaClient
from apala_client.models import Message, MessageFeedback


def main():
    # Initialize client
    api_key = "IjU50unIfiSfO3txKLWpRDugelb9SGbsi6KShkLzeOM="
    company_guid = "550e8400-e29b-41d4-a716-446655440001"
    customer_id = "550e8400-e29b-41d4-a716-446655440002"

    client = ApalaClient(api_key=api_key, base_url="http://localhost:4000")

    # Test authentication
    print("🔐 Testing Authentication...")
    try:
        auth_response = client.authenticate()
        print(f"✅ Auth successful: {auth_response.get('company_name', 'N/A')}")
    except Exception as e:
        print(f"❌ Auth failed: {e}")
        return

    # Test message processing
    print("\n📤 Testing Message Processing...")
    messages = [
        Message(content="Hi, I need help with my loan.", channel="EMAIL"),
        Message(content="What are your rates?", channel="SMS"),
    ]
    candidate = Message(content="Thank you for your inquiry!", channel="EMAIL")

    try:
        process_response = client.message_process(
            message_history=messages,
            candidate_message=candidate,
            customer_id=customer_id,
            zip_code="90210",
            company_guid=company_guid,
        )
        print("✅ Message processing successful")
        print(f"   Message ID: {process_response['candidate_message']['message_id']}")
    except Exception as e:
        print(f"❌ Message processing failed: {e}")
        return

    # Test message optimization - debug the error
    print("\n🎯 Testing Message Optimization...")
    try:
        optimize_response = client.optimize_message(
            message_history=messages,
            candidate_message=candidate,
            customer_id=customer_id,
            zip_code="90210",
            company_guid=company_guid,
        )
        print("✅ Message optimization successful")
        print(f"   Optimized: {optimize_response.get('optimized_message', 'N/A')[:50]}...")
    except Exception as e:
        print(f"❌ Message optimization failed: {e}")
        # Let's see the actual response
        if hasattr(e, "response"):
            print(f"   Status: {e.response.status_code}")
            try:
                error_body = e.response.json()
                print(f"   Error: {json.dumps(error_body, indent=2)}")
            except:
                print(f"   Raw error: {e.response.text}")

    # Test feedback submission - debug the error
    print("\n📊 Testing Feedback Submission...")
    try:
        feedback = MessageFeedback(
            original_message_id=process_response["candidate_message"]["message_id"],
            sent_message_content=process_response["candidate_message"]["content"],
            customer_responded=True,
            quality_score=85,
            time_to_respond_ms=1800000,
        )

        feedback_response = client.submit_single_feedback(feedback)
        print("✅ Feedback submission successful")
        print(f"   Response: {feedback_response}")
    except Exception as e:
        print(f"❌ Feedback submission failed: {e}")
        # Let's see the actual response
        if hasattr(e, "response"):
            print(f"   Status: {e.response.status_code}")
            try:
                error_body = e.response.json()
                print(f"   Error: {json.dumps(error_body, indent=2)}")
            except:
                print(f"   Raw error: {e.response.text}")


if __name__ == "__main__":
    main()
