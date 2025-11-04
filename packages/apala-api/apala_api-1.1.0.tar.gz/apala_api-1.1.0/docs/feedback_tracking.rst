Feedback Tracking
=================

Feedback tracking allows you to measure the effectiveness of your processed messages and improve the AI system's performance over time.

Overview
--------

The feedback system tracks:

* **Response Rate**: Did the customer respond to your message?
* **Response Time**: How quickly did they respond?
* **Message Quality**: Your assessment of the interaction quality
* **Performance Metrics**: Analytics to improve future messages

Basic Feedback Submission
-------------------------

.. code-block:: python

   from apala_client import ApalaClient, MessageFeedback

   client = ApalaClient(api_key="your-key")
   client.authenticate()

   # After processing a message and sending it to customer
   response = client.message_process(...)  # Your message processing
   message_id = response["candidate_message"]["message_id"]
   sent_content = response["candidate_message"]["content"]

   # Customer responded positively
   result = client.submit_single_feedback(
       message_id=message_id,
       customer_responded=True,
       score="good",  # "good", "bad", or "neutral"
       actual_sent_message=sent_content
   )
   print(f"Feedback recorded with ID: {result.id}")

Feedback Metrics
----------------

**Customer Response** (``customer_responded``)
   Boolean indicating whether the customer replied to your message.

**Quality Score** (``score``)
   Your assessment of the interaction quality. Must be one of:

   * **"good"**: Positive interaction, customer needs met, clear resolution
   * **"neutral"**: Adequate response, customer responded but could be better
   * **"bad"**: Negative interaction, customer dissatisfied or no response

**Actual Sent Message** (``actual_sent_message``)
   Optional field containing the actual message content that was sent to the customer.
   Useful if you modified the optimized message before sending.

Tracking Workflow
-----------------

Here's a complete workflow for tracking message performance:

.. code-block:: python

   import time
   from datetime import datetime, timezone
   from apala_client import ApalaClient, Message, MessageFeedback

   def complete_message_workflow(client, conversation_data):
       """Complete workflow: process, send, track, and provide feedback."""
       
       # Step 1: Process message
       print("📤 Processing message...")
       response = client.message_process(
           message_history=conversation_data["messages"],
           candidate_message=conversation_data["candidate"],
           customer_id=conversation_data["customer_id"],
           zip_code=conversation_data["zip_code"],
           company_guid=conversation_data["company_guid"]
       )
       
       processed_message = response["candidate_message"]
       message_id = processed_message["message_id"]
       sent_time = datetime.now(timezone.utc)
       
       print(f"✅ Message processed: {message_id}")
       
       # Step 2: "Send" message to customer (simulate)
       print(f"📧 Sending to customer: {processed_message['content']}")
       
       # Step 3: Wait for and track customer response
       customer_response_time = wait_for_customer_response(
           message_id, 
           timeout_hours=24
       )
       
       # Step 4: Assess interaction quality
       quality_score = assess_interaction_quality(
           processed_message["content"],
           customer_response_time
       )
       
       # Step 5: Submit feedback
       feedback_result = client.submit_single_feedback(
           message_id=message_id,
           customer_responded=customer_response_time is not None,
           score=quality_score,
           actual_sent_message=processed_message["content"]
       )

       print(f"📊 Feedback submitted: {feedback_result.id}")
       
       return {
           "processing_response": response,
           "feedback_result": feedback_result,
           "quality_score": quality_score
       }

   def assess_interaction_quality(message_content, response_time_ms):
       """Assess interaction quality based on content and response time."""

       # Determine base score from response
       if response_time_ms is None:
           return "bad"  # No response
       elif response_time_ms < 30 * 60 * 1000:  # < 30 minutes
           base_quality = "good"  # Quick response
       elif response_time_ms < 24 * 60 * 60 * 1000:  # < 24 hours
           base_quality = "neutral"  # Acceptable timing
       else:
           base_quality = "bad"  # Slow response

       # Could adjust based on message quality indicators if needed
       # For now, return the time-based assessment
       return base_quality

Batch Feedback Submission
-------------------------

Submit feedback for multiple messages efficiently:

.. code-block:: python

   def submit_batch_feedback(client, feedback_list):
       """Submit multiple feedback records efficiently using bulk endpoint."""

       # Use the built-in bulk submission method
       try:
           result = client.submit_feedback_bulk(feedback_list)
           return {
               "success": result.success,
               "count": result.count,
               "feedback": result.feedback
           }
       except Exception as e:
           return {
               "success": False,
               "error": str(e)
           }

Analytics and Insights
----------------------

**Track Performance Trends**
   Monitor your message effectiveness over time:

   .. code-block:: python

      import pandas as pd
      from datetime import datetime, timedelta

      def analyze_feedback_trends(feedback_data):
          """Analyze feedback trends and performance metrics."""
          
          df = pd.DataFrame(feedback_data)
          
          # Response rate by channel
          response_rates = df.groupby('channel').agg({
              'customer_responded': 'mean',
              'quality_score': 'mean',
              'time_to_respond_ms': 'median'
          })
          
          print("Response Rates by Channel:")
          print(response_rates)
          
          # Quality score trends
          df['date'] = pd.to_datetime(df['sent_timestamp'])
          daily_quality = df.groupby(df['date'].dt.date)['quality_score'].mean()
          
          print("\nDaily Quality Score Trends:")
          print(daily_quality.tail(7))  # Last 7 days
          
          return {
              "overall_response_rate": df['customer_responded'].mean(),
              "average_quality_score": df['quality_score'].mean(),
              "median_response_time_hours": df['time_to_respond_ms'].median() / (1000 * 60 * 60)
          }

**A/B Testing with Feedback**
   Compare different message approaches:

   .. code-block:: python

      def ab_test_with_feedback(client, test_data):
          """Run A/B test and collect feedback for both variants."""
          
          results = {"variant_a": [], "variant_b": []}
          
          for conversation in test_data:
              # Randomly assign to variant
              variant = "variant_a" if hash(conversation["customer_id"]) % 2 == 0 else "variant_b"
              
              # Use appropriate message for variant
              candidate_message = conversation[f"candidate_{variant}"]
              
              # Process message
              response = client.message_process(
                  message_history=conversation["messages"],
                  candidate_message=candidate_message,
                  customer_id=conversation["customer_id"],
                  zip_code=conversation["zip_code"],
                  company_guid=conversation["company_guid"]
              )
              
              # Simulate customer interaction and feedback
              feedback = simulate_customer_interaction(response)
              feedback_result = client.submit_single_feedback(feedback)
              
              results[variant].append({
                  "feedback": feedback,
                  "feedback_id": feedback_result["feedback_id"],
                  "response": response
              })
          
          # Analyze results
          for variant, data in results.items():
              avg_quality = sum(item["feedback"].quality_score for item in data) / len(data)
              response_rate = sum(item["feedback"].customer_responded for item in data) / len(data)
              
              print(f"{variant.upper()}:")
              print(f"  Average Quality: {avg_quality:.1f}")
              print(f"  Response Rate: {response_rate:.1%}")
          
          return results

Quality Scoring Guidelines
--------------------------

**"good"**
   - Customer responds positively
   - Clear resolution or next steps provided
   - Customer expresses satisfaction
   - Information provided is helpful
   - Generally positive interaction

**"neutral"**
   - Customer responds but seems neutral
   - Basic needs addressed
   - Some room for improvement in clarity or completeness
   - Information provided but could be better
   - Requires follow-up

**"bad"**
   - No customer response
   - Customer responds negatively or with frustration
   - Information unclear or incorrect
   - Customer needs are not well addressed
   - Message caused confusion

Feedback Best Practices
-----------------------

**Timing**
   - Submit feedback as soon as you have customer response data
   - Don't wait too long - feedback is most valuable when recent
   - Set up automated tracking where possible

**Quality Assessment**
   - Be consistent in your scoring criteria
   - Consider both customer satisfaction and business outcomes
   - Document your scoring rationale for team consistency

**Data Collection**
   - Track all messages, not just successful ones
   - Include context about customer type and situation
   - Monitor trends over time, not just individual scores

**Privacy and Security**
   - Don't include sensitive customer information in feedback
   - Follow data retention policies
   - Ensure feedback data is properly secured

Integration Patterns
--------------------

**CRM Integration**
   Track feedback alongside customer records:

   .. code-block:: python

      def update_crm_with_feedback(crm_client, customer_id, feedback_result):
          """Update CRM with message feedback data."""
          
          crm_client.add_activity({
              "customer_id": customer_id,
              "activity_type": "message_feedback",
              "feedback_id": feedback_result["feedback_id"],
              "quality_score": feedback_result["quality_score"],
              "timestamp": datetime.now(timezone.utc).isoformat()
          })

**Analytics Platform Integration**
   Send feedback to analytics systems:

   .. code-block:: python

      import json

      def send_to_analytics(analytics_client, feedback_data):
          """Send feedback to analytics platform."""
          
          event = {
              "event_type": "message_feedback",
              "timestamp": datetime.now(timezone.utc).isoformat(),
              "properties": {
                  "message_id": feedback_data.original_message_id,
                  "customer_responded": feedback_data.customer_responded,
                  "quality_score": feedback_data.quality_score,
                  "response_time_ms": feedback_data.time_to_respond_ms
              }
          }
          
          analytics_client.track(event)

This feedback system helps you continuously improve your customer communications and maximize the effectiveness of the AI-enhanced messaging platform.