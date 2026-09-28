# ============================================================
# business.py — Business Tier Router
# Rwanda Cost-of-Living Navigator
# ============================================================
# This file handles all API endpoints for Tier 2 — Business.
#
# Think of this as the business advisory desk.
# A shopkeeper, HR manager, or small business owner comes
# with questions about how rising costs are affecting their
# operations — and we give them data-driven answers.
#
# Endpoints in this file:
#   GET  /api/business/cost-pressure     — category cost trends
#   GET  /api/business/forecast          — 1-3 month forecast
#   GET  /api/business/what-changed      — what changed this month
#   POST /api/business/wage-signal       — wage review reference
# ============================================================

from fastapi import APIRouter, HTTPException
from typing import List, Optional
import pandas as pd

from app.models import (
    WhatChangedResult,
    WhatChangedItem,
    ForecastItem,
)
from app.config import NATIONAL_INFLATION_LATEST, LATEST_DATA_MONTH
from app.main import data_store

# Create the router
router = APIRouter()


# ============================================================
# ENDPOINT 1 — Cost Pressure by Category
# ============================================================
@router.get(
    "/cost-pressure",
    summary     = "Get cost pressure trends for all categories",
    description = """
    Returns all 12 spending categories with their current
    year-on-year and month-on-month inflation rates.
    Sorted from highest to lowest pressure so business owners
    can immediately see which costs are rising fastest.

    Example use: A restaurant owner wants to know which of
    their input costs — food, utilities, transport — is
    rising fastest so they can adjust their budget.
    """
)
def get_cost_pressure():
    """
    Return all categories sorted by cost pressure — highest first.
    This is the main view for the Business tier dashboard.
    """

    if "cpi_latest" not in data_store:
        raise HTTPException(
            status_code = 503,
            detail      = "CPI data not loaded — please try again shortly"
        )

    df_cpi = data_store["cpi_latest"].copy()

    # Keep only the 12 main categories
    df_cpi = df_cpi[
        (df_cpi["COICOP"].astype(str).str.len() == 2) &
        (df_cpi["COICOP"].astype(str) != "00")
    ].copy()

    # Sort by YoY inflation — highest pressure first
    df_cpi = df_cpi.sort_values("YoY_pct", ascending=False)

    # Build the response — one entry per category
    categories = []
    for _, row in df_cpi.iterrows():

        mom = float(row["MoM_pct"]) if pd.notna(row["MoM_pct"]) else 0

        # Assign pressure level label
        yoy = float(row["YoY_pct"])
        if yoy >= 20:
            pressure_level = "Very High"
        elif yoy >= 15:
            pressure_level = "High"
        elif yoy >= 10:
            pressure_level = "Medium"
        else:
            pressure_level = "Lower"

        # Assign trend based on month-on-month change
        if mom > 0.5:
            trend = "Rising"
        elif mom < -0.5:
            trend = "Falling"
        else:
            trend = "Stable"

        categories.append({
            "cpi_code"       : str(row["COICOP"]),
            "category_name"  : str(row["Category_Name"]),
            "yoy_pct"        : round(yoy, 2),
            "mom_pct"        : round(mom, 2),
            "pressure_level" : pressure_level,
            "trend"          : trend,
            "weight_pct"     : round(float(row["Weight_pct"]), 2),
            "data_month"     : LATEST_DATA_MONTH,
            "note"           : "Based on NISR CPI data — model estimate only"
        })

    return {
        "data_month"         : LATEST_DATA_MONTH,
        "national_inflation" : NATIONAL_INFLATION_LATEST,
        "categories"         : categories,
        "note"               : (
            "Year-on-year rates compare August 2026 to August 2025. "
            "Month-on-month rates compare August 2026 to July 2026. "
            "Source: NISR Consumer Price Index."
        )
    }


# ============================================================
# ENDPOINT 2 — Short-Term Cost Forecast
# ============================================================
@router.get(
    "/forecast",
    summary     = "Get 1-3 month inflation forecast by category",
    description = """
    Returns projected month-on-month inflation changes for
    September, October, and November 2026 for all 12 categories.

    Method: Weighted moving average of the last 6 months of
    month-on-month changes — more weight given to recent months.

    IMPORTANT: These are model estimates only — not official
    NISR figures. Every forecast includes a confidence range
    showing the uncertainty band around the projection.

    Example use: A business owner planning their October budget
    wants to know whether transport costs are likely to keep
    rising or stabilize in the next 2 months.
    """
)
def get_forecast(category: Optional[str] = None):
    """
    Return the 1-3 month forecast for all categories
    or for one specific category if provided.

    Parameters:
        category: optional CPI code to filter — e.g. "01" for food
    """

    if "forecasts" not in data_store:
        raise HTTPException(
            status_code = 503,
            detail      = "Forecast data not loaded — please try again shortly"
        )

    df_forecasts = data_store["forecasts"].copy()

    # Filter to one category if requested
    if category:
        df_forecasts = df_forecasts[
            df_forecasts["cpi_code"].astype(str) == category
        ]
        if len(df_forecasts) == 0:
            raise HTTPException(
                status_code = 404,
                detail      = f"Category '{category}' not found. "
                              f"Use codes 01-12."
            )

    # Sort by current YoY — highest pressure first
    df_forecasts = df_forecasts.sort_values(
        "current_yoy", ascending=False
    )

    result = []
    for _, row in df_forecasts.iterrows():
        result.append(ForecastItem(
            cpi_code         = str(row["cpi_code"]),
            category_name    = str(row["category_name"]),
            current_yoy      = round(float(row["current_yoy"]), 2),
            forecast_month_1 = round(float(row["avg_mom_6m"]), 2),
            forecast_month_2 = round(
                float(row["avg_mom_6m"]) * 0.95, 2
            ),
            forecast_month_3 = round(
                float(row["avg_mom_6m"]) * 0.90, 2
            ),
            trend            = str(row["trend"]),
            confidence_range = round(
                float(row["confidence_range"]), 2
            ),
            is_estimate      = True,
        ))

    return {
        "forecast_months" : [
            "September 2026",
            "October 2026",
            "November 2026"
        ],
        "method"          : (
            "Weighted moving average of last 6 months "
            "of month-on-month changes"
        ),
        "forecasts"       : result,
        "warning"         : (
            "⚠ These are model estimates only — not official NISR "
            "figures. Forecasts carry uncertainty — see confidence_range "
            "for the margin of error around each projection."
        ),
        "data_source"     : "NISR Consumer Price Index — August 2026"
    }


# ============================================================
# ENDPOINT 3 — What Changed This Month (Business View)
# ============================================================
@router.get(
    "/what-changed",
    response_model = WhatChangedResult,
    summary        = "Get what changed in costs this month",
    description    = """
    Returns all 12 categories sorted into Rising, Stable,
    and Falling — framed for business cost planning rather
    than household budgeting.

    Same underlying data as the Personal tier but presented
    from a business cost perspective.
    """
)
def get_what_changed_business():
    """
    Classify all categories into Rising, Stable, or Falling
    based on month-on-month change — business framing.
    """

    if "cpi_latest" not in data_store:
        raise HTTPException(
            status_code = 503,
            detail      = "CPI data not loaded"
        )

    df_cpi = data_store["cpi_latest"].copy()
    df_cpi = df_cpi[
        (df_cpi["COICOP"].astype(str).str.len() == 2) &
        (df_cpi["COICOP"].astype(str) != "00")
    ].copy()

    rising  = []
    stable  = []
    falling = []

    for _, row in df_cpi.iterrows():

        mom = float(row["MoM_pct"]) if pd.notna(row["MoM_pct"]) else 0

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

    rising.sort(key  = lambda x: x.mom_pct, reverse=True)
    falling.sort(key = lambda x: x.mom_pct)

    return WhatChangedResult(
        data_month = LATEST_DATA_MONTH,
        rising     = rising,
        stable     = stable,
        falling    = falling,
    )


# ============================================================
# ENDPOINT 4 — Wage Review Signal
# ============================================================
@router.get(
    "/wage-signal",
    summary     = "Get objective wage review reference",
    description = """
    Returns an objective, data-driven signal for wage review
    conversations — based on actual NISR inflation data.

    Shows how much purchasing power has declined since a
    given date, giving HR teams and employers an honest
    reference point for salary adjustment discussions.

    Example use: An HR manager whose team had their last
    salary review in January 2025 wants to know how much
    purchasing power has declined since then.
    """
)
def get_wage_signal(since_month: Optional[str] = None):
    """
    Calculate how much purchasing power has declined
    since a given month using the CPI history.

    Parameters:
        since_month: month to compare from — format YYYY-MM
                     defaults to 12 months ago if not provided
    """

    if "cpi_history" not in data_store:
        raise HTTPException(
            status_code = 503,
            detail      = "CPI history not loaded"
        )

    df_history = data_store["cpi_history"].copy()

    # Get the general index only (COICOP = 00)
    df_general = df_history[
        df_history["COICOP"].astype(str) == "00"
    ].copy()

    df_general = df_general.sort_values("Date")

    # Get the latest month index value
    latest_row   = df_general.iloc[-1]
    latest_index = float(latest_row["CPI_Index"])
    latest_month = str(latest_row["YearMonth"])

    # Default: compare to 12 months ago
    if since_month is None:
        compare_row = df_general.iloc[-13]
    else:
        mask        = df_general["YearMonth"] == since_month
        compare_rows = df_general[mask]
        if len(compare_rows) == 0:
            raise HTTPException(
                status_code = 404,
                detail      = f"Month '{since_month}' not found in data. "
                              f"Use format YYYY-MM e.g. 2025-01"
            )
        compare_row = compare_rows.iloc[0]

    compare_index = float(compare_row["CPI_Index"])
    compare_month = str(compare_row["YearMonth"])

    # How much has purchasing power declined?
    # If CPI rose 15.9%, a salary that stayed the same
    # is now worth 13.7% less in real terms
    inflation_since    = round(
        (latest_index / compare_index - 1) * 100, 2
    )
    purchasing_power_loss = round(
        (1 - compare_index / latest_index) * 100, 2
    )

    return {
        "comparison_month"      : compare_month,
        "latest_month"          : latest_month,
        "inflation_since"       : inflation_since,
        "purchasing_power_loss" : purchasing_power_loss,
        "wage_signal"           : (
            f"A salary unchanged since {compare_month} has lost "
            f"{purchasing_power_loss}% of its purchasing power. "
            f"To maintain the same real value, it would need to "
            f"increase by {inflation_since}%."
        ),
        "note"                  : (
            "This is a general cost-of-living reference based on "
            "NISR national CPI data. Individual circumstances vary. "
            "This is not financial or legal advice."
        ),
        "data_source"           : "NISR Consumer Price Index"
    }
