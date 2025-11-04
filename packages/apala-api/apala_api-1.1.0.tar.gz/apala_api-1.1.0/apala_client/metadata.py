# Copyright (c) 2025 Apala Cap. All rights reserved.
# This software is proprietary and confidential.

"""
Optional metadata models for message optimization.

These models provide type-safe metadata that can enhance message personalization
based on customer demographics and financial information.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CreditScoreBin(str, Enum):
    """Binned credit score ranges."""

    SCORE_500_550 = "SCORE_500_550"
    SCORE_550_600 = "SCORE_550_600"
    SCORE_600_650 = "SCORE_600_650"
    SCORE_650_700 = "SCORE_650_700"
    SCORE_700_750 = "SCORE_700_750"
    SCORE_750_800 = "SCORE_750_800"
    SCORE_800_PLUS = "SCORE_800_PLUS"
    UNKNOWN = "UNKNOWN"


class LoanAmountBin(str, Enum):
    """Binned loan amount ranges."""

    AMOUNT_0_500 = "AMOUNT_0_500"
    AMOUNT_500_1000 = "AMOUNT_500_1000"
    AMOUNT_1000_2000 = "AMOUNT_1000_2000"
    AMOUNT_2000_5000 = "AMOUNT_2000_5000"
    AMOUNT_5000_10000 = "AMOUNT_5000_10000"
    AMOUNT_10000_PLUS = "AMOUNT_10000_PLUS"


class AgeBin(str, Enum):
    """Binned age ranges."""

    AGE_18_25 = "AGE_18_25"
    AGE_25_30 = "AGE_25_30"
    AGE_30_35 = "AGE_30_35"
    AGE_35_40 = "AGE_35_40"
    AGE_40_45 = "AGE_40_45"
    AGE_45_50 = "AGE_45_50"
    AGE_50_55 = "AGE_50_55"
    AGE_55_60 = "AGE_55_60"
    AGE_60_PLUS = "AGE_60_PLUS"


class MonthlyIncomeBin(str, Enum):
    """Binned monthly income ranges."""

    INCOME_0_2000 = "INCOME_0_2000"
    INCOME_2000_3000 = "INCOME_2000_3000"
    INCOME_3000_4000 = "INCOME_3000_4000"
    INCOME_4000_5000 = "INCOME_4000_5000"
    INCOME_5000_6000 = "INCOME_5000_6000"
    INCOME_6000_8000 = "INCOME_6000_8000"
    INCOME_8000_10000 = "INCOME_8000_10000"
    INCOME_10000_PLUS = "INCOME_10000_PLUS"


class ApplicationReason(str, Enum):
    """Purpose of loan application."""

    DEBT_CONSOLIDATION = "DEBT_CONSOLIDATION"
    HOME_IMPROVEMENT = "HOME_IMPROVEMENT"
    MEDICAL_EMERGENCY = "MEDICAL_EMERGENCY"
    CAR_REPAIR = "CAR_REPAIR"
    MOVING_EXPENSES = "MOVING_EXPENSES"
    EDUCATION = "EDUCATION"
    BUSINESS_EXPENSES = "BUSINESS_EXPENSES"
    EMERGENCY_EXPENSES = "EMERGENCY_EXPENSES"
    VACATION = "VACATION"
    WEDDING = "WEDDING"
    OTHER = "OTHER"


class CustomerMetadata(BaseModel):
    """
    Optional customer metadata for enhanced message personalization.

    All fields are optional and can be used to provide additional context
    about the customer for more targeted message optimization.
    """

    is_repeat_borrower: Optional[int] = Field(
        None,
        description="Customer borrowing history: 0 = New borrower, 1 = Repeat borrower",
        ge=0,
        le=1
    )
    credit_score_bin: Optional[CreditScoreBin] = Field(
        None,
        description="Binned credit score range"
    )
    requested_loan_amount_bin: Optional[LoanAmountBin] = Field(
        None,
        description="Binned loan amount range"
    )
    state_id: Optional[int] = Field(
        None,
        description="Anonymized state identifier",
        ge=1
    )
    age_bin: Optional[AgeBin] = Field(
        None,
        description="Binned age range"
    )
    monthly_income_bin: Optional[MonthlyIncomeBin] = Field(
        None,
        description="Binned monthly income range"
    )
    application_reason: Optional[ApplicationReason] = Field(
        None,
        description="Purpose of loan application"
    )

    model_config = ConfigDict(use_enum_values=False)  # We'll handle enum conversion in to_dict()

    def to_dict(self):
        """
        Convert to dictionary, excluding None values.

        Returns:
            Dictionary with only non-None fields
        """
        return {
            k: v.value if isinstance(v, Enum) else v
            for k, v in self.model_dump(exclude_none=True).items()
        }
