# ============================================================
# models.py — Rwanda Cost-of-Living Navigator
# ============================================================
# This file defines the data structures (shapes) of everything
# the API receives from the frontend and sends back.
#
# Think of it like defining the form fields:
# - What information does the user send us? (Input models)
# - What information do we send back? (Output models)
#
# We use Pydantic — a Python library that automatically
# checks that data has the right type and format before
# the API processes it. If a user sends text where we
# expect a number, Pydantic catches it immediately.
# ============================================================

from pydantic import BaseModel, Field
from typing import Optional, List


# ============================================================
# INPUT MODELS — what the frontend sends to the backend
# ============================================================

class HouseholdSpending(BaseModel):
    """
    The spending information a user enters in the
    Personal tier calculator.
    All amounts are in Rwandan Francs (RWF) per month.
    All fields are optional — if not provided, defaults to 0.
    """

    # Monthly income
    monthly_income: float = Field(
        default=0,
        description="Total monthly household income in RWF",
        example=150000
    )

    # The 12 CPI spending categories
    food: float = Field(
        default=0,
        description="Monthly spending on food and groceries in RWF",
        example=55000
    )
    alcohol_tobacco: float = Field(
        default=0,
        description="Monthly spending on alcohol and tobacco in RWF",
        example=0
    )
    clothing: float = Field(
        default=0,
        description="Monthly spending on clothing and footwear in RWF",
        example=10000
    )
    housing: float = Field(
        default=0,
        description="Monthly spending on rent, electricity, water in RWF",
        example=40000
    )
    furnishing: float = Field(
        default=0,
        description="Monthly spending on household items in RWF",
        example=5000
    )
    health: float = Field(
        default=0,
        description="Monthly spending on health and medicine in RWF",
        example=10000
    )
    transport: float = Field(
        default=0,
        description="Monthly spending on transport in RWF",
        example=20000
    )
    communication: float = Field(
        default=0,
        description="Monthly spending on airtime and internet in RWF",
        example=3000
    )
    recreation: float = Field(
        default=0,
        description="Monthly spending on recreation in RWF",
        example=2000
    )
    education: float = Field(
        default=0,
        description="Monthly spending on education in RWF",
        example=8000
    )
    restaurants: float = Field(
        default=0,
        description="Monthly spending on eating out in RWF",
        example=0
    )
    miscellaneous: float = Field(
        default=0,
        description="Monthly spending on personal care and other items in RWF",
        example=5000
    )

    # User location — used to compare against district averages
    district: Optional[str] = Field(
        default=None,
        description="User's district — e.g. Nyarugenge, Gasabo",
        example="Gasabo"
    )
    area_type: Optional[str] = Field(
        default=None,
        description="Urban or Rural",
        example="Urban"
    )

    # Language preference
    language: Optional[str] = Field(
        default="en",
        description="Language for tips and labels — en or rw",
        example="en"
    )


class ProfileRequest(BaseModel):
    """
    Request to compare a household against a profile group.
    """
    profile_name: str = Field(
        description="Profile to compare against",
        example="Urban household"
    )


# ============================================================
# OUTPUT MODELS — what the backend sends back to the frontend
# ============================================================

class CategoryBreakdown(BaseModel):
    """
    Inflation breakdown for one spending category.
    Shown in the personal inflation results.
    """
    cpi_code        : str    # e.g. "01"
    category_name   : str    # e.g. "Food and non-alcoholic beverages"
    amount_rwf      : float  # how much user spends on this category
    share_pct       : float  # what percentage of their budget this is
    yoy_inflation   : float  # how much this category rose this year
    contribution    : float  # how much this adds to personal inflation
    trend           : str    # Rising, Stable, or Falling
    monthly_extra   : float  # extra RWF this costs vs last year


class PersonalInflationResult(BaseModel):
    """
    The complete result returned to the Personal tier.
    Contains the user's personal inflation rate and breakdown.
    """
    personal_inflation_rate : float  # e.g. 16.7
    national_average        : float  # e.g. 15.9
    difference_from_national: float  # e.g. +0.8
    total_monthly_spend     : float  # total RWF spent
    monthly_extra_cost      : float  # extra RWF due to inflation
    annual_extra_cost       : float  # extra RWF per year
    biggest_pressure        : str    # category hitting hardest
    biggest_pressure_extra  : float  # extra RWF from that category
    breakdown               : List[CategoryBreakdown]
    data_month              : str    # e.g. "August 2026"


class BudgetingTip(BaseModel):
    """
    One practical budgeting tip for a spending category.
    """
    cpi_code    : str  # which category this tip is for
    category    : str  # category name
    rank        : int  # 1 = biggest pressure, 2 = second, etc.
    tip         : str  # practical advice
    challenge   : str  # monthly challenge
    saving_tip  : str  # saving opportunity
    local_tip   : str  # Rwanda-specific advice


class WhatChangedItem(BaseModel):
    """
    One category in the 'What changed this month?' section.
    """
    category_name : str    # e.g. "Transport"
    yoy_pct       : float  # year on year change
    mom_pct       : float  # month on month change
    status        : str    # Rising, Stable, or Falling
    weight_pct    : float  # share of national basket


class WhatChangedResult(BaseModel):
    """
    The complete 'What changed this month?' result.
    """
    data_month : str
    rising     : List[WhatChangedItem]
    stable     : List[WhatChangedItem]
    falling    : List[WhatChangedItem]


class ProfileComparison(BaseModel):
    """
    How a user's inflation compares to a profile group.
    """
    user_inflation      : float
    profile_name        : str
    profile_inflation   : float
    difference          : float
    direction           : str   # "above" or "below"


class ForecastItem(BaseModel):
    """
    Short-term inflation forecast for one category.
    """
    cpi_code            : str
    category_name       : str
    current_yoy         : float
    forecast_month_1    : float   # projected MoM change next month
    forecast_month_2    : float   # month after
    forecast_month_3    : float   # month after that
    trend               : str     # Rising, Stable, Falling
    confidence_range    : float   # uncertainty band
    is_estimate         : bool    # always True — label clearly


class DistrictPressureItem(BaseModel):
    """
    Cost-of-living pressure score for one district.
    Used in the Government tier map.
    """
    district        : str
    area_type       : str    # Urban or Rural
    pressure_index  : float  # weighted inflation score
    risk_level      : str    # High, Medium, or Lower
    household_count : int    # households represented


class VulnerabilityScore(BaseModel):
    """
    Inflation vulnerability for one income group.
    """
    quintile        : str    # Q1 to Q5
    label           : str    # e.g. "Poorest 20%"
    inflation_rate  : float
    vulnerability   : str    # High, Medium, or Lower
    household_count : int
