"""
Apala API Demo - Interactive Marimo Notebook

This notebook demonstrates the complete workflow for using the Apala API
to interact with Phoenix Message Analysis Services.
"""

import marimo

__generated_with = "0.16.5"
app = marimo.App(width="medium")


@app.cell
def __():
    import marimo as mo
    import os
    import sys
    import uuid
    import traceback
    from typing import Any, Dict

    # Add parent directory to path to import our client
    sys.path.append("..")

    from apala_client import ApalaClient
    from apala_client.models import Message, MessageFeedback

    mo.md(
        """
        # 🚀 Apala API Interactive Demo

        Welcome to the comprehensive demonstration of the Apala API Python SDK!
        This notebook will guide you through:

        1. 🔐 **Authentication** - Setting up API credentials
        2. 📝 **Message Processing** - Analyzing customer conversations
        3. 🎯 **Message Optimization** - Enhancing messages for better engagement
        4. 📊 **Feedback Tracking** - Monitoring message performance

        Let's get started!
        """
    )
    return ApalaClient, Message, MessageFeedback, mo, os, sys, traceback, uuid


@app.cell
def __(mo):
    mo.md(
        """
        ## 🔐 Step 1: Authentication Setup

        First, let's configure your API credentials. You can either:
        - Enter them in the form below, or
        - Set environment variables: `APALA_API_KEY`, `APALA_BASE_URL`, `APALA_COMPANY_GUID`
        """
    )
    return


@app.cell
def __(mo, os):
    # Create input forms for API configuration
    api_key_input = mo.ui.text(
        placeholder="Enter your API key",
        value=os.getenv("APALA_API_KEY", "IjU50unIfiSfO3txKLWpRDugelb9SGbsi6KShkLzeOM="),
        label="API Key"
    )

    base_url_input = mo.ui.text(
        placeholder="https://your-phoenix-server.com",
        value=os.getenv("APALA_BASE_URL", "http://localhost:4000"),
        label="Server URL"
    )

    company_guid_input = mo.ui.text(
        placeholder="your-company-uuid",
        value=os.getenv("APALA_COMPANY_GUID", "550e8400-e29b-41d4-a716-446655440001"),
        label="Company GUID"
    )

    customer_id_input = mo.ui.text(
        placeholder="customer-uuid",
        value="550e8400-e29b-41d4-a716-446655440000",
        label="Customer ID (for demo)"
    )

    zip_code_input = mo.ui.text(
        placeholder="90210",
        value="90210",
        label="Zip Code"
    )

    auth_button = mo.ui.run_button(label="🔐 Test Authentication")

    mo.vstack([
        mo.md("**Configuration:**"),
        api_key_input,
        base_url_input,
        company_guid_input,
        customer_id_input,
        zip_code_input,
        mo.md("## Test Your Connection"),
        auth_button
    ])
    return (
        api_key_input,
        auth_button,
        base_url_input,
        company_guid_input,
        customer_id_input,
        zip_code_input,
    )


@app.cell
def __(ApalaClient, api_key_input, auth_button, base_url_input, mo, traceback):
    # Authentication logic - runs when auth_button is clicked
    if auth_button.value:
        try:
            client = ApalaClient(
                api_key=api_key_input.value,
                base_url=base_url_input.value
            )
            auth_response = client.authenticate()

            auth_result = mo.md(f"""
            ✅ **Authentication Successful!**

            - **Company**: {auth_response['company_name']}
            - **Company ID**: {auth_response['company_id']}
            - **Token Type**: {auth_response['token_type']}
            - **Token expires in**: {auth_response['expires_in']} seconds
            - **Access Token** (first 30 chars): `{auth_response['access_token'][:30]}...`

            <details>
            <summary>📋 Full Response JSON</summary>

            ```json
            {{
              "access_token": "{auth_response['access_token'][:50]}...",
              "refresh_token": "{auth_response['refresh_token'][:50]}...",
              "token_type": "{auth_response['token_type']}",
              "expires_in": {auth_response['expires_in']},
              "company_id": "{auth_response['company_id']}",
              "company_name": "{auth_response['company_name']}"
            }}
            ```
            </details>
            """)

        except Exception as e:
            auth_result = mo.md(f"""
            ❌ **Authentication Failed**

            **Error Type**: `{type(e).__name__}`

            **Error Message**: `{str(e)}`

            <details>
            <summary>📋 Full Traceback</summary>

            ```
            {traceback.format_exc()}
            ```
            </details>

            **Troubleshooting:**
            - Check that Phoenix server is running at `{base_url_input.value}`
            - Verify API key is valid
            - Ensure network connectivity
            """)
            client = None
            auth_response = None
    else:
        auth_result = mo.md("👆 Click the button above to test authentication.")
        client = None
        auth_response = None

    # Display result
    auth_result
    return auth_response, auth_result, client


@app.cell
def __(mo):
    mo.md(
        """
        ## 📝 Step 2: Message Processing Demo

        Now let's process a customer conversation. You can customize the messages below:
        """
    )
    return


@app.cell
def __(mo):
    # Message input forms
    customer_msg1 = mo.ui.text_area(
        value="Hi, I'm interested in refinancing my mortgage. My current rate is 4.5% and I have excellent credit.",
        label="Customer Message 1"
    )

    customer_msg2 = mo.ui.text_area(
        value="What documents do I need to provide and how long does the process take?",
        label="Customer Message 2"
    )

    candidate_response = mo.ui.text_area(
        value="Thank you for your interest in refinancing! With excellent credit, you could qualify for rates as low as 3.1%. For the application, you'll need: recent pay stubs, tax returns, and bank statements. The process typically takes 30-45 days.",
        label="Your Candidate Response"
    )

    process_button = mo.ui.run_button(label="📤 Process Messages")

    mo.vstack([
        mo.md("**Customer Conversation:**"),
        customer_msg1,
        customer_msg2,
        mo.md("**Your Response:**"),
        candidate_response,
        process_button
    ])
    return candidate_response, customer_msg1, customer_msg2, process_button


@app.cell
def __(
    Message,
    client,
    candidate_response,
    company_guid_input,
    customer_id_input,
    customer_msg1,
    customer_msg2,
    mo,
    process_button,
    traceback,
    zip_code_input,
):
    # Message processing logic - runs when process_button is clicked
    if process_button.value and client is not None:
        try:
            # Create message objects
            # Customer messages have reply_or_not=False (they are incoming messages)
            messages = [
                Message(
                    content=customer_msg1.value,
                    channel="EMAIL",
                    reply_or_not=False
                ),
                Message(
                    content=customer_msg2.value,
                    channel="EMAIL",
                    reply_or_not=False
                )
            ]

            # Candidate message is our response, so reply_or_not=True
            candidate = Message(
                content=candidate_response.value,
                channel="EMAIL",
                reply_or_not=True
            )

            # Create the payload for debugging
            import json as _json_proc
            from apala_client.models import MessageHistory as _MessageHistory_proc

            _message_history_obj = _MessageHistory_proc(
                messages=messages,
                candidate_message=candidate,
                customer_id=customer_id_input.value,
                zip_code=zip_code_input.value,
                company_guid=company_guid_input.value
            )

            _payload = _message_history_obj.to_processing_dict()
            _payload_json_proc = _json_proc.dumps(_payload, indent=2)

            # Process through API
            processing_response = client.message_process(
                message_history=messages,
                candidate_message=candidate,
                customer_id=customer_id_input.value,
                zip_code=zip_code_input.value,
                company_guid=company_guid_input.value
            )

            processing_result = mo.md(f"""
            ✅ **Message Processing Successful!**

            ### Response Details
            - **Message ID**: `{processing_response['candidate_message']['message_id']}`
            - **Channel**: `{processing_response['candidate_message']['channel']}`
            - **Company GUID**: `{processing_response['company']}`
            - **Customer ID**: `{processing_response['customer_id']}`

            ### Processed Message Content
            > {processing_response['candidate_message']['content']}

            <details>
            <summary>📋 Full API Response</summary>

            ```json
            {{
              "company": "{processing_response['company']}",
              "customer_id": "{processing_response['customer_id']}",
              "candidate_message": {{
                "message_id": "{processing_response['candidate_message']['message_id']}",
                "content": "{processing_response['candidate_message']['content'][:100]}...",
                "channel": "{processing_response['candidate_message']['channel']}"
              }}
            }}
            ```
            </details>

            ### Input Summary
            - **Message History**: {len(messages)} message(s)
            - **Zip Code**: {zip_code_input.value}
            """)

        except Exception as e:
            # Try to get error response body from server
            import json as _json_proc_err
            _error_response_proc = ""
            if hasattr(e, 'response') and e.response is not None:
                try:
                    _error_response_proc = e.response.text
                except:
                    _error_response_proc = "Could not read error response"

            # Get the payload that was sent
            try:
                from apala_client.models import MessageHistory as _MessageHistory_proc_err
                _message_history_obj_err = _MessageHistory_proc_err(
                    messages=messages,
                    candidate_message=candidate,
                    customer_id=customer_id_input.value,
                    zip_code=zip_code_input.value,
                    company_guid=company_guid_input.value
                )
                _payload_err = _message_history_obj_err.to_processing_dict()
                _payload_json_proc_err = _json_proc_err.dumps(_payload_err, indent=2)
            except Exception as payload_error:
                _payload_json_proc_err = f"Could not generate payload: {str(payload_error)}"

            processing_result = mo.md(f"""
            ❌ **Processing Failed**

            **Error Type**: `{type(e).__name__}`

            **Error Message**: `{str(e)}`

            <details>
            <summary>🔍 Server Error Response</summary>

            ```
            {_error_response_proc}
            ```
            </details>

            <details>
            <summary>📤 Request Payload Sent</summary>

            ```json
            {_payload_json_proc_err}
            ```
            </details>

            <details>
            <summary>📋 Full Traceback</summary>

            ```
            {traceback.format_exc()}
            ```
            </details>

            **What was sent:**
            - Customer ID: `{customer_id_input.value}`
            - Zip Code: `{zip_code_input.value}`
            - Company GUID: `{company_guid_input.value}`
            - Message count: 2
            """)
            processing_response = None
            messages = None
            candidate = None
    else:
        if client is None:
            processing_result = mo.md("❗ Complete authentication first, then click the button above to process messages.")
        else:
            processing_result = mo.md("👆 Click the button above to process messages.")
        processing_response = None
        messages = None
        candidate = None

    # Display result
    processing_result
    return candidate, messages, processing_response, processing_result


@app.cell
def __(mo):
    mo.md(
        """
        ## 🎯 Step 3: Message Optimization

        Let's optimize your message for better customer engagement:
        """
    )
    return


@app.cell
def __(mo):
    optimize_button = mo.ui.run_button(label="🎯 Optimize Message")
    optimize_button
    return (optimize_button,)


@app.cell
def __(
    candidate,
    client,
    messages,
    processing_response,
    candidate_response,
    company_guid_input,
    customer_id_input,
    mo,
    optimize_button,
    traceback,
    zip_code_input,
):
    # Message optimization logic - runs when optimize_button is clicked
    if optimize_button.value and processing_response is not None:
        try:
            # Create the payload for debugging
            import json as _json_opt
            from apala_client.models import MessageHistory as _MessageHistory_opt

            _message_history_obj_opt = _MessageHistory_opt(
                messages=messages,
                candidate_message=candidate,
                customer_id=customer_id_input.value,
                zip_code=zip_code_input.value,
                company_guid=company_guid_input.value
            )

            _payload_opt = _message_history_obj_opt.to_optimization_dict()
            _payload_json_opt = _json_opt.dumps(_payload_opt, indent=2)

            optimization = client.optimize_message(
                message_history=messages,
                candidate_message=candidate,
                customer_id=customer_id_input.value,
                zip_code=zip_code_input.value,
                company_guid=company_guid_input.value
            )

            optimization_result = mo.md(f"""
            ✅ **Message Optimization Complete!**

            ### Original Message
            > {optimization['original_message']}

            ### 🎯 Optimized Message
            > {optimization['optimized_message']}

            ### Recommendations
            - **Recommended Channel**: `{optimization['recommended_channel']}`

            <details>
            <summary>📋 Full Optimization Response</summary>

            ```json
            {{
              "original_message": "{optimization['original_message'][:100]}...",
              "optimized_message": "{optimization['optimized_message'][:100]}...",
              "recommended_channel": "{optimization['recommended_channel']}"
            }}
            ```
            </details>

            ### Comparison
            - **Original Length**: {len(optimization['original_message'])} characters
            - **Optimized Length**: {len(optimization['optimized_message'])} characters
            - **Change**: {len(optimization['optimized_message']) - len(optimization['original_message']):+d} characters
            """)

        except Exception as e:
            # Try to get error response body from server
            import json as _json_opt_err
            _error_response_opt = ""
            if hasattr(e, 'response') and e.response is not None:
                try:
                    _error_response_opt = e.response.text
                except:
                    _error_response_opt = "Could not read error response"

            # Get the payload that was sent
            try:
                from apala_client.models import MessageHistory as _MessageHistory_opt_err
                _message_history_obj_opt_err = _MessageHistory_opt_err(
                    messages=messages,
                    candidate_message=candidate,
                    customer_id=customer_id_input.value,
                    zip_code=zip_code_input.value,
                    company_guid=company_guid_input.value
                )
                _payload_opt_err = _message_history_obj_opt_err.to_optimization_dict()
                _payload_json_opt_err = _json_opt_err.dumps(_payload_opt_err, indent=2)
            except Exception as payload_error:
                _payload_json_opt_err = f"Could not generate payload: {str(payload_error)}"

            optimization_result = mo.md(f"""
            ❌ **Optimization Failed**

            **Error Type**: `{type(e).__name__}`

            **Error Message**: `{str(e)}`

            <details>
            <summary>🔍 Server Error Response</summary>

            ```
            {_error_response_opt}
            ```
            </details>

            <details>
            <summary>📤 Request Payload Sent</summary>

            ```json
            {_payload_json_opt_err}
            ```
            </details>

            <details>
            <summary>📋 Full Traceback</summary>

            ```
            {traceback.format_exc()}
            ```
            </details>

            **Request Details:**
            - Customer ID: `{customer_id_input.value}`
            - Zip Code: `{zip_code_input.value}`
            - Company GUID: `{company_guid_input.value}`
            - Original message length: {len(candidate_response.value)} chars
            """)
            optimization = None
    else:
        if processing_response is None:
            optimization_result = mo.md("❗ Complete message processing first, then click the button above to optimize.")
        else:
            optimization_result = mo.md("👆 Click the button above to optimize the message.")
        optimization = None

    # Display result
    optimization_result
    return optimization, optimization_result


@app.cell
def __(mo):
    mo.md(
        """
        ## 📊 Step 4: Feedback Submission

        After sending your message to the customer, track its performance:
        """
    )
    return


@app.cell
def __(mo):
    # Feedback form
    customer_responded = mo.ui.checkbox(value=True, label="Customer responded")

    quality_score = mo.ui.slider(
        start=0, stop=100, value=85, step=5,
        label="Quality Score (0-100)"
    )

    response_time = mo.ui.number(
        value=30, label="Response time (minutes)"
    )

    feedback_button = mo.ui.run_button(label="📊 Submit Feedback")

    mo.vstack([
        mo.md("**Feedback Metrics:**"),
        customer_responded,
        quality_score,
        response_time,
        feedback_button
    ])
    return customer_responded, feedback_button, quality_score, response_time


@app.cell
def __(
    MessageFeedback,
    client,
    processing_response,
    customer_responded,
    feedback_button,
    mo,
    quality_score,
    response_time,
    traceback,
):
    # Feedback submission logic - runs when feedback_button is clicked
    if feedback_button.value and processing_response is not None:
        try:
            feedback = MessageFeedback(
                original_message_id=processing_response["candidate_message"]["message_id"],
                sent_message_content=processing_response["candidate_message"]["content"],
                customer_responded=customer_responded.value,
                quality_score=quality_score.value,
                time_to_respond_ms=response_time.value * 60 * 1000 if customer_responded.value else None
            )

            feedback_response = client.submit_single_feedback(feedback)

            feedback_result = mo.md(f"""
            ✅ **Feedback Submitted Successfully!**

            ### Server Response
            - **Status**: {feedback_response['success']}
            - **Message**: {feedback_response['message']}
            - **Feedback ID**: `{feedback_response['feedback_id']}`
            - **Received At**: {feedback_response['received_at']}

            ### Feedback Summary
            - **Original Message ID**: `{feedback.original_message_id}`
            - **Customer Responded**: {"Yes ✅" if feedback.customer_responded else "No ❌"}
            - **Quality Score**: {feedback.quality_score}/100
            - **Response Time**: {f"{response_time.value} minutes ({feedback.time_to_respond_ms} ms)" if feedback.time_to_respond_ms else "N/A"}

            <details>
            <summary>📋 Full Feedback Payload</summary>

            ```json
            {{
              "original_message_id": "{feedback.original_message_id}",
              "sent_message_content": "{feedback.sent_message_content[:100]}...",
              "customer_responded": {str(feedback.customer_responded).lower()},
              "quality_score": {feedback.quality_score},
              "time_to_respond_in_millis": {feedback.time_to_respond_ms if feedback.time_to_respond_ms else "null"}
            }}
            ```
            </details>

            <details>
            <summary>📋 Server Response JSON</summary>

            ```json
            {{
              "success": {str(feedback_response['success']).lower()},
              "message": "{feedback_response['message']}",
              "feedback_id": {feedback_response['feedback_id']},
              "received_at": "{feedback_response['received_at']}"
            }}
            ```
            </details>
            """)

        except Exception as e:
            feedback_result = mo.md(f"""
            ❌ **Feedback Submission Failed**

            **Error Type**: `{type(e).__name__}`

            **Error Message**: `{str(e)}`

            <details>
            <summary>📋 Full Traceback</summary>

            ```
            {traceback.format_exc()}
            ```
            </details>

            **Feedback Details:**
            - Message ID: `{processing_response["candidate_message"]["message_id"]}`
            - Customer Responded: {customer_responded.value}
            - Quality Score: {quality_score.value}
            - Response Time: {response_time.value} minutes
            """)
            feedback = None
            feedback_response = None
    else:
        if processing_response is None:
            feedback_result = mo.md("❗ Complete message processing first, then click the button above to submit feedback.")
        else:
            feedback_result = mo.md("👆 Click the button above to submit feedback.")
        feedback = None
        feedback_response = None

    # Display result
    feedback_result
    return feedback, feedback_response, feedback_result


@app.cell
def __(mo):
    mo.md(
        """
        ## 🎉 Workflow Complete!

        Congratulations! You've successfully completed the full Apala API workflow:

        1. ✅ **Authentication** - Obtained JWT tokens
        2. ✅ **Message Processing** - Processed customer messages and candidate response
        3. ✅ **Message Optimization** - Enhanced message for better engagement
        4. ✅ **Feedback Submission** - Provided performance feedback

        ## Next Steps

        ### Production Integration

        To integrate this into your production system:

        1. **Install the package**: `pip install apala-api`
        2. **Set environment variables**:
           ```bash
           export APALA_API_KEY="your-api-key"
           export APALA_BASE_URL="https://your-server.com"
           export APALA_COMPANY_GUID="your-company-uuid"
           ```
        3. **Implement error handling** and retries for production reliability
        4. **Set up monitoring** to track API usage and performance

        ### Code Example

        ```python
        from apala_client import ApalaClient
        from apala_client.models import Message, MessageFeedback

        # Initialize client
        client = ApalaClient(api_key="your-api-key")

        # Authenticate
        client.authenticate()

        # Process messages
        response = client.message_process(
            message_history=messages,
            candidate_message=candidate,
            customer_id=customer_id,
            zip_code=zip_code,
            company_guid=company_guid
        )

        # Submit feedback after customer interaction
        feedback = MessageFeedback(
            original_message_id=response["candidate_message"]["message_id"],
            sent_message_content=response["candidate_message"]["content"],
            customer_responded=True,
            quality_score=85,
            time_to_respond_ms=1800000
        )
        client.submit_single_feedback(feedback)
        ```

        ## Additional Features

        - **Batch Processing**: Process multiple message conversations
        - **Async Support**: Use `httpx` for async operations
        - **Custom Session Configuration**: Configure timeouts and retries
        - **Rate Limiting**: Respect API rate limits
        - **Monitoring**: Track usage and performance metrics

        Happy coding! 🚀
        """
    )
    return


if __name__ == "__main__":
    app.run()
