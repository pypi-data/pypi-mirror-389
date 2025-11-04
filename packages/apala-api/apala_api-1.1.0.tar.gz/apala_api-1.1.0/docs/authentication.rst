Authentication Guide
===================

The Apala API uses a two-tier authentication system: API keys for initial authentication and JWT tokens for ongoing API requests.

Authentication Flow
-------------------

1. **API Key Exchange**: Your API key is exchanged for JWT access and refresh tokens
2. **Token Usage**: All API requests use the JWT access token
3. **Automatic Refresh**: The SDK automatically refreshes tokens when they expire

Basic Authentication
--------------------

.. code-block:: python

   from apala_client import ApalaClient

   # Initialize with API key
   client = ApalaClient(
       api_key="IjU50unIfiSfO3txKLWpRDugelb9SGbsi6KShkLzeOM=",
       base_url="https://your-phoenix-server.com"
   )

   # Authenticate and get JWT tokens
   auth_response = client.authenticate()
   
   print(f"Company: {auth_response['company_name']}")
   print(f"Token expires in: {auth_response['expires_in']} seconds")

Environment Variables
---------------------

For security, store credentials in environment variables:

.. code-block:: bash

   # Set environment variables
   export APALA_API_KEY="your-api-key-here"
   export APALA_BASE_URL="https://your-server.com"
   export APALA_COMPANY_GUID="your-company-uuid"

.. code-block:: python

   import os
   from apala_client import ApalaClient

   # Load from environment
   client = ApalaClient(
       api_key=os.getenv("APALA_API_KEY"),
       base_url=os.getenv("APALA_BASE_URL")
   )

Token Management
----------------

The SDK handles token lifecycle automatically:

**Automatic Refresh**
   Tokens are refreshed 60 seconds before expiration

**Manual Refresh**
   You can manually refresh if needed:

   .. code-block:: python

      # Force token refresh
      refresh_response = client.refresh_access_token()
      print(f"New token expires in: {refresh_response['expires_in']} seconds")

**Token Inspection**
   Check current token status:

   .. code-block:: python

      import time

      # Check if token is valid
      current_time = time.time()
      is_valid = client.access_token and current_time < (client.token_expires_at or 0)
      
      if not is_valid:
          print("Token expired or missing, re-authenticating...")
          client.authenticate()

Authentication Errors
---------------------

Handle common authentication issues:

.. code-block:: python

   import requests

   try:
       auth_response = client.authenticate()
   except requests.HTTPError as e:
       if e.response.status_code == 401:
           print("Invalid API key")
       elif e.response.status_code == 403:
           print("API key lacks necessary permissions")
       elif e.response.status_code >= 500:
           print("Server error - try again later")
       else:
           print(f"Authentication failed: {e.response.status_code}")
   except requests.ConnectionError:
       print("Cannot connect to server - check URL and network")

Secure API Key Storage
----------------------

**Development**
   Use environment variables or config files (never commit to git):

   .. code-block:: python

      # .env file (add to .gitignore)
      APALA_API_KEY=your-key-here
      APALA_BASE_URL=https://your-server.com

      # Load with python-dotenv
      from dotenv import load_dotenv
      load_dotenv()

**Production**
   Use secure secret management:

   .. code-block:: python

      # AWS Secrets Manager example
      import boto3
      import json

      def get_api_credentials():
          client = boto3.client('secretsmanager')
          response = client.get_secret_value(SecretId='apala-api-credentials')
          secrets = json.loads(response['SecretString'])
          return secrets['api_key'], secrets['base_url']

      api_key, base_url = get_api_credentials()
      client = ApalaClient(api_key=api_key, base_url=base_url)

Authentication Best Practices
-----------------------------

**Security**
   - Never hardcode API keys in source code
   - Use environment variables for local development
   - Use secret management services in production
   - Rotate API keys regularly

**Error Handling**
   - Always handle authentication failures gracefully
   - Implement retry logic for temporary failures
   - Log authentication events for monitoring

**Performance**
   - Reuse the same client instance across requests
   - Let the SDK handle token refresh automatically
   - Don't authenticate more frequently than necessary

Production Authentication Pattern
---------------------------------

Here's a production-ready authentication pattern:

.. code-block:: python

   import os
   import logging
   import time
   from contextlib import contextmanager
   from apala_client import ApalaClient
   import requests

   logger = logging.getLogger(__name__)

   class SecureApalaClient:
       def __init__(self):
           self.api_key = os.environ["APALA_API_KEY"]
           self.base_url = os.environ["APALA_BASE_URL"]
           self._client = None
           self._last_auth_attempt = 0
           self._auth_retry_delay = 300  # 5 minutes

       @contextmanager
       def get_authenticated_client(self):
           """Context manager providing authenticated client."""
           try:
               client = self._get_client()
               yield client
           finally:
               if client:
                   client.close()

       def _get_client(self):
           """Get or create authenticated client."""
           current_time = time.time()
           
           # Create new client if needed
           if not self._client:
               self._client = ApalaClient(
                   api_key=self.api_key,
                   base_url=self.base_url
               )

           # Check if we need to authenticate
           needs_auth = (
               not self._client.access_token or 
               current_time >= (self._client.token_expires_at or 0)
           )

           if needs_auth:
               self._authenticate_with_retry()

           return self._client

       def _authenticate_with_retry(self):
           """Authenticate with exponential backoff retry."""
           current_time = time.time()
           
           # Prevent too frequent retry attempts
           if current_time - self._last_auth_attempt < self._auth_retry_delay:
               raise Exception("Authentication retry delay not met")

           max_retries = 3
           for attempt in range(max_retries):
               try:
                   logger.info(f"Authentication attempt {attempt + 1}")
                   self._client.authenticate()
                   logger.info("Authentication successful")
                   self._last_auth_attempt = current_time
                   return
               except requests.HTTPError as e:
                   logger.error(f"Auth attempt {attempt + 1} failed: {e.response.status_code}")
                   if e.response.status_code in [401, 403]:
                       # Don't retry auth errors
                       raise
                   if attempt < max_retries - 1:
                       time.sleep(2 ** attempt)  # Exponential backoff
               except requests.ConnectionError as e:
                   logger.error(f"Auth attempt {attempt + 1} connection failed: {e}")
                   if attempt < max_retries - 1:
                       time.sleep(2 ** attempt)

           self._last_auth_attempt = current_time
           raise Exception(f"Authentication failed after {max_retries} attempts")

   # Usage
   secure_client = SecureApalaClient()
   
   with secure_client.get_authenticated_client() as client:
       response = client.message_process(...)

Debugging Authentication
------------------------

Enable debug logging to troubleshoot authentication issues:

.. code-block:: python

   import logging
   import urllib3

   # Enable debug logging
   logging.basicConfig(level=logging.DEBUG)
   urllib3.disable_warnings()  # Optional: disable SSL warnings

   client = ApalaClient(api_key="your-key", base_url="https://server.com")
   
   try:
       auth_response = client.authenticate()
       print("Debug: Authentication successful")
   except Exception as e:
       print(f"Debug: Authentication failed - {e}")

This will show detailed HTTP request/response information to help diagnose authentication problems.