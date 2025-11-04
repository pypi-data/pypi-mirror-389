Apala API - Python SDK
========================

.. image:: https://img.shields.io/badge/python-3.9+-blue.svg
   :target: https://www.python.org/downloads/
   :alt: Python 3.9+

.. image:: https://img.shields.io/badge/type--hints-yes-brightgreen
   :target: https://docs.python.org/3/library/typing.html
   :alt: Type Hints

A modern, type-safe Python SDK for interacting with Phoenix Message Analysis Services for loan/financial AI applications.

**Copyright (c) 2025 Apala Cap. All rights reserved. Proprietary and confidential.**

Features
--------

✅ **Type-Safe API**
   - Full TypedDict responses with IDE autocomplete
   - mypy integration catches errors at development time
   - No runtime surprises - all response fields are typed

✅ **Complete Functionality**
   - Message Processing: Analyze customer conversations and candidate responses
   - Message Optimization: Enhance messages for maximum engagement
   - Feedback Tracking: Monitor message performance and customer responses
   - Authentication: Automatic JWT token management with refresh

✅ **Production Ready**
   - Multi-Python Support: Python 3.9, 3.10, 3.11, 3.12
   - Comprehensive Testing: Unit tests, integration tests, type checking
   - Error Handling: Uses standard ``requests`` exceptions (no custom exceptions)
   - Validation: Client-side validation of UUIDs, zip codes, channels

Quick Start
-----------

Installation
~~~~~~~~~~~~

.. code-block:: bash

   pip install apala-api

Basic Usage
~~~~~~~~~~~

.. code-block:: python

   from apala_client import ApalaClient, Message, MessageFeedback

   # Initialize client
   client = ApalaClient(
       api_key="your-api-key", 
       base_url="https://your-server.com"
   )

   # Authenticate (automatic JWT token management)
   client.authenticate()

   # Create customer message history
   messages = [
       Message(content="Hi, I need help with my loan application.", channel="EMAIL"),
       Message(content="What are the current interest rates?", channel="SMS"),
   ]

   # Create your candidate response
   candidate = Message(
       content="Thank you for your inquiry! Our current rates start at 3.5% APR.",
       channel="EMAIL"
   )

   # Process messages through the AI system
   response = client.message_process(
       message_history=messages,
       candidate_message=candidate,
       customer_id="550e8400-e29b-41d4-a716-446655440000",
       zip_code="90210",
       company_guid="550e8400-e29b-41d4-a716-446655440001"
   )

   # Submit feedback after customer interaction
   feedback = MessageFeedback(
       original_message_id=response["candidate_message"]["message_id"],
       sent_message_content=response["candidate_message"]["content"],
       customer_responded=True,
       quality_score=85,
       time_to_respond_ms=1800000  # 30 minutes
   )

   feedback_result = client.submit_single_feedback(feedback)

Table of Contents
-----------------

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   quickstart
   authentication
   message_processing
   feedback_tracking
   examples

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/client
   api/models
   api/types

.. toctree::
   :maxdepth: 1
   :caption: Development

   development
   testing
   contributing

