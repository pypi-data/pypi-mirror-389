Message Processing
==================

The message processing system analyzes customer conversation history and candidate responses to provide AI-enhanced communication recommendations.

Core Concepts
-------------

**Message History**
   A chronological sequence of customer messages leading up to the current interaction.

**Candidate Message**
   Your proposed response to the customer's messages.

**Processing**
   The AI system analyzes context, sentiment, and intent to enhance your response.

**Optimization**
   Further refinement of messages for maximum customer engagement.

Basic Message Processing
------------------------

.. code-block:: python

   from apala_client import ApalaClient, Message

   client = ApalaClient(api_key="your-key")
   client.authenticate()

   # Customer conversation history
   messages = [
       Message(
           content="I'm looking for a mortgage refinance",
           channel="EMAIL",
           reply_or_not=False
       ),
       Message(
           content="My current rate is 4.5% and I have excellent credit",
           channel="EMAIL",
           reply_or_not=False
       )
   ]

   # Your candidate response
   candidate = Message(
       content="With excellent credit, you could qualify for rates as low as 3.1%. Let me run some numbers for you.",
       channel="EMAIL"
   )

   # Process through AI system
   response = client.message_process(
       message_history=messages,
       candidate_message=candidate,
       customer_id="550e8400-e29b-41d4-a716-446655440000",
       zip_code="90210",
       company_guid="company-uuid-here"
   )

   # Access results
   processed_msg = response["candidate_message"]
   print(f"Processed message ID: {processed_msg['message_id']}")
   print(f"Enhanced content: {processed_msg['content']}")

Message Types and Channels
--------------------------

**Supported Channels**
   - ``"SMS"``: Text message communication
   - ``"EMAIL"``: Email communication  
   - ``"OTHER"``: Any other communication channel

**Channel-Specific Optimization**
   The AI adjusts message style based on channel:

   .. code-block:: python

      # SMS - concise and direct
      sms_msg = Message(
          content="Hi! Ready to discuss loan options?",
          channel="SMS"
      )

      # EMAIL - more detailed and formal
      email_msg = Message(
          content="Thank you for your inquiry. I'd be happy to discuss our competitive loan options and help you find the perfect solution.",
          channel="EMAIL"
      )

Advanced Processing Workflows
-----------------------------

**Multi-Turn Conversations**
   Handle complex conversation flows:

   .. code-block:: python

      def process_conversation_chain(client, conversation_data):
          """Process a multi-turn conversation."""
          
          all_messages = []
          responses = []
          
          for turn in conversation_data["turns"]:
              # Add customer messages to history
              customer_msg = Message(
                  content=turn["customer_content"],
                  channel=turn["channel"],
                  reply_or_not=False
              )
              all_messages.append(customer_msg)
              
              # Process with full history
              candidate = Message(
                  content=turn["candidate_response"],
                  channel=turn["channel"]
              )
              
              response = client.message_process(
                  message_history=all_messages.copy(),
                  candidate_message=candidate,
                  customer_id=conversation_data["customer_id"],
                  zip_code=conversation_data["zip_code"],
                  company_guid=conversation_data["company_guid"]
              )
              
              responses.append(response)
              
              # Add processed response to history for next turn
              response_msg = Message(
                  content=response["candidate_message"]["content"],
                  channel=response["candidate_message"]["channel"],
                  message_id=response["candidate_message"]["message_id"],
                  reply_or_not=True
              )
              all_messages.append(response_msg)
          
          return responses

**Batch Processing**
   Process multiple conversations efficiently:

   .. code-block:: python

      import concurrent.futures
      from typing import List, Dict

      def batch_process_messages(
          client: ApalaClient, 
          conversations: List[Dict],
          max_workers: int = 5
      ) -> List[Dict]:
          """Process multiple conversations in parallel."""
          
          def process_single(conv_data):
              try:
                  return client.message_process(
                      message_history=conv_data["messages"],
                      candidate_message=conv_data["candidate"],
                      customer_id=conv_data["customer_id"],
                      zip_code=conv_data["zip_code"],
                      company_guid=conv_data["company_guid"]
                  )
              except Exception as e:
                  return {"error": str(e), "conversation_id": conv_data.get("id")}
          
          with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
              results = list(executor.map(process_single, conversations))
          
          return results

Message Optimization
--------------------

Optimize messages for better customer engagement:

.. code-block:: python

   # Get optimized version of your message
   optimization = client.optimize_message(
       message_history=messages,
       candidate_message=candidate,
       customer_id="customer-uuid",
       zip_code="90210",
       company_guid="company-uuid"
   )

   print("=== Optimization Results ===")
   print(f"Original: {optimization['original_message']}")
   print(f"Optimized: {optimization['optimized_message']}")
   print(f"Recommended Channel: {optimization['recommended_channel']}")

**A/B Testing with Optimization**
   Compare original vs optimized messages:

   .. code-block:: python

      def ab_test_messages(client, message_data):
          """Run A/B test comparing original vs optimized messages."""
          
          # Process original message
          original_response = client.message_process(**message_data)
          
          # Get optimized version
          optimization = client.optimize_message(**message_data)
          
          # Create optimized candidate
          optimized_candidate = Message(
              content=optimization["optimized_message"],
              channel=optimization["recommended_channel"]
          )
          
          # Process optimized message
          optimized_data = message_data.copy()
          optimized_data["candidate_message"] = optimized_candidate
          optimized_response = client.message_process(**optimized_data)
          
          return {
              "original": original_response,
              "optimized": optimized_response,
              "optimization_suggestions": optimization
          }

Context and Personalization
---------------------------

**Customer Context**
   Use customer data for personalized responses:

   .. code-block:: python

      def create_personalized_message(customer_profile, base_message):
          """Create personalized message based on customer profile."""
          
          # Customize based on customer data
          if customer_profile.get("credit_score", 0) > 750:
              tone = "Our premium rates for excellent credit customers"
          elif customer_profile.get("first_time_buyer"):
              tone = "First-time buyer programs and guidance"
          else:
              tone = "Competitive rates and flexible terms"
          
          personalized_content = f"{base_message} {tone}"
          
          return Message(
              content=personalized_content,
              channel=customer_profile.get("preferred_channel", "EMAIL")
          )

**Geographic Personalization**
   Leverage zip code data:

   .. code-block:: python

      # ZIP code influences processing
      high_cost_areas = ["90210", "10001", "94102"]  # CA, NY examples
      
      if zip_code in high_cost_areas:
          candidate_content = "Our jumbo loan programs offer competitive rates for high-value properties in your area."
      else:
          candidate_content = "Our conventional loan programs offer great rates for properties in your market."

Error Handling and Validation
-----------------------------

**Input Validation**
   The SDK automatically validates inputs:

   .. code-block:: python

      try:
          response = client.message_process(
              message_history=messages,
              candidate_message=candidate,
              customer_id="invalid-uuid",  # Will raise ValueError
              zip_code="123",              # Will raise ValueError
              company_guid="company-uuid"
          )
      except ValueError as e:
          print(f"Validation error: {e}")

**Processing Errors**
   Handle API errors gracefully:

   .. code-block:: python

      import requests
      import time

      def robust_message_processing(client, message_data, max_retries=3):
          """Process message with retry logic."""
          
          for attempt in range(max_retries):
              try:
                  return client.message_process(**message_data)
              except requests.HTTPError as e:
                  if e.response.status_code == 429:  # Rate limited
                      wait_time = 2 ** attempt
                      print(f"Rate limited, waiting {wait_time}s...")
                      time.sleep(wait_time)
                  elif e.response.status_code >= 500:  # Server error
                      print(f"Server error on attempt {attempt + 1}")
                      if attempt < max_retries - 1:
                          time.sleep(1)
                  else:
                      raise  # Don't retry client errors
              except requests.ConnectionError:
                  print(f"Connection error on attempt {attempt + 1}")
                  if attempt < max_retries - 1:
                      time.sleep(2 ** attempt)
          
          raise Exception(f"Processing failed after {max_retries} attempts")

Performance Optimization
------------------------

**Session Reuse**
   Reuse client instances for better performance:

   .. code-block:: python

      # Good: Reuse client
      client = ApalaClient(api_key="key")
      client.authenticate()
      
      for conversation in conversations:
          response = client.message_process(**conversation)
      
      client.close()

      # Bad: Create new client each time
      for conversation in conversations:
          client = ApalaClient(api_key="key")  # Wasteful
          client.authenticate()
          response = client.message_process(**conversation)
          client.close()

**Request Batching**
   Group related requests when possible:

   .. code-block:: python

      def process_customer_workflow(client, customer_data):
          """Process multiple steps for a single customer efficiently."""
          
          # Step 1: Process initial message
          response = client.message_process(**customer_data["initial"])
          
          # Step 2: Optimize the same message
          optimization = client.optimize_message(**customer_data["initial"])
          
          # Step 3: Process follow-up if needed
          if customer_data.get("followup"):
              followup_response = client.message_process(**customer_data["followup"])
              return response, optimization, followup_response
          
          return response, optimization

Best Practices
--------------

**Message Quality**
   - Provide clear, natural conversation history
   - Write candidate responses in your authentic voice
   - Include relevant context in message history
   - Use appropriate channels for message types

**Performance**
   - Reuse authenticated client instances
   - Implement appropriate retry logic
   - Use batch processing for multiple conversations
   - Cache optimization results when applicable

**Error Handling**
   - Always validate inputs before processing
   - Handle network errors gracefully
   - Log processing events for debugging
   - Implement circuit breaker patterns for high-volume usage

**Data Management**
   - Store message IDs for feedback tracking
   - Maintain conversation history for context
   - Track processing metrics for optimization
   - Implement data retention policies as needed