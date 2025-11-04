Data Models
===========

.. automodule:: apala_client.models
   :members:
   :undoc-members:
   :show-inheritance:

The data models provide type-safe interfaces for working with messages and feedback.

Message Model
-------------

.. autoclass:: apala_client.models.Message
   :members:
   :special-members: __init__, __post_init__
   :exclude-members: __weakref__

The :class:`Message` class represents both customer messages and candidate responses.

**Fields:**

* ``content`` (str): The message text content
* ``channel`` (str): Communication channel - "SMS", "EMAIL", or "OTHER"  
* ``message_id`` (Optional[str]): Unique message identifier (auto-generated if None)
* ``send_timestamp`` (Optional[str]): ISO timestamp (auto-generated if None)
* ``reply_or_not`` (bool): Whether this message is a reply (default: False)

**Example:**

.. code-block:: python

   from apala_client import Message

   # Customer message
   customer_msg = Message(
       content="I'm interested in a home loan",
       channel="EMAIL",
       reply_or_not=False
   )

   # Candidate response
   response_msg = Message(
       content="Great! Let me help you with loan options.",
       channel="EMAIL"
   )

   # Convert to dict for API calls
   data = customer_msg.to_dict()

MessageFeedback Model
---------------------

.. autoclass:: apala_client.models.MessageFeedback
   :members:
   :special-members: __init__
   :exclude-members: __weakref__

The :class:`MessageFeedback` class tracks performance metrics for processed messages.

**Fields:**

* ``original_message_id`` (str): ID from message processing response
* ``sent_message_content`` (str): Actual message content sent to customer
* ``customer_responded`` (bool): Whether the customer responded
* ``quality_score`` (int): Quality rating from 0-100
* ``time_to_respond_ms`` (Optional[int]): Customer response time in milliseconds

**Example:**

.. code-block:: python

   from apala_client import MessageFeedback

   feedback = MessageFeedback(
       original_message_id="msg_12345",
       sent_message_content="Thank you for your inquiry!",
       customer_responded=True,
       quality_score=85,
       time_to_respond_ms=1800000  # 30 minutes
   )

   # Convert to dict for API submission
   data = feedback.to_dict()

MessageHistory Model
--------------------

.. autoclass:: apala_client.models.MessageHistory
   :members:
   :special-members: __init__, __post_init__
   :exclude-members: __weakref__

The :class:`MessageHistory` class bundles together all data needed for message processing.

**Fields:**

* ``messages`` (List[Message]): List of customer messages
* ``candidate_message`` (Message): Your candidate response
* ``customer_id`` (str): Customer UUID
* ``zip_code`` (str): Customer's 5-digit zip code
* ``company_guid`` (str): Company UUID

**Validation:**

The ``__post_init__`` method automatically validates:

* UUIDs are properly formatted
* Zip code is exactly 5 digits
* All message channels are valid ("SMS", "EMAIL", "OTHER")

**Example:**

.. code-block:: python

   from apala_client import Message, MessageHistory

   history = MessageHistory(
       messages=[
           Message(content="Hello", channel="EMAIL"),
           Message(content="Need help", channel="SMS")
       ],
       candidate_message=Message(
           content="How can I assist you?",
           channel="EMAIL"
       ),
       customer_id="550e8400-e29b-41d4-a716-446655440000",
       zip_code="90210",
       company_guid="550e8400-e29b-41d4-a716-446655440001"
   )

   # Convert for processing API
   processing_data = history.to_processing_dict()

   # Convert for optimization API  
   optimization_data = history.to_optimization_dict()

Model Validation
----------------

All models include automatic validation:

**UUID Validation**
   Customer IDs and company GUIDs must be valid UUID format

**Zip Code Validation**
   Must be exactly 5 digits

**Channel Validation**
   Must be one of: "SMS", "EMAIL", "OTHER"

**Content Validation**
   Message content cannot be empty

**Example of Validation Errors:**

.. code-block:: python

   # This will raise ValueError
   try:
       invalid_history = MessageHistory(
           messages=[],
           candidate_message=candidate,
           customer_id="not-a-uuid",  # Invalid UUID
           zip_code="123",            # Too short
           company_guid="also-invalid"
       )
   except ValueError as e:
       print(f"Validation error: {e}")

Best Practices
--------------

**Message Creation**
   - Always specify the channel explicitly
   - Let message_id and send_timestamp auto-generate for new messages
   - Use descriptive content that clearly represents the customer's intent

**Feedback Tracking**
   - Submit feedback for every message you send to customers
   - Use realistic quality scores (0-100)
   - Include response time when available for better analytics

**Data Validation**
   - Use proper UUID format for customer and company IDs
   - Ensure zip codes are exactly 5 digits
   - Validate message content before processing