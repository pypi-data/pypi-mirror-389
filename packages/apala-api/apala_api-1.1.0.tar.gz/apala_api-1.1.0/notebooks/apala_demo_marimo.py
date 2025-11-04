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
    from typing import Any, Dict

    # Add parent directory to path to import our client
    sys.path.append("..")

    from apala_client import (
        ApalaClient,
        CustomerMetadata,
        CreditScoreBin,
        LoanAmountBin,
        AgeBin,
        MonthlyIncomeBin,
        ApplicationReason,
        Message,
    )

    mo.md(
        """
        # 🚀 Apala API Interactive Demo

        Welcome to the comprehensive demonstration of the Apala API Python SDK!

        This notebook provides:
        - **Interactive Forms** for each API step
        - **Code Examples** showing exactly how to use the SDK
        - **Complete Flow Example** at the bottom for quick integration

        ## Workflow Steps:

        1. 🔐 **Authentication** - Get API access
        2. 📝 **Create Messages** - Build message history
        3. 🎯 **Optimize Messages** - Enhance for engagement (with optional metadata)
        4. 📊 **Submit Feedback** - Track performance
        5. 🔄 **Complete Flow** - End-to-end example

        Let's get started!
        """
    )
    return (
        AgeBin,
        ApalaClient,
        ApplicationReason,
        CreditScoreBin,
        CustomerMetadata,
        LoanAmountBin,
        Message,
        MonthlyIncomeBin,
        mo,
        os,
        sys,
        uuid,
    )


# ============================================================================
# STEP 1: AUTHENTICATION
# ============================================================================

@app.cell
def __(mo):
    mo.md(
        """
        ## 🔐 Step 1: Authentication

        Exchange your API key for JWT tokens to access the service.

        ### 📋 Code Example:
        ```python
        from apala_client import ApalaClient

        # Initialize client
        client = ApalaClient(
            api_key="your-api-key",
            base_url="http://localhost:4000"  # or your production URL
        )

        # Authenticate to get JWT tokens
        auth_response = client.authenticate()

        print(f"Access token: {auth_response.access_token[:30]}...")
        print(f"Company: {auth_response.company_name}")
        ```
        """
    )
    return


@app.cell
def __(mo, os):
    # Authentication form
    mo.md("### 🔧 Configuration Form")
    return


@app.cell
def __(mo, os):
    api_key_input = mo.ui.text(
        placeholder="Enter your API key",
        value=os.getenv("APALA_API_KEY", "Oz4dD6DSeUJT3fxKIFXn8dsIsvLnL9QERnql2aiqz3k="),
        label="API Key",
        full_width=True
    )

    base_url_input = mo.ui.text(
        placeholder="https://your-phoenix-server.com",
        value=os.getenv("APALA_BASE_URL", "http://localhost:4000"),
        label="Server URL",
        full_width=True
    )

    company_guid_input = mo.ui.text(
        placeholder="your-company-uuid",
        value=os.getenv("APALA_COMPANY_GUID", "0b4794d6-db0a-463b-acf6-7056d33b8f3a"),
        label="Company GUID",
        full_width=True
    )

    customer_id_input = mo.ui.text(
        placeholder="customer-uuid",
        value="550e8400-e29b-41d4-a716-446655440000",
        label="Customer ID",
        full_width=True
    )

    zip_code_input = mo.ui.text(
        placeholder="90210",
        value="90210",
        label="Zip Code (5 digits)",
        full_width=True
    )

    auth_button = mo.ui.run_button(label="🔐 Authenticate")

    mo.vstack([
        api_key_input,
        base_url_input,
        company_guid_input,
        mo.md("---"),
        mo.md("**Customer Information (for later steps):**"),
        customer_id_input,
        zip_code_input,
        mo.md("---"),
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
def __(ApalaClient, api_key_input, auth_button, base_url_input, mo):
    # Authentication execution
    if auth_button.value:
        try:
            client = ApalaClient(
                api_key=api_key_input.value,
                base_url=base_url_input.value
            )
            auth_response = client.authenticate()

            auth_result = mo.md(f"""
            ✅ **Authentication Successful!**

            - Company: **{auth_response.company_name}**
            - Company ID: `{auth_response.company_id}`
            - Token Type: `{auth_response.token_type}`
            - Expires in: {auth_response.expires_in} seconds

            ### 🔑 JWT Tokens

            **Access Token:**
            ```
            {auth_response.access_token}
            ```

            **Refresh Token:**
            ```
            {auth_response.refresh_token}
            ```

            <details>
            <summary>📋 Full Response JSON</summary>

            ```json
            {{
              "access_token": "{auth_response.access_token}",
              "refresh_token": "{auth_response.refresh_token}",
              "token_type": "{auth_response.token_type}",
              "expires_in": {auth_response.expires_in},
              "company_id": "{auth_response.company_id}",
              "company_name": "{auth_response.company_name}"
            }}
            ```
            </details>
            """)
        except Exception as e:
            client = None
            auth_response = None
            auth_result = mo.md(f"""
            ❌ **Authentication Failed**

            Error: `{str(e)}`

            Please check your API key and server URL.
            """)
    else:
        client = None
        auth_response = None
        auth_result = mo.md("👆 Click the button above to authenticate.")

    auth_result
    return auth_response, auth_result, client


# ============================================================================
# STEP 2: CREATE MESSAGES
# ============================================================================

@app.cell
def __(mo):
    mo.md(
        """
        ## 📝 Step 2: Create Message History

        Build a conversation history with customer messages and your candidate response.

        ### 📋 Code Example:
        ```python
        from apala_client import Message

        # Customer messages (incoming)
        messages = [
            Message(
                content="Hi, I need a loan for home improvement",
                channel="SMS",
                reply_or_not=False  # Customer's initial message
            ),
            Message(
                content="What are the interest rates?",
                channel="SMS",
                reply_or_not=True  # Customer is replying to your previous message
            )
        ]

        # Your candidate response (outgoing)
        candidate = Message(
            content="Thank you for your interest! Our rates start at 3.5% APR.",
            channel="SMS",
            reply_or_not=True  # You are replying to customer
        )
        ```

        ### Available Options:
        - **channel**: `"SMS"`, `"EMAIL"`, or `"OTHER"`
        - **reply_or_not**: `True` if this is a reply, `False` if it's an initial/outbound message
        - **message_id**: Auto-generated if not provided
        - **send_timestamp**: Auto-generated if not provided
        """
    )
    return


@app.cell
def __(mo):
    mo.md("### 🔧 Message Creation Form")
    return


@app.cell
def __(mo):
    # Message 1 form
    msg1_content = mo.ui.text_area(
        value="Hi, I'm interested in refinancing my mortgage. My current rate is 4.5%.",
        label="Customer Message 1",
        full_width=True
    )

    msg1_channel = mo.ui.dropdown(
        options=["SMS", "EMAIL", "OTHER"],
        value="EMAIL",
        label="Channel"
    )

    msg1_is_reply = mo.ui.checkbox(
        value=False,
        label="Is this a reply? (True = reply, False = initial message)"
    )

    mo.vstack([
        mo.md("**Message 1:**"),
        msg1_content,
        mo.hstack([msg1_channel, msg1_is_reply], justify="start"),
    ])
    return msg1_channel, msg1_content, msg1_is_reply


@app.cell
def __(mo):
    # Message 2 form
    msg2_content = mo.ui.text_area(
        value="What documents do I need and how long does it take?",
        label="Customer Message 2",
        full_width=True
    )

    msg2_channel = mo.ui.dropdown(
        options=["SMS", "EMAIL", "OTHER"],
        value="EMAIL",
        label="Channel"
    )

    msg2_is_reply = mo.ui.checkbox(
        value=True,
        label="Is this a reply?"
    )

    mo.vstack([
        mo.md("**Message 2:**"),
        msg2_content,
        mo.hstack([msg2_channel, msg2_is_reply], justify="start"),
    ])
    return msg2_channel, msg2_content, msg2_is_reply


@app.cell
def __(mo):
    # Candidate message form
    candidate_content = mo.ui.text_area(
        value="Thank you for your interest! With excellent credit, you could qualify for rates as low as 3.1%. You'll need pay stubs, tax returns, and bank statements. The process takes 30-45 days.",
        label="Your Candidate Response",
        full_width=True
    )

    candidate_channel = mo.ui.dropdown(
        options=["SMS", "EMAIL", "OTHER"],
        value="EMAIL",
        label="Channel"
    )

    candidate_is_reply = mo.ui.checkbox(
        value=True,
        label="Is this a reply?"
    )

    create_messages_button = mo.ui.run_button(label="📝 Create Messages")

    mo.vstack([
        mo.md("**Your Candidate Response:**"),
        candidate_content,
        mo.hstack([candidate_channel, candidate_is_reply], justify="start"),
        mo.md("---"),
        create_messages_button
    ])
    return (
        candidate_channel,
        candidate_content,
        candidate_is_reply,
        create_messages_button,
    )


@app.cell
def __(
    Message,
    candidate_channel,
    candidate_content,
    candidate_is_reply,
    create_messages_button,
    mo,
    msg1_channel,
    msg1_content,
    msg1_is_reply,
    msg2_channel,
    msg2_content,
    msg2_is_reply,
):
    # Create message objects
    if create_messages_button.value:
        messages = [
            Message(
                content=msg1_content.value,
                channel=msg1_channel.value,
                reply_or_not=msg1_is_reply.value
            ),
            Message(
                content=msg2_content.value,
                channel=msg2_channel.value,
                reply_or_not=msg2_is_reply.value
            )
        ]

        candidate = Message(
            content=candidate_content.value,
            channel=candidate_channel.value,
            reply_or_not=candidate_is_reply.value
        )

        messages_result = mo.md(f"""
        ✅ **Messages Created!**

        - Created {len(messages)} customer message(s)
        - Created 1 candidate response
        - Message IDs auto-generated
        - Timestamps auto-generated

        Ready for optimization!
        """)
    else:
        messages = None
        candidate = None
        messages_result = mo.md("👆 Click the button above to create messages.")

    messages_result
    return candidate, messages, messages_result


# ============================================================================
# STEP 3: OPTIMIZE MESSAGE (with optional metadata)
# ============================================================================

@app.cell
def __(mo):
    mo.md(
        """
        ## 🎯 Step 3: Optimize Message

        Enhance your message for maximum customer engagement. Optionally provide customer metadata for better personalization.

        ### 📋 Code Example (Basic):
        ```python
        # Basic optimization (no metadata)
        optimization = client.optimize_message(
            message_history=messages,
            candidate_message=candidate,
            customer_id="550e8400-e29b-41d4-a716-446655440000",
            zip_code="90210",
            company_guid="550e8400-e29b-41d4-a716-446655440001"
        )

        print(f"Optimized: {optimization.optimized_message}")
        print(f"Channel: {optimization.recommended_channel}")
        print(f"Message ID: {optimization.message_id}")
        ```

        ### 📋 Code Example (With Metadata):
        ```python
        from apala_client import CustomerMetadata, CreditScoreBin, ApplicationReason

        # Create metadata for enhanced personalization
        metadata = CustomerMetadata(
            is_repeat_borrower=1,
            credit_score_bin=CreditScoreBin.SCORE_650_700,
            age_bin=AgeBin.AGE_30_35,
            application_reason=ApplicationReason.HOME_IMPROVEMENT
        )

        # Optimize with metadata
        optimization = client.optimize_message(
            message_history=messages,
            candidate_message=candidate,
            customer_id=customer_id,
            zip_code=zip_code,
            company_guid=company_guid,
            metadata=metadata  # Optional: for better personalization
        )
        ```

        ### Optional Metadata Fields:
        - **is_repeat_borrower**: 0 (new) or 1 (repeat)
        - **credit_score_bin**: Score ranges (500-550, 550-600, etc.)
        - **requested_loan_amount_bin**: Amount ranges
        - **age_bin**: Age ranges (18-25, 25-30, etc.)
        - **monthly_income_bin**: Income ranges
        - **application_reason**: Loan purpose
        - **state_id**: Anonymized state identifier
        """
    )
    return


@app.cell
def __(mo):
    mo.md("### 🔧 Optimization Form")
    return


@app.cell
def __(mo):
    # Metadata toggle
    use_metadata_opt = mo.ui.checkbox(
        value=True,
        label="📊 Use Customer Metadata (Enhanced Personalization)"
    )

    mo.vstack([use_metadata_opt])
    return (use_metadata_opt,)


@app.cell
def __(
    AgeBin,
    ApplicationReason,
    CreditScoreBin,
    LoanAmountBin,
    MonthlyIncomeBin,
    mo,
    use_metadata_opt,
):
    # Metadata form (conditional)
    if use_metadata_opt.value:
        is_repeat_borrower_opt = mo.ui.dropdown(
            options={"New Borrower": 0, "Repeat Borrower": 1},
            value="Repeat Borrower",  # Use the key, not the value
            label="Customer Type"
        )

        credit_score_bin_opt = mo.ui.dropdown(
            options={
                "500-550": CreditScoreBin.SCORE_500_550,
                "550-600": CreditScoreBin.SCORE_550_600,
                "600-650": CreditScoreBin.SCORE_600_650,
                "650-700": CreditScoreBin.SCORE_650_700,
                "700-750": CreditScoreBin.SCORE_700_750,
                "750-800": CreditScoreBin.SCORE_750_800,
                "800+": CreditScoreBin.SCORE_800_PLUS,
                "Unknown": CreditScoreBin.UNKNOWN,
            },
            value="650-700",  # Use the key, not the enum
            label="Credit Score Range"
        )

        loan_amount_bin_opt = mo.ui.dropdown(
            options={
                "$0-500": LoanAmountBin.AMOUNT_0_500,
                "$500-1,000": LoanAmountBin.AMOUNT_500_1000,
                "$1,000-2,000": LoanAmountBin.AMOUNT_1000_2000,
                "$2,000-5,000": LoanAmountBin.AMOUNT_2000_5000,
                "$5,000-10,000": LoanAmountBin.AMOUNT_5000_10000,
                "$10,000+": LoanAmountBin.AMOUNT_10000_PLUS,
            },
            value="$2,000-5,000",  # Use the key, not the enum
            label="Requested Loan Amount"
        )

        age_bin_opt = mo.ui.dropdown(
            options={
                "18-25": AgeBin.AGE_18_25,
                "25-30": AgeBin.AGE_25_30,
                "30-35": AgeBin.AGE_30_35,
                "35-40": AgeBin.AGE_35_40,
                "40-45": AgeBin.AGE_40_45,
                "45-50": AgeBin.AGE_45_50,
                "50-55": AgeBin.AGE_50_55,
                "55-60": AgeBin.AGE_55_60,
                "60+": AgeBin.AGE_60_PLUS,
            },
            value="30-35",  # Use the key, not the enum
            label="Age Range"
        )

        income_bin_opt = mo.ui.dropdown(
            options={
                "$0-2,000": MonthlyIncomeBin.INCOME_0_2000,
                "$2,000-3,000": MonthlyIncomeBin.INCOME_2000_3000,
                "$3,000-4,000": MonthlyIncomeBin.INCOME_3000_4000,
                "$4,000-5,000": MonthlyIncomeBin.INCOME_4000_5000,
                "$5,000-6,000": MonthlyIncomeBin.INCOME_5000_6000,
                "$6,000-8,000": MonthlyIncomeBin.INCOME_6000_8000,
                "$8,000-10,000": MonthlyIncomeBin.INCOME_8000_10000,
                "$10,000+": MonthlyIncomeBin.INCOME_10000_PLUS,
            },
            value="$4,000-5,000",  # Use the key, not the enum
            label="Monthly Income"
        )

        application_reason_opt = mo.ui.dropdown(
            options={
                "Debt Consolidation": ApplicationReason.DEBT_CONSOLIDATION,
                "Home Improvement": ApplicationReason.HOME_IMPROVEMENT,
                "Medical Emergency": ApplicationReason.MEDICAL_EMERGENCY,
                "Car Repair": ApplicationReason.CAR_REPAIR,
                "Moving Expenses": ApplicationReason.MOVING_EXPENSES,
                "Education": ApplicationReason.EDUCATION,
                "Business Expenses": ApplicationReason.BUSINESS_EXPENSES,
                "Emergency Expenses": ApplicationReason.EMERGENCY_EXPENSES,
                "Vacation": ApplicationReason.VACATION,
                "Wedding": ApplicationReason.WEDDING,
                "Other": ApplicationReason.OTHER,
            },
            value="Home Improvement",  # Use the key, not the enum
            label="Application Reason"
        )

        state_id_opt = mo.ui.number(
            start=1,
            stop=50,
            value=5,
            label="State ID (1-50, optional)"
        )

        mo.vstack([
            mo.md("**Customer Metadata:**"),
            mo.hstack([is_repeat_borrower_opt, credit_score_bin_opt], justify="start"),
            mo.hstack([loan_amount_bin_opt, age_bin_opt], justify="start"),
            mo.hstack([income_bin_opt, application_reason_opt], justify="start"),
            state_id_opt,
        ])
    else:
        is_repeat_borrower_opt = None
        credit_score_bin_opt = None
        loan_amount_bin_opt = None
        age_bin_opt = None
        income_bin_opt = None
        application_reason_opt = None
        state_id_opt = None
        mo.md("*Metadata disabled - basic optimization will be used*")

    return (
        age_bin_opt,
        application_reason_opt,
        credit_score_bin_opt,
        income_bin_opt,
        is_repeat_borrower_opt,
        loan_amount_bin_opt,
        state_id_opt,
    )


@app.cell
def __(mo):
    optimize_button = mo.ui.run_button(label="🎯 Optimize Message")
    optimize_button
    return (optimize_button,)


@app.cell
def __(
    CustomerMetadata,
    age_bin_opt,
    application_reason_opt,
    candidate,
    client,
    company_guid_input,
    credit_score_bin_opt,
    customer_id_input,
    income_bin_opt,
    is_repeat_borrower_opt,
    loan_amount_bin_opt,
    messages,
    mo,
    optimize_button,
    state_id_opt,
    use_metadata_opt,
    zip_code_input,
):
    # Optimization execution
    if optimize_button.value and messages is not None and client is not None:
        try:
            # Build metadata if enabled
            customer_metadata = None
            if use_metadata_opt.value:
                customer_metadata = CustomerMetadata(
                    is_repeat_borrower=is_repeat_borrower_opt.value,
                    credit_score_bin=credit_score_bin_opt.value,
                    requested_loan_amount_bin=loan_amount_bin_opt.value,
                    age_bin=age_bin_opt.value,
                    monthly_income_bin=income_bin_opt.value,
                    application_reason=application_reason_opt.value,
                    state_id=state_id_opt.value if state_id_opt.value else None
                )

            optimization = client.optimize_message(
                message_history=messages,
                candidate_message=candidate,
                customer_id=customer_id_input.value,
                zip_code=zip_code_input.value,
                company_guid=company_guid_input.value,
                metadata=customer_metadata
            )

            metadata_info = ""
            if customer_metadata:
                metadata_info = f"""
**Metadata Used:**
- Customer Type: {"Repeat" if customer_metadata.is_repeat_borrower == 1 else "New"}
- Credit Score: {customer_metadata.credit_score_bin.value if customer_metadata.credit_score_bin else "N/A"}
- Loan Amount: {customer_metadata.requested_loan_amount_bin.value if customer_metadata.requested_loan_amount_bin else "N/A"}
- Age: {customer_metadata.age_bin.value if customer_metadata.age_bin else "N/A"}
- Income: {customer_metadata.monthly_income_bin.value if customer_metadata.monthly_income_bin else "N/A"}
- Reason: {customer_metadata.application_reason.value if customer_metadata.application_reason else "N/A"}
"""

            optimization_result = mo.md(f"""
✅ **Message Optimized!**

{metadata_info}

**Original Message:**
> {optimization.original_message}

**🎯 Optimized Message:**
> {optimization.optimized_message}

**Recommended Channel:** `{optimization.recommended_channel}`

**Message ID:** `{optimization.message_id}` (save this for feedback)

**Change:** {len(optimization.optimized_message) - len(optimization.original_message):+d} characters

<details>
<summary>📋 Full Response JSON</summary>

```json
{{
  "message_id": "{optimization.message_id}",
  "original_message": "{optimization.original_message}",
  "optimized_message": "{optimization.optimized_message}",
  "recommended_channel": "{optimization.recommended_channel}"
}}
```
</details>
            """)
        except Exception as e:
            import traceback
            optimization = None

            # Try to get response details if available
            error_details = ""
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_details = f"""
**HTTP Status:** {e.response.status_code}

**Response Body:**
```json
{e.response.text}
```
"""
                except:
                    error_details = f"**HTTP Status:** {getattr(e.response, 'status_code', 'unknown')}"

            optimization_result = mo.md(f"""
❌ **Optimization Failed**

**Error:** `{str(e)}`

{error_details}

<details>
<summary>🔍 Full Traceback</summary>

```
{traceback.format_exc()}
```
</details>

**Troubleshooting:**
- Make sure you've created messages and authenticated
- Check that customer_id and company_guid are valid UUIDs
- Verify zip_code is a 5-digit string
            """)
    else:
        optimization = None
        if client is None:
            optimization_result = mo.md("❗ Please authenticate first.")
        elif messages is None:
            optimization_result = mo.md("❗ Please create messages first.")
        else:
            optimization_result = mo.md("👆 Click the button above to optimize.")

    optimization_result
    return customer_metadata, optimization, optimization_result


# ============================================================================
# STEP 4: SUBMIT FEEDBACK
# ============================================================================

@app.cell
def __(mo):
    mo.md(
        """
        ## 📊 Step 4: Submit Feedback

        After sending the optimized message to your customer, track its performance.

        ### 📋 Code Example (Single):
        ```python
        # Submit feedback for a single message
        feedback = client.submit_single_feedback(
            message_id=optimization.message_id,
            customer_responded=True,
            score="good",  # "good", "bad", or "neutral"
            actual_sent_message=optimization.optimized_message  # Optional
        )

        print(f"Feedback ID: {feedback.id}")
        print(f"Submitted at: {feedback.inserted_at}")
        ```

        ### 📋 Code Example (Bulk):
        ```python
        # Submit feedback for multiple messages
        feedback_list = [
            {
                "message_id": "msg-uuid-1",
                "customer_responded": True,
                "score": "good",
                "actual_sent_message": "Hi! Ready to help."  # Optional
            },
            {
                "message_id": "msg-uuid-2",
                "customer_responded": False,
                "score": "neutral"
            }
        ]

        bulk_response = client.submit_feedback_bulk(feedback_list)
        print(f"Submitted {bulk_response.count} items")
        ```
        """
    )
    return


@app.cell
def __(mo):
    mo.md("### 🔧 Feedback Form")
    return


@app.cell
def __(mo):
    customer_responded_feedback = mo.ui.checkbox(
        value=True,
        label="Did the customer respond?"
    )

    quality_score_feedback = mo.ui.dropdown(
        options={
            "Good": "good",
            "Neutral": "neutral",
            "Bad": "bad",
        },
        value="Good",
        label="Quality Score"
    )

    include_actual_message = mo.ui.checkbox(
        value=True,
        label="Include actual sent message (recommended for tracking)"
    )

    submit_feedback_button = mo.ui.run_button(label="📊 Submit Feedback")

    mo.vstack([
        customer_responded_feedback,
        quality_score_feedback,
        include_actual_message,
        mo.md("---"),
        submit_feedback_button
    ])
    return (
        customer_responded_feedback,
        include_actual_message,
        quality_score_feedback,
        submit_feedback_button,
    )


@app.cell
def __(
    client,
    customer_responded_feedback,
    include_actual_message,
    mo,
    optimization,
    quality_score_feedback,
    submit_feedback_button,
):
    # Feedback execution
    if submit_feedback_button.value and optimization is not None and client is not None:
        try:
            actual_msg = optimization.optimized_message if include_actual_message.value else None

            feedback_response = client.submit_single_feedback(
                message_id=optimization.message_id,
                customer_responded=customer_responded_feedback.value,
                score=quality_score_feedback.value,
                actual_sent_message=actual_msg
            )

            feedback_result = mo.md(f"""
✅ **Feedback Submitted!**

- **Feedback ID:** `{feedback_response.id}`
- **Message ID:** `{feedback_response.message_id}`
- **Customer Responded:** {"Yes ✅" if feedback_response.customer_responded else "No ❌"}
- **Score:** {feedback_response.score}
- **Actual Message:** {(feedback_response.actual_sent_message or "N/A")[:50]}...
- **Submitted At:** {feedback_response.inserted_at}
            """)
        except Exception as e:
            feedback_response = None
            feedback_result = mo.md(f"""
❌ **Feedback Failed**

Error: `{str(e)}`
            """)
    else:
        feedback_response = None
        if client is None:
            feedback_result = mo.md("❗ Please authenticate first.")
        elif optimization is None:
            feedback_result = mo.md("❗ Please optimize a message first.")
        else:
            feedback_result = mo.md("👆 Click the button above to submit feedback.")

    feedback_result
    return feedback_response, feedback_result


# ============================================================================
# STEP 5: COMPLETE FLOW EXAMPLE
# ============================================================================

@app.cell
def __(mo):
    mo.md(
        """
        ---

        ## 🔄 Complete End-to-End Flow Example

        Here's a complete, production-ready example showing the full workflow:

        ```python
        from apala_client import (
            ApalaClient,
            Message,
            CustomerMetadata,
            CreditScoreBin,
            AgeBin,
            ApplicationReason
        )

        # ========================================
        # 1. INITIALIZE & AUTHENTICATE
        # ========================================
        client = ApalaClient(
            api_key="your-api-key",
            base_url="https://api.yourdomain.com"
        )

        auth_response = client.authenticate()
        print(f"✅ Authenticated as: {auth_response.company_name}")


        # ========================================
        # 2. CREATE MESSAGE HISTORY
        # ========================================
        # Customer messages
        messages = [
            Message(
                content="I need a $5,000 loan for home repairs",
                channel="SMS",
                reply_or_not=False  # Initial message
            ),
            Message(
                content="What's the interest rate?",
                channel="SMS",
                reply_or_not=True  # Replying to your previous message
            )
        ]

        # Your candidate response
        candidate = Message(
            content="Thank you for your interest. Our rates start at 3.5% APR for qualified borrowers.",
            channel="SMS",
            reply_or_not=True  # Replying to customer
        )


        # ========================================
        # 3. OPTIMIZE MESSAGE (with metadata)
        # ========================================
        # Optional: Create metadata for better personalization
        metadata = CustomerMetadata(
            is_repeat_borrower=1,  # Repeat customer
            credit_score_bin=CreditScoreBin.SCORE_700_750,
            age_bin=AgeBin.AGE_35_40,
            application_reason=ApplicationReason.HOME_IMPROVEMENT
        )

        optimization = client.optimize_message(
            message_history=messages,
            candidate_message=candidate,
            customer_id="550e8400-e29b-41d4-a716-446655440000",
            zip_code="90210",
            company_guid="550e8400-e29b-41d4-a716-446655440001",
            metadata=metadata  # Optional but recommended
        )

        print(f"Original: {optimization.original_message}")
        print(f"Optimized: {optimization.optimized_message}")
        print(f"Channel: {optimization.recommended_channel}")
        print(f"Message ID: {optimization.message_id}")


        # ========================================
        # 4. SEND MESSAGE TO CUSTOMER
        # ========================================
        # ... send optimization.optimized_message via your messaging system ...
        # ... using optimization.recommended_channel ...


        # ========================================
        # 5. SUBMIT FEEDBACK
        # ========================================
        # After sending and monitoring customer response
        feedback = client.submit_single_feedback(
            message_id=optimization.message_id,
            customer_responded=True,  # Customer replied
            score="good",  # "good", "bad", or "neutral"
            actual_sent_message=optimization.optimized_message  # What you actually sent
        )

        print(f"✅ Feedback submitted: {feedback.id}")


        # ========================================
        # BULK FEEDBACK (if you have multiple)
        # ========================================
        feedback_list = [
            {
                "message_id": "msg-uuid-1",
                "customer_responded": True,
                "score": "good",
                "actual_sent_message": "Custom message 1"
            },
            {
                "message_id": "msg-uuid-2",
                "customer_responded": False,
                "score": "neutral"
            }
        ]

        bulk_response = client.submit_feedback_bulk(feedback_list)
        print(f"✅ Submitted {bulk_response.count} feedback items")


        # ========================================
        # CLEANUP
        # ========================================
        client.close()
        ```

        ### 🎯 Integration Tips:

        1. **Store Message IDs**: Save `optimization.message_id` to link feedback later
        2. **Use Metadata**: Provide customer metadata for better personalization
        3. **Track Performance**: Submit feedback to improve the AI over time
        4. **Handle Errors**: Wrap calls in try/except for production
        5. **Token Management**: The client auto-refreshes JWT tokens
        6. **Bulk Operations**: Use bulk feedback for efficiency

        ### 🔒 Security Best Practices:

        - Store API keys in environment variables (never in code)
        - Use HTTPS in production (`base_url="https://..."`)
        - Implement rate limiting on your side
        - Monitor for unusual patterns
        - Rotate API keys periodically
        """
    )
    return


@app.cell
def __(mo):
    mo.md(
        """
        ---

        ## 🎉 You're Ready!

        You now have everything you need to integrate the Apala API into your application.

        ### Next Steps:

        1. **Install the SDK**: `pip install apala-api` (when published)
        2. **Get API Credentials**: Contact your Phoenix admin
        3. **Set Environment Variables**:
           ```bash
           export APALA_API_KEY="your-key"
           export APALA_BASE_URL="https://api.yourdomain.com"
           export APALA_COMPANY_GUID="your-company-guid"
           ```
        4. **Copy the Complete Flow Example** above into your application
        5. **Start Optimizing Messages**! 🚀

        ### 📚 Additional Resources:

        - [API Documentation](https://docs.yourdomain.com)
        - [SDK Source Code](https://github.com/yourdomain/apala-api)
        - Support: support@yourdomain.com

        Happy coding! 🎊
        """
    )
    return


if __name__ == "__main__":
    app.run()
