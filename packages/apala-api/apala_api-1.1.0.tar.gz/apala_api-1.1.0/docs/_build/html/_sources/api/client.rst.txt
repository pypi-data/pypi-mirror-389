ApalaClient
===========

.. automodule:: apala_client.client
   :members:
   :undoc-members:
   :show-inheritance:

The :class:`ApalaClient` is the main interface for interacting with the Phoenix Message Analysis API.

Overview
--------

The client provides the following functionality:

* **Authentication**: Automatic JWT token management with refresh
* **Message Processing**: Process customer message histories and candidate responses
* **Message Optimization**: Enhance messages for better customer engagement
* **Feedback Tracking**: Submit performance feedback for processed messages

Example Usage
-------------

Basic Client Setup
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from apala_client import ApalaClient

   # Initialize the client
   client = ApalaClient(
       api_key="your-api-key",
       base_url="https://your-server.com"
   )

   # Authenticate (gets JWT tokens)
   auth_response = client.authenticate()
   print(f"Authenticated as: {auth_response['company_name']}")

Message Processing
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from apala_client import Message

   # Create message history
   messages = [
       Message(content="I need help with my loan", channel="EMAIL"),
       Message(content="What are your rates?", channel="SMS")
   ]

   # Define candidate response
   candidate = Message(
       content="Our rates start at 3.5% APR. Let me help you!",
       channel="EMAIL"
   )

   # Process through AI system
   response = client.message_process(
       message_history=messages,
       candidate_message=candidate,
       customer_id="customer-uuid-here",
       zip_code="12345",
       company_guid="company-uuid-here"
   )

   # Access typed response
   message_id = response["candidate_message"]["message_id"]
   print(f"Processed message ID: {message_id}")

Message Optimization
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Optimize message for better engagement
   optimization = client.optimize_message(
       message_history=messages,
       candidate_message=candidate,
       customer_id="customer-uuid",
       zip_code="12345",
       company_guid="company-uuid"
   )

   print(f"Original: {optimization['original_message']}")
   print(f"Optimized: {optimization['optimized_message']}")
   print(f"Recommended channel: {optimization['recommended_channel']}")

Feedback Submission
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from apala_client import MessageFeedback

   # Create feedback after customer interaction
   feedback = MessageFeedback(
       original_message_id="message-id-from-processing",
       sent_message_content="The actual message sent",
       customer_responded=True,
       quality_score=88,
       time_to_respond_ms=1200000  # 20 minutes
   )

   # Submit feedback
   result = client.submit_single_feedback(feedback)
   print(f"Feedback ID: {result['feedback_id']}")

Error Handling
--------------

The client uses standard ``requests`` library exceptions:

.. code-block:: python

   import requests

   try:
       response = client.message_process(...)
   except requests.HTTPError as e:
       print(f"HTTP error: {e.response.status_code}")
   except requests.ConnectionError as e:
       print(f"Connection error: {e}")
   except requests.RequestException as e:
       print(f"Request error: {e}")
   except ValueError as e:
       print(f"Validation error: {e}")

Class Reference
---------------

.. autoclass:: apala_client.client.ApalaClient
   :members:
   :special-members: __init__
   :exclude-members: __weakref__