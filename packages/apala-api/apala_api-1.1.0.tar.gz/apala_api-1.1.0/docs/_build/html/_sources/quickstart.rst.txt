Quick Start Guide
=================

This guide will get you up and running with the Apala API Python SDK in minutes.

Installation
------------

Install the package using pip:

.. code-block:: bash

   pip install apala-api

Or install from source with development tools:

.. code-block:: bash

   git clone <repository-url>
   cd apala_api
   pip install -e ".[dev]"

First Steps
-----------

1. **Get Your API Credentials**

   Contact your Phoenix Message Analysis service provider to obtain:
   
   * API Key (for authentication)
   * Server URL (e.g., ``https://api.yourcompany.com``)
   * Company GUID (your organization's unique identifier)

2. **Set Environment Variables**

   .. code-block:: bash

      export APALA_API_KEY="your-api-key-here"
      export APALA_BASE_URL="https://your-server.com"
      export APALA_COMPANY_GUID="your-company-uuid"

3. **Create Your First Client**

   .. code-block:: python

      from apala_client import ApalaClient

      # Initialize the client
      client = ApalaClient(
          api_key="your-api-key",
          base_url="https://your-server.com"
      )

      # Authenticate and get JWT tokens
      auth_response = client.authenticate()
      print(f"Connected as: {auth_response['company_name']}")

Your First Message Processing
-----------------------------

Let's process a simple customer conversation:

.. code-block:: python

   from apala_client import ApalaClient, Message

   # 1. Initialize and authenticate
   client = ApalaClient(api_key="your-api-key")
   client.authenticate()

   # 2. Create customer message history
   customer_messages = [
       Message(
           content="Hi, I'm interested in getting a home loan",
           channel="EMAIL",
           reply_or_not=False
       ),
       Message(
           content="What documents do I need to provide?",
           channel="EMAIL", 
           reply_or_not=False
       )
   ]

   # 3. Create your candidate response
   candidate_response = Message(
       content="Thank you for your interest! For a home loan, you'll need: proof of income, credit report, and bank statements. Our rates start at 3.2% APR.",
       channel="EMAIL"
   )

   # 4. Process through the AI system
   response = client.message_process(
       message_history=customer_messages,
       candidate_message=candidate_response,
       customer_id="550e8400-e29b-41d4-a716-446655440000",
       zip_code="90210",
       company_guid="your-company-guid"
   )

   # 5. Access the results
   processed_message = response["candidate_message"]
   print(f"Message ID: {processed_message['message_id']}")
   print(f"Content: {processed_message['content']}")
   print(f"Channel: {processed_message['channel']}")

Your First Message Optimization
-------------------------------

Enhance your message for better customer engagement:

.. code-block:: python

   # Optimize the same message for better engagement
   optimization = client.optimize_message(
       message_history=customer_messages,
       candidate_message=candidate_response,
       customer_id="550e8400-e29b-41d4-a716-446655440000",
       zip_code="90210",
       company_guid="your-company-guid"
   )

   print("=== Message Optimization Results ===")
   print(f"Original: {optimization['original_message']}")
   print(f"Optimized: {optimization['optimized_message']}")
   print(f"Recommended Channel: {optimization['recommended_channel']}")

Your First Feedback Submission
------------------------------

Track how your messages perform:

.. code-block:: python

   from apala_client import MessageFeedback

   # After sending the message to your customer and getting their response
   feedback = MessageFeedback(
       original_message_id=processed_message["message_id"],
       sent_message_content=processed_message["content"],
       customer_responded=True,  # Did the customer respond?
       quality_score=85,  # Your assessment (0-100)
       time_to_respond_ms=1800000  # 30 minutes in milliseconds
   )

   # Submit the feedback
   feedback_result = client.submit_single_feedback(feedback)
   print(f"Feedback submitted! ID: {feedback_result['feedback_id']}")

Complete Example
----------------

Here's a complete working example that demonstrates the full workflow:

.. code-block:: python

   #!/usr/bin/env python3
   """
   Complete Apala API workflow example
   """

   import os
   from apala_client import ApalaClient, Message, MessageFeedback

   def main():
       # Configuration
       api_key = os.getenv("APALA_API_KEY", "your-api-key")
       base_url = os.getenv("APALA_BASE_URL", "https://your-server.com")
       company_guid = os.getenv("APALA_COMPANY_GUID", "your-company-uuid")
       
       # Initialize client
       client = ApalaClient(api_key=api_key, base_url=base_url)
       
       try:
           # Step 1: Authenticate
           print("🔐 Authenticating...")
           auth_response = client.authenticate()
           print(f"✅ Connected as: {auth_response['company_name']}")
           
           # Step 2: Prepare conversation data
           print("\n📝 Preparing conversation...")
           messages = [
               Message(
                   content="I'm having trouble with my account login",
                   channel="SMS",
                   reply_or_not=False
               ),
               Message(
                   content="I've tried resetting my password twice",
                   channel="SMS",
                   reply_or_not=False
               )
           ]
           
           candidate = Message(
               content="I understand your frustration. Let me help you resolve this right away. I'll send you a direct reset link.",
               channel="SMS"
           )
           
           # Step 3: Process messages
           print("📤 Processing messages...")
           response = client.message_process(
               message_history=messages,
               candidate_message=candidate,
               customer_id="550e8400-e29b-41d4-a716-446655440000",
               zip_code="90210",
               company_guid=company_guid
           )
           print(f"✅ Message processed: {response['candidate_message']['message_id']}")
           
           # Step 4: Optimize message
           print("🎯 Optimizing message...")
           optimization = client.optimize_message(
               message_history=messages,
               candidate_message=candidate,
               customer_id="550e8400-e29b-41d4-a716-446655440000",
               zip_code="90210",
               company_guid=company_guid
           )
           print(f"✅ Optimization complete")
           print(f"   Recommended channel: {optimization['recommended_channel']}")
           
           # Step 5: Submit feedback
           print("📊 Submitting feedback...")
           feedback = MessageFeedback(
               original_message_id=response["candidate_message"]["message_id"],
               sent_message_content=optimization["optimized_message"],
               customer_responded=True,
               quality_score=88,
               time_to_respond_ms=600000  # 10 minutes
           )
           
           feedback_result = client.submit_single_feedback(feedback)
           print(f"✅ Feedback submitted: {feedback_result['feedback_id']}")
           
           print("\n🎉 Workflow complete!")
           
       except Exception as e:
           print(f"❌ Error: {e}")
           
       finally:
           # Clean up
           client.close()

   if __name__ == "__main__":
       main()

Next Steps
----------

Now that you've completed the quick start, explore these topics:

* :doc:`authentication` - Learn about JWT token management
* :doc:`message_processing` - Deep dive into message processing features  
* :doc:`feedback_tracking` - Advanced feedback and analytics
* :doc:`examples` - More real-world examples and use cases
* :doc:`api/client` - Complete API reference

Common Issues
-------------

**Authentication Errors**
   - Verify your API key is correct
   - Check that the server URL is accessible
   - Ensure your API key has proper permissions

**Network Errors**
   - Confirm the server is running and accessible
   - Check firewall settings and network connectivity
   - Verify the base URL format (include ``https://``)

**Validation Errors**
   - Customer ID and Company GUID must be valid UUIDs
   - Zip code must be exactly 5 digits
   - Message channels must be "SMS", "EMAIL", or "OTHER"

**Type Errors (if using mypy)**
   - Install type stubs: ``pip install types-requests``
   - Check that you're using the correct response types
   - Verify import statements include the needed types

Getting Help
------------

* **Documentation**: Complete API reference in this documentation
* **Type Safety**: Enable mypy for compile-time error detection
* **Examples**: See :doc:`examples` for more use cases
* **GitHub Issues**: Report bugs and request features

Ready to build something amazing? Let's go! 🚀