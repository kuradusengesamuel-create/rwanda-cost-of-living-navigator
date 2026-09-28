# ============================================================
# personal.py — Personal Tier Router
# Rwanda Cost-of-Living Navigator
# ============================================================
# This file handles all API endpoints for Tier 1 — Personal.
#
# Think of this as the personal finance desk at a bank.
# The user comes with their income and spending information,
# and we give them back a clear picture of how inflation
# is affecting them personally — not just the national average.
#
# Endpoints in this file:
#   POST /api/personal/inflation     — personal inflation rate
#   GET  /api/personal/what-changed  — what changed this month
#   POST /api/personal/tips          — budgeting tips
#   POST /api/personal/compare       — compare to profiles
# ============================================================

from fastapi import APIRouter, HTTPException
from typing import List
import pandas as pd

from app.models import (
    HouseholdSpending,
    PersonalInflationResult,
    CategoryBreakdown,
    WhatChangedResult,
    WhatChangedItem,
    BudgetingTip,
    ProfileComparison,
)
from app.config import NATIONAL_INFLATION_LATEST, LATEST_DATA_MONTH
from app.main import data_store

# Create the router
# A router is like a department within the API building.
# All personal tier endpoints live here.
router = APIRouter()


# Helper: map user input fields to CPI codes
# This connects what the user typed to the official
# NISR category codes we use in our data
FIELD_TO_CPI = {
    "food"            : "01",
    "alcohol_tobacco" : "02",
    "clothing"        : "03",
    "housing"         : "04",
    "furnishing"      : "05",
    "health"          : "06",
    "transport"       : "07",
    "communication"   : "08",
    "recreation"      : "09",
    "education"       : "10",
    "restaurants"     : "11",
    "miscellaneous"   : "12",
}


# ============================================================
# ENDPOINT 1 — Personal Inflation Calculator
# ============================================================
@router.post(
    "/inflation",
    response_model = PersonalInflationResult,
    summary        = "Calculate personal inflation rate",
    description    = """
    Takes a household's monthly spending across all 12 categories
    and returns their personal inflation rate, the rate that
    reflects their actual spending pattern, not the national average.

    For example a family spending 50% on food will have a higher
    personal inflation rate than the national average because
    food is rising faster than most other categories.
    """
)
def calculate_personal_inflation(spending: HouseholdSpending):
    """
    Main calculation engine for the personal tier.

    Steps:
    1. Calculate each category's share of total spending
    2. Multiply each share by that category's inflation rate
    3. Sum all contributions to get personal inflation rate
    4. Identify the biggest pressure category
    5. Generate the spending breakdown for display
    """

    # Step 1: Get CPI inflation data
    if "cpi_latest" not in data_store:
        raise HTTPException(
            status_code = 503,
            detail      = "CPI data not loaded — please try again shortly"
        )

    df_cpi = data_store["cpi_latest"].copy()

    # Keep only the 12 main categories, not sub-items or total
    df_cpi = df_cpi[
        (df_cpi["COICOP"].astype(str).str.len() == 2) &
        (df_cpi["COICOP"].astype(str) != "00")
    ].copy()

    # Build a lookup dictionary: CPI code → YoY inflation rate
    # e.g. {"01": 16.7, "04": 19.9, "07": 27.5 ...}
    inflation_lookup = dict(
        zip(
            df_cpi["COICOP"].astype(str),
            df_cpi["YoY_pct"]
        )
    )

    # Build category name lookup: CPI code → readable name
    name_lookup = dict(
        zip(
            df_cpi["COICOP"].astype(str),
            df_cpi["Category_Name"]
        )
    )

    # Step 2: Calculate total spending
    spending_dict = spending.dict()
    total_spend   = sum(
        spending_dict[field]
        for field in FIELD_TO_CPI.keys()
        if spending_dict.get(field, 0) > 0
    )

    # If the user entered nothing, return a clear error
    if total_spend == 0:
        raise HTTPException(
            status_code = 400,
            detail      = "Please enter at least one spending amount"
        )

    # Step 3: Calculate contribution per category 
    breakdown      = []
    personal_rate  = 0.0

    for field, cpi_code in FIELD_TO_CPI.items():

        amount = spending_dict.get(field, 0)

        # Skip categories where the user spent nothing
        if amount <= 0:
            continue

        # What share of their total budget is this category?
        share_pct = (amount / total_spend) * 100

        # What is this category's inflation rate?
        yoy_inflation = inflation_lookup.get(cpi_code, 0)

        # How much does this category contribute to personal inflation?
        # Formula: contribution = (share / 100) × inflation_rate
        contribution = (share_pct / 100) * yoy_inflation

        # How much extra RWF is this costing per month?
        monthly_extra = amount * (yoy_inflation / 100)

        # What is the trend for this category?
        mom_pct = df_cpi[
            df_cpi["COICOP"].astype(str) == cpi_code
        ]["MoM_pct"].values

        if len(mom_pct) > 0:
            if mom_pct[0] > 0.5:
                trend = "Rising"
            elif mom_pct[0] < -0.5:
                trend = "Falling"
            else:
                trend = "Stable"
        else:
            trend = "Stable"

        # Add this category to the breakdown list
        breakdown.append(CategoryBreakdown(
            cpi_code      = cpi_code,
            category_name = name_lookup.get(cpi_code, field),
            amount_rwf    = round(amount, 0),
            share_pct     = round(share_pct, 2),
            yoy_inflation = round(yoy_inflation, 2),
            contribution  = round(contribution, 4),
            trend         = trend,
            monthly_extra = round(monthly_extra, 0),
        ))

        # Add this category's contribution to the total
        personal_rate += contribution

    # Step 4: Round and finalize the personal rate
    personal_rate = round(personal_rate, 2)
    national_avg  = NATIONAL_INFLATION_LATEST
    difference    = round(personal_rate - national_avg, 2)

    # Step 5: Sort breakdown by contribution (highest first) ─
    breakdown.sort(key=lambda x: x.contribution, reverse=True)

    # Step 6: Identify biggest pressure 
    biggest       = breakdown[0] if breakdown else None
    biggest_name  = biggest.category_name if biggest else "Unknown"
    biggest_extra = biggest.monthly_extra if biggest else 0

    # Step 7: Calculate total extra monthly cost
    monthly_extra_total = sum(b.monthly_extra for b in breakdown)
    annual_extra_total  = monthly_extra_total * 12

    return PersonalInflationResult(
        personal_inflation_rate  = personal_rate,
        national_average         = national_avg,
        difference_from_national = difference,
        total_monthly_spend      = round(total_spend, 0),
        monthly_extra_cost       = round(monthly_extra_total, 0),
        annual_extra_cost        = round(annual_extra_total, 0),
        biggest_pressure         = biggest_name,
        biggest_pressure_extra   = round(biggest_extra, 0),
        breakdown                = breakdown,
        data_month               = LATEST_DATA_MONTH,
    )


# ============================================================
# ENDPOINT 2 — What Changed This Month
# ============================================================
@router.get(
    "/what-changed",
    response_model = WhatChangedResult,
    summary        = "Get what changed in inflation this month",
    description    = """
    Returns all 12 spending categories sorted into three groups:
    Rising (prices went up this month), Stable (little change),
    and Falling (prices went down). Uses month-on-month change
    to show what happened specifically this month — not just
    the annual average.
    """
)
def get_what_changed():
    """
    Classify all categories into Rising, Stable, or Falling
    based on their month-on-month change this month.
    """

    if "cpi_latest" not in data_store:
        raise HTTPException(
            status_code = 503,
            detail      = "CPI data not loaded"
        )

    df_cpi = data_store["cpi_latest"].copy()

    # Keep only the 12 main categories
    df_cpi = df_cpi[
        (df_cpi["COICOP"].astype(str).str.len() == 2) &
        (df_cpi["COICOP"].astype(str) != "00")
    ].copy()

    rising  = []
    stable  = []
    falling = []

    for _, row in df_cpi.iterrows():

        # Determine status based on month-on-month change
        mom = row["MoM_pct"] if pd.notna(row["MoM_pct"]) else 0

        if mom > 0.5:
            status = "Rising"
        elif mom < -0.5:
            status = "Falling"
        else:
            status = "Stable"

        item = WhatChangedItem(
            category_name = str(row["Category_Name"]),
            yoy_pct       = round(float(row["YoY_pct"]), 2),
            mom_pct       = round(float(mom), 2),
            status        = status,
            weight_pct    = round(float(row["Weight_pct"]), 2),
        )

        if status == "Rising":
            rising.append(item)
        elif status == "Falling":
            falling.append(item)
        else:
            stable.append(item)

    # Sort each group by magnitude of change
    rising.sort(key  = lambda x: x.mom_pct, reverse=True)
    falling.sort(key = lambda x: x.mom_pct)

    return WhatChangedResult(
        data_month = LATEST_DATA_MONTH,
        rising     = rising,
        stable     = stable,
        falling    = falling,
    )


# ============================================================
# ENDPOINT 3 — Budgeting Tips
# ============================================================
@router.post(
    "/tips",
    response_model = List[BudgetingTip],
    summary        = "Get personalized budgeting tips",
    description    = """
    Takes a household's spending data and returns practical,
    Rwanda-specific budgeting tips for their top 3 pressure
    categories. Tips mention real local markets, services,
    and options available in Rwanda.
    """
)
def get_budgeting_tips(spending: HouseholdSpending):
    """
    Generate tips for the top 3 pressure categories
    based on the user's spending pattern.
    """

    if "tips" not in data_store:
        raise HTTPException(
            status_code = 503,
            detail      = "Tips library not loaded"
        )

    if "cpi_latest" not in data_store:
        raise HTTPException(
            status_code = 503,
            detail      = "CPI data not loaded"
        )

    # Calculate spending shares
    spending_dict = spending.dict()
    total_spend   = sum(
        spending_dict[field]
        for field in FIELD_TO_CPI.keys()
        if spending_dict.get(field, 0) > 0
    )

    if total_spend == 0:
        raise HTTPException(
            status_code = 400,
            detail      = "Please enter at least one spending amount"
        )

    # Get CPI inflation rates
    df_cpi = data_store["cpi_latest"].copy()
    df_cpi = df_cpi[
        (df_cpi["COICOP"].astype(str).str.len() == 2) &
        (df_cpi["COICOP"].astype(str) != "00")
    ]
    inflation_lookup = dict(
        zip(df_cpi["COICOP"].astype(str), df_cpi["YoY_pct"])
    )

    # Calculate contribution per category
    contributions = []
    for field, cpi_code in FIELD_TO_CPI.items():
        amount = spending_dict.get(field, 0)
        if amount <= 0:
            continue
        share       = (amount / total_spend) * 100
        inflation   = inflation_lookup.get(cpi_code, 0)
        contribution = (share / 100) * inflation
        contributions.append((field, cpi_code, contribution))

    # Sort by contribution and take top 3
    contributions.sort(key=lambda x: x[2], reverse=True)
    top_3 = contributions[:3]

    # Get tips for each top category
    tips_library = data_store["tips"]
    result       = []

    for rank, (field, cpi_code, _) in enumerate(top_3, 1):
        if cpi_code in tips_library:
            tip_data = tips_library[cpi_code]
            result.append(BudgetingTip(
                cpi_code   = cpi_code,
                category   = field,
                rank       = rank,
                tip        = tip_data.get("tip", ""),
                challenge  = tip_data.get("challenge", ""),
                saving_tip = tip_data.get("saving_tip", ""),
                local_tip  = tip_data.get("local_tip", ""),
            ))

    return result


# ============================================================
# ENDPOINT 4 — Profile Comparison
# ============================================================
@router.post(
    "/compare",
    response_model = List[ProfileComparison],
    summary        = "Compare household inflation to profile groups",
    description    = """
    Compares the user's personal inflation rate against
    four typical Rwandan household profiles derived from
    EICV7 survey data:
    - Low income urban (Q1-Q2, urban)
    - Middle income (Q2-Q3, all areas)
    - Urban household (all quintiles, urban)
    - Rural household (all quintiles, rural)
    """
)
def compare_to_profiles(spending: HouseholdSpending):
    """
    Calculate the user's personal rate and compare it
    to all available profile benchmarks.
    """

    if "profiles" not in data_store:
        raise HTTPException(
            status_code = 503,
            detail      = "Profile benchmarks not loaded"
        )

    # First calculate the user's personal inflation rate
    personal_result = calculate_personal_inflation(spending)
    user_rate       = personal_result.personal_inflation_rate

    # Compare against each profile
    profiles = data_store["profiles"]
    result   = []

    for profile_name, profile_data in profiles.items():
        profile_rate = profile_data["inflation_rate"]
        difference   = round(user_rate - profile_rate, 2)
        direction    = "above" if difference > 0 else "below"

        result.append(ProfileComparison(
            user_inflation    = user_rate,
            profile_name      = profile_name,
            profile_inflation = profile_rate,
            difference        = abs(difference),
            direction         = direction,
        ))

    return result
