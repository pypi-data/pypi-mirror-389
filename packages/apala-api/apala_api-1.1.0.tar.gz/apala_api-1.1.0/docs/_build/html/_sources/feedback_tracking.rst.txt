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

   # Customer responded in 15 minutes
   feedback = MessageFeedback(
       original_message_id=message_id,
       sent_message_content=sent_content,
       customer_responded=True,
       quality_score=85,  # 0-100 scale
       time_to_respond_ms=900000  # 15 minutes in milliseconds
   )

   # Submit feedback
   result = client.submit_single_feedback(feedback)
   print(f"Feedback recorded with ID: {result['feedback_id']}")

Feedback Metrics
----------------

**Customer Response** (``customer_responded``)
   Boolean indicating whether the customer replied to your message.

**Quality Score** (``quality_score``)
   Your assessment of the interaction on a 0-100 scale:
   
   * 90-100: Excellent - Customer very satisfied, clear resolution
   * 80-89: Good - Positive interaction, customer needs met
   * 70-79: Satisfactory - Adequate response, some improvement possible
   * 60-69: Fair - Customer responded but interaction could be better
   * 50-59: Poor - Customer dissatisfied or confused
   * 0-49: Very Poor - Negative interaction, customer frustrated

**Response Time** (``time_to_respond_ms``)
   Time from message sent to customer response, in milliseconds:

   .. code-block:: python

      # Common time conversions
      MINUTE = 60 * 1000        # 60,000 ms
      HOUR = 60 * MINUTE        # 3,600,000 ms
      DAY = 24 * HOUR           # 86,400,000 ms

      # Examples
      feedback_5_min = MessageFeedback(
          ...,
          time_to_respond_ms=5 * MINUTE  # 5 minutes
      )

      feedback_2_hours = MessageFeedback(
          ...,
          time_to_respond_ms=2 * HOUR    # 2 hours
      )

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
       feedback = MessageFeedback(
           original_message_id=message_id,
           sent_message_content=processed_message["content"],
           customer_responded=customer_response_time is not None,
           quality_score=quality_score,
           time_to_respond_ms=customer_response_time
       )
       
       feedback_result = client.submit_single_feedback(feedback)
       print(f"📊 Feedback submitted: {feedback_result['feedback_id']}")
       
       return {
           "processing_response": response,
           "feedback_result": feedback_result,
           "quality_score": quality_score
       }

   def assess_interaction_quality(message_content, response_time_ms):
       """Assess interaction quality based on content and response time."""
       
       base_score = 75  # Start with satisfactory
       
       # Adjust for response time
       if response_time_ms is None:
           score = 40  # No response
       elif response_time_ms < 5 * 60 * 1000:  # < 5 minutes
           score = base_score + 15  # Very quick response
       elif response_time_ms < 30 * 60 * 1000:  # < 30 minutes
           score = base_score + 10  # Quick response
       elif response_time_ms < 2 * 60 * 60 * 1000:  # < 2 hours
           score = base_score + 5   # Good response time
       elif response_time_ms < 24 * 60 * 60 * 1000:  # < 24 hours
           score = base_score       # Acceptable
       else:
           score = base_score - 10  # Slow response
       
       # Adjust for message quality indicators
       if len(message_content) > 200:
           score += 5  # Detailed response
       if "?" in message_content:
           score += 3  # Engaging questions
       
       return min(100, max(0, score))  # Clamp to 0-100

Batch Feedback Submission
-------------------------

Submit feedback for multiple messages efficiently:

.. code-block:: python

   def submit_batch_feedback(client, feedback_list):
       """Submit multiple feedback records efficiently."""
       
       results = []
       errors = []
       
       for i, feedback in enumerate(feedback_list):
           try:
               result = client.submit_single_feedback(feedback)
               results.append({
                   "index": i,
                   "feedback_id": result["feedback_id"],
                   "success": True
               })
           except Exception as e:
               errors.append({
                   "index": i,
                   "error": str(e),
                   "message_id": feedback.original_message_id
               })
       
       return {
           "successful": results,
           "failed": errors,
           "success_rate": len(results) / len(feedback_list)
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

**Excellent (90-100)**
   - Customer responds quickly and positively
   - Clear resolution or next steps provided
   - Customer expresses satisfaction
   - No follow-up questions needed

**Good (80-89)**
   - Customer responds within reasonable time
   - Information provided is helpful
   - Minor clarification may be needed
   - Generally positive interaction

**Satisfactory (70-79)**
   - Customer responds but may need more information
   - Basic needs addressed
   - Some room for improvement in clarity or completeness

**Fair (60-69)**
   - Customer responds but seems confused or neutral
   - Information provided but not optimally presented
   - Requires significant follow-up

**Poor (50-59)**
   - Customer responds negatively or with frustration
   - Information unclear or incorrect
   - Customer needs are not well addressed

**Very Poor (0-49)**
   - No customer response or very negative response
   - Message caused confusion or frustration
   - Significant problems with content or approach

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