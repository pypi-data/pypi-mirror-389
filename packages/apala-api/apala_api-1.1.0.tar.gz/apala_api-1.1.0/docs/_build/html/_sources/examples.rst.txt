Examples and Use Cases
======================

This page provides real-world examples of using the Apala API for various loan and financial scenarios.

Loan Application Inquiry
-------------------------

Handle customer inquiries about loan applications:

.. code-block:: python

   from apala_client import ApalaClient, Message, MessageFeedback

   def handle_loan_inquiry():
       client = ApalaClient(api_key="your-api-key")
       client.authenticate()
       
       # Customer conversation about loan application
       messages = [
           Message(
               content="Hi, I submitted a loan application last week but haven't heard back. Can you check the status?",
               channel="EMAIL",
               reply_or_not=False
           ),
           Message(
               content="The application reference number is LA-2024-1234.",
               channel="EMAIL", 
               reply_or_not=False
           )
       ]
       
       # Your proposed response
       candidate = Message(
           content="Thank you for following up on your loan application LA-2024-1234. I've checked your status and your application is currently under review. You can expect a decision within 3-5 business days. I'll send you an email as soon as we have an update.",
           channel="EMAIL"
       )
       
       # Process and optimize
       response = client.message_process(
           message_history=messages,
           candidate_message=candidate,
           customer_id="customer-uuid",
           zip_code="90210",
           company_guid="company-uuid"
       )
       
       optimization = client.optimize_message(
           message_history=messages,
           candidate_message=candidate,
           customer_id="customer-uuid",
           zip_code="90210",
           company_guid="company-uuid"
       )
       
       print(f"Original: {candidate.content}")
       print(f"Optimized: {optimization['optimized_message']}")
       print(f"Channel: {optimization['recommended_channel']}")
       
       return response, optimization

Rate Shopping Conversation
--------------------------

Help customers compare loan rates and terms:

.. code-block:: python

   def handle_rate_shopping():
       client = ApalaClient(api_key="your-api-key")
       client.authenticate()
       
       # Customer asking about rates
       messages = [
           Message(
               content="I'm shopping for a mortgage and want to compare your rates with other lenders.",
               channel="SMS",
               reply_or_not=False
           ),
           Message(
               content="I have excellent credit (790+ score) and 20% down payment.",
               channel="SMS",
               reply_or_not=False
           ),
           Message(
               content="Looking at a $400K home purchase in California.",
               channel="SMS",
               reply_or_not=False
           )
       ]
       
       candidate = Message(
           content="Great credit score! For a $400K purchase with 20% down, our current rates start at 3.25% APR for 30-year fixed. With your credit profile, you'd likely qualify for our best rates. Can I schedule a quick call to discuss your specific situation?",
           channel="SMS"
       )
       
       # Process the conversation
       response = client.message_process(
           message_history=messages,
           candidate_message=candidate,
           customer_id="customer-uuid",
           zip_code="90210",
           company_guid="company-uuid"
       )
       
       return response

Document Collection Process
---------------------------

Guide customers through document submission:

.. code-block:: python

   def handle_document_collection():
       client = ApalaClient(api_key="your-api-key")
       client.authenticate()
       
       # Customer confused about documents
       messages = [
           Message(
               content="I'm ready to submit my loan documents but I'm not sure what you need exactly.",
               channel="EMAIL",
               reply_or_not=False
           ),
           Message(
               content="I'm self-employed so my income documentation might be different than usual.",
               channel="EMAIL",
               reply_or_not=False
           )
       ]
       
       candidate = Message(
           content="Perfect timing! For self-employed borrowers, we need: 2 years of tax returns with all schedules, 2 years of profit & loss statements, 3 months of bank statements, and a CPA letter. I'll email you a secure upload link and checklist right now.",
           channel="EMAIL"
       )
       
       # Get optimized version
       optimization = client.optimize_message(
           message_history=messages,
           candidate_message=candidate,
           customer_id="customer-uuid",
           zip_code="90210",
           company_guid="company-uuid"
       )
       
       return optimization

Batch Processing Multiple Conversations
--------------------------------------

Process multiple customer conversations efficiently:

.. code-block:: python

   def batch_process_conversations():
       client = ApalaClient(api_key="your-api-key")
       client.authenticate()
       
       # Multiple customer scenarios
       conversations = [
           {
               "customer_id": "customer-1-uuid",
               "zip_code": "90210",
               "messages": [
                   Message(content="Need refinancing help", channel="SMS"),
               ],
               "candidate": Message(content="I'd be happy to help with refinancing options.", channel="SMS")
           },
           {
               "customer_id": "customer-2-uuid", 
               "zip_code": "10001",
               "messages": [
                   Message(content="First time home buyer questions", channel="EMAIL"),
               ],
               "candidate": Message(content="Congratulations on your first home purchase journey!", channel="EMAIL")
           }
       ]
       
       results = []
       for conv in conversations:
           response = client.message_process(
               message_history=conv["messages"],
               candidate_message=conv["candidate"],
               customer_id=conv["customer_id"],
               zip_code=conv["zip_code"],
               company_guid="company-uuid"
           )
           results.append(response)
       
       return results

Feedback Tracking Workflow
--------------------------

Implement comprehensive feedback tracking:

.. code-block:: python

   def track_message_performance():
       client = ApalaClient(api_key="your-api-key")
       client.authenticate()
       
       # Simulate message processing
       response = process_customer_message(client)
       message_id = response["candidate_message"]["message_id"]
       message_content = response["candidate_message"]["content"]
       
       # Simulate different customer response scenarios
       scenarios = [
           {
               "name": "Quick Positive Response",
               "responded": True,
               "quality_score": 90,
               "response_time_minutes": 15
           },
           {
               "name": "Delayed Response", 
               "responded": True,
               "quality_score": 75,
               "response_time_minutes": 240  # 4 hours
           },
           {
               "name": "No Response",
               "responded": False,
               "quality_score": 40,
               "response_time_minutes": None
           }
       ]
       
       feedback_results = []
       for scenario in scenarios:
           feedback = MessageFeedback(
               original_message_id=message_id,
               sent_message_content=message_content,
               customer_responded=scenario["responded"],
               quality_score=scenario["quality_score"],
               time_to_respond_ms=scenario["response_time_minutes"] * 60 * 1000 if scenario["response_time_minutes"] else None
           )
           
           result = client.submit_single_feedback(feedback)
           feedback_results.append({
               "scenario": scenario["name"],
               "feedback_id": result["feedback_id"]
           })
       
       return feedback_results

Error Handling and Retry Logic
------------------------------

Implement robust error handling for production use:

.. code-block:: python

   import requests
   import time
   from typing import Optional

   def robust_message_processing(
       client: ApalaClient,
       messages: list,
       candidate: Message,
       customer_id: str,
       zip_code: str,
       company_guid: str,
       max_retries: int = 3
   ) -> Optional[dict]:
       """
       Process messages with retry logic and comprehensive error handling.
       """
       
       for attempt in range(max_retries):
           try:
               # Ensure we have valid authentication
               if not client.access_token or time.time() >= (client.token_expires_at or 0):
                   print(f"Attempt {attempt + 1}: Refreshing authentication...")
                   client.authenticate()
               
               # Process the messages
               response = client.message_process(
                   message_history=messages,
                   candidate_message=candidate,
                   customer_id=customer_id,
                   zip_code=zip_code,
                   company_guid=company_guid
               )
               
               print(f"✅ Success on attempt {attempt + 1}")
               return response
               
           except requests.HTTPError as e:
               print(f"❌ HTTP error on attempt {attempt + 1}: {e.response.status_code}")
               
               if e.response.status_code == 401:
                   # Authentication issue - try to re-authenticate
                   print("🔄 Re-authenticating due to 401 error...")
                   try:
                       client.authenticate()
                   except Exception as auth_error:
                       print(f"❌ Re-authentication failed: {auth_error}")
                       
               elif e.response.status_code == 429:
                   # Rate limited - wait before retry
                   wait_time = 2 ** attempt  # Exponential backoff
                   print(f"⏳ Rate limited, waiting {wait_time} seconds...")
                   time.sleep(wait_time)
                   
               elif e.response.status_code >= 500:
                   # Server error - retry might help
                   wait_time = 2 ** attempt
                   print(f"⏳ Server error, waiting {wait_time} seconds before retry...")
                   time.sleep(wait_time)
               else:
                   # Client error - don't retry
                   print(f"❌ Client error {e.response.status_code}, not retrying")
                   break
                   
           except requests.ConnectionError as e:
               print(f"❌ Connection error on attempt {attempt + 1}: {e}")
               wait_time = 2 ** attempt
               print(f"⏳ Waiting {wait_time} seconds before retry...")
               time.sleep(wait_time)
               
           except ValueError as e:
               # Validation error - don't retry
               print(f"❌ Validation error: {e}")
               break
               
           except Exception as e:
               print(f"❌ Unexpected error on attempt {attempt + 1}: {e}")
               wait_time = 2 ** attempt
               time.sleep(wait_time)
       
       print(f"❌ Failed after {max_retries} attempts")
       return None

Custom Session Configuration
----------------------------

Configure the HTTP session for specific requirements:

.. code-block:: python

   import requests
   from requests.adapters import HTTPAdapter
   from requests.packages.urllib3.util.retry import Retry

   def create_custom_client():
       """Create a client with custom session configuration."""
       
       client = ApalaClient(api_key="your-api-key")
       
       # Create custom session with retry strategy
       session = requests.Session()
       
       # Configure retry strategy
       retry_strategy = Retry(
           total=3,
           backoff_factor=1,
           status_forcelist=[429, 500, 502, 503, 504],
       )
       
       adapter = HTTPAdapter(max_retries=retry_strategy)
       session.mount("http://", adapter)
       session.mount("https://", adapter)
       
       # Set custom timeout
       session.timeout = 30
       
       # Add custom headers
       session.headers.update({
           'User-Agent': 'MyApp/1.0 ApalaSDK/0.1.0'
       })
       
       # Replace the client's session
       client._session = session
       
       return client

Production Deployment Example
-----------------------------

Example of how to use the SDK in a production environment:

.. code-block:: python

   import os
   import logging
   from contextlib import contextmanager
   from apala_client import ApalaClient

   # Configure logging
   logging.basicConfig(level=logging.INFO)
   logger = logging.getLogger(__name__)

   class ProductionApalaService:
       """Production-ready wrapper for Apala API operations."""
       
       def __init__(self):
           self.api_key = os.environ["APALA_API_KEY"]
           self.base_url = os.environ["APALA_BASE_URL"]
           self.company_guid = os.environ["APALA_COMPANY_GUID"]
           self.client = None
       
       @contextmanager
       def get_client(self):
           """Context manager for client lifecycle."""
           client = ApalaClient(api_key=self.api_key, base_url=self.base_url)
           try:
               client.authenticate()
               logger.info("Apala client authenticated successfully")
               yield client
           except Exception as e:
               logger.error(f"Apala client error: {e}")
               raise
           finally:
               client.close()
               logger.info("Apala client closed")
       
       def process_customer_message(self, customer_data: dict) -> dict:
           """Process a customer message with full error handling."""
           
           with self.get_client() as client:
               try:
                   response = client.message_process(
                       message_history=customer_data["messages"],
                       candidate_message=customer_data["candidate"],
                       customer_id=customer_data["customer_id"],
                       zip_code=customer_data["zip_code"],
                       company_guid=self.company_guid
                   )
                   
                   logger.info(f"Message processed: {response['candidate_message']['message_id']}")
                   return response
                   
               except Exception as e:
                   logger.error(f"Message processing failed: {e}")
                   raise

   # Usage
   service = ProductionApalaService()
   result = service.process_customer_message({
       "messages": [Message(content="Help needed", channel="EMAIL")],
       "candidate": Message(content="Happy to help!", channel="EMAIL"),
       "customer_id": "customer-uuid",
       "zip_code": "90210"
   })

Interactive Development with Jupyter
------------------------------------

Use the SDK in Jupyter notebooks for analysis and experimentation:

.. code-block:: python

   # Cell 1: Setup
   %pip install apala-api
   import pandas as pd
   from apala_client import ApalaClient, Message, MessageFeedback

   # Cell 2: Initialize
   client = ApalaClient(api_key="your-api-key")
   auth_response = client.authenticate()
   print(f"Connected as: {auth_response['company_name']}")

   # Cell 3: Process multiple messages and analyze results
   results = []
   
   test_scenarios = [
       {"content": "Need loan help", "channel": "SMS"},
       {"content": "Rate inquiry", "channel": "EMAIL"},
       {"content": "Document questions", "channel": "OTHER"}
   ]
   
   for scenario in test_scenarios:
       messages = [Message(content=scenario["content"], channel=scenario["channel"])]
       candidate = Message(content="I'm here to help!", channel=scenario["channel"])
       
       response = client.message_process(
           message_history=messages,
           candidate_message=candidate,
           customer_id="test-customer-uuid",
           zip_code="90210",
           company_guid="company-uuid"
       )
       
       results.append({
           "original_channel": scenario["channel"],
           "content": scenario["content"],
           "message_id": response["candidate_message"]["message_id"],
           "processed_content": response["candidate_message"]["content"]
       })
   
   # Cell 4: Analyze with pandas
   df = pd.DataFrame(results)
   print(df.head())

Testing and Development
----------------------

Example test patterns for your own applications:

.. code-block:: python

   import pytest
   from unittest.mock import Mock, patch
   from apala_client import ApalaClient, Message

   class TestApalaIntegration:
       
       @pytest.fixture
       def mock_client(self):
           """Mock client for testing."""
           client = ApalaClient(api_key="test-key")
           client.access_token = "mock-token"
           client.token_expires_at = 9999999999  # Far future
           return client
       
       @patch('requests.Session.post')
       def test_message_processing(self, mock_post, mock_client):
           """Test message processing with mocked response."""
           
           # Mock the API response
           mock_response = Mock()
           mock_response.json.return_value = {
               "company": "test-company",
               "customer_id": "test-customer",
               "candidate_message": {
                   "content": "Test response",
                   "channel": "EMAIL",
                   "message_id": "test-msg-123"
               }
           }
           mock_response.raise_for_status.return_value = None
           mock_post.return_value = mock_response
           
           # Test the processing
           messages = [Message(content="Test", channel="EMAIL")]
           candidate = Message(content="Response", channel="EMAIL")
           
           response = mock_client.message_process(
               message_history=messages,
               candidate_message=candidate,
               customer_id="test-customer",
               zip_code="90210",
               company_guid="test-company"
           )
           
           assert response["candidate_message"]["message_id"] == "test-msg-123"
           mock_post.assert_called_once()

These examples should give you a solid foundation for building production applications with the Apala API. Remember to always handle errors gracefully and implement appropriate retry logic for your use case!