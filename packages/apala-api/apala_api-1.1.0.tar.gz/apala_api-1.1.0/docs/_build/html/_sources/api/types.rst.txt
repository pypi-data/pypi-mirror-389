Response Types
==============

.. automodule:: apala_client.models
   :members: AuthResponse, RefreshResponse, MessageProcessingResponse, MessageOptimizationResponse, FeedbackResponse, CandidateMessageResponse
   :undoc-members:

The Apala API provides fully typed responses using TypedDict for compile-time type safety and IDE autocomplete support.

Authentication Types
--------------------

AuthResponse
~~~~~~~~~~~~

.. autoclass:: apala_client.models.AuthResponse
   :members:

Response from the authentication endpoint when exchanging an API key for JWT tokens.

**Fields:**

* ``access_token`` (str): JWT access token for API requests
* ``refresh_token`` (str): JWT refresh token for obtaining new access tokens
* ``token_type`` (str): Token type, typically "Bearer"
* ``expires_in`` (int): Access token expiration time in seconds
* ``company_id`` (str): Your company's unique identifier
* ``company_name`` (str): Your company's display name

**Example:**

.. code-block:: python

   from apala_client import ApalaClient
   from apala_client.models import AuthResponse

   client = ApalaClient(api_key="your-key")
   auth_response: AuthResponse = client.authenticate()

   # Type-safe access to response fields
   token: str = auth_response["access_token"]
   company: str = auth_response["company_name"]
   expires: int = auth_response["expires_in"]

RefreshResponse
~~~~~~~~~~~~~~~

.. autoclass:: apala_client.models.RefreshResponse
   :members:

Response from the token refresh endpoint.

**Fields:**

* ``access_token`` (str): New JWT access token
* ``expires_in`` (int): New token expiration time in seconds

**Example:**

.. code-block:: python

   from apala_client.models import RefreshResponse

   refresh_response: RefreshResponse = client.refresh_access_token()
   new_token: str = refresh_response["access_token"]

Message Processing Types
------------------------

MessageProcessingResponse
~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: apala_client.models.MessageProcessingResponse
   :members:

Response from the message processing endpoint.

**Fields:**

* ``company`` (str): Company GUID that processed the message
* ``customer_id`` (str): Customer UUID
* ``candidate_message`` (CandidateMessageResponse): Processed message details

**Example:**

.. code-block:: python

   from apala_client.models import MessageProcessingResponse

   response: MessageProcessingResponse = client.message_process(...)
   
   # Type-safe field access
   company_id: str = response["company"]
   customer_id: str = response["customer_id"]
   message_info = response["candidate_message"]

CandidateMessageResponse
~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: apala_client.models.CandidateMessageResponse
   :members:

Nested type representing the processed candidate message.

**Fields:**

* ``content`` (str): The message content
* ``channel`` (str): Communication channel
* ``message_id`` (str): Unique message identifier

**Example:**

.. code-block:: python

   from apala_client.models import CandidateMessageResponse

   candidate: CandidateMessageResponse = response["candidate_message"]
   
   message_id: str = candidate["message_id"]
   content: str = candidate["content"]
   channel: str = candidate["channel"]

MessageOptimizationResponse
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: apala_client.models.MessageOptimizationResponse
   :members:

Response from the message optimization endpoint.

**Fields:**

* ``optimized_message`` (str): AI-enhanced message content
* ``recommended_channel`` (str): Optimal communication channel
* ``original_message`` (str): Original message for comparison

**Example:**

.. code-block:: python

   from apala_client.models import MessageOptimizationResponse

   optimization: MessageOptimizationResponse = client.optimize_message(...)
   
   original: str = optimization["original_message"]
   improved: str = optimization["optimized_message"]
   channel: str = optimization["recommended_channel"]

Feedback Types
--------------

FeedbackResponse
~~~~~~~~~~~~~~~~

.. autoclass:: apala_client.models.FeedbackResponse
   :members:

Response from feedback submission endpoints.

**Fields:**

* ``success`` (bool): Whether feedback was successfully recorded
* ``message`` (str): Human-readable status message
* ``feedback_id`` (int): Unique identifier for the feedback record
* ``received_at`` (str): ISO timestamp when feedback was received

**Example:**

.. code-block:: python

   from apala_client.models import FeedbackResponse

   feedback_response: FeedbackResponse = client.submit_single_feedback(feedback)
   
   success: bool = feedback_response["success"]
   feedback_id: int = feedback_response["feedback_id"]
   timestamp: str = feedback_response["received_at"]

Type Safety Benefits
--------------------

Using TypedDict provides several advantages:

**IDE Autocomplete**
   Your IDE can provide intelligent autocomplete for response fields:

   .. code-block:: python

      auth_response = client.authenticate()
      # IDE shows: access_token, refresh_token, company_name, etc.
      token = auth_response["access_token"]

**Compile-Time Error Detection**
   mypy catches type errors during development:

   .. code-block:: python

      # This will cause a mypy error:
      auth_response = client.authenticate()
      invalid_field = auth_response["nonexistent_field"]  # Error!

**Runtime Safety**
   TypedDict prevents accessing non-existent fields:

   .. code-block:: python

      # This raises a KeyError at runtime:
      response = client.authenticate()
      bad_field = response["missing_key"]  # KeyError!

**Documentation Through Types**
   The types serve as executable documentation:

   .. code-block:: python

      def process_auth_response(response: AuthResponse) -> str:
          # Developers know exactly what fields are available
          return f"Company {response['company_name']} authenticated"

Working with Typed Responses
-----------------------------

**Basic Usage**

.. code-block:: python

   from apala_client import ApalaClient
   from apala_client.models import AuthResponse, MessageProcessingResponse

   client = ApalaClient(api_key="your-key")
   
   # Fully typed authentication
   auth: AuthResponse = client.authenticate()
   company_name: str = auth["company_name"]
   
   # Fully typed message processing
   result: MessageProcessingResponse = client.message_process(...)
   message_id: str = result["candidate_message"]["message_id"]

**Error Handling with Types**

.. code-block:: python

   import requests
   from apala_client.models import AuthResponse

   try:
       auth_response: AuthResponse = client.authenticate()
       token = auth_response["access_token"]
   except requests.HTTPError as e:
       print(f"Authentication failed: {e.response.status_code}")
   except KeyError as e:
       print(f"Unexpected response format: {e}")

**Type Checking**

Enable mypy in your project to catch type errors:

.. code-block:: bash

   # Install mypy
   pip install mypy

   # Check your code
   mypy your_project.py

**IDE Configuration**

For the best experience, use an IDE that supports Python type hints:

* **VS Code**: Install the Python extension
* **PyCharm**: Type hints supported out of the box  
* **Vim/Neovim**: Use coc.nvim or similar plugins

This ensures you get full autocomplete and error detection while developing with the Apala API.