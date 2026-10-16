# ============================================================
# government.py — Government Tier Router
# Rwanda Cost-of-Living Navigator
# ============================================================
# This file handles all API endpoints for Tier 3 — Government.
#
# Think of this as the policy intelligence desk.
# Government planners, researchers, and social protection
# officers use this tier to understand where cost-of-living
# pressure is highest across Rwanda's 30 districts — so
# they can target interventions where they are needed most.
#
# All data shown here is aggregated and anonymized.
# No individual household data is ever exposed.
# District scores are derived from NISR EICV7 survey data
# combined with live CPI inflation rates.
#
# Endpoints in this file:
#   GET /api/government/district-index      — all 30 districts
#   GET /api/government/district/{name}     — one district detail
#   GET /api/government/vulnerability       — income group risk
#   GET /api/government/early-warnings      — threshold alerts
#   GET /api/government/summary             — national overview
# ============================================================

from fastapi import APIRouter, HTTPException
from typing import Optional
import pandas as pd

from app.models import (
    DistrictPressureItem,
    VulnerabilityScore,
)
from app.config import NATIONAL_INFLATION_LATEST, LATEST_DATA_MONTH
from app.main import data_store

# Create the router
router = APIRouter()

# Quintile labels
# Human-readable labels for each income quintile
QUINTILE_LABELS = {
    "Q1": "Poorest 20% of households",
    "Q2": "Lower middle income",
    "Q3": "Middle income",
    "Q4": "Upper middle income",
    "Q5": "Richest 20% of households",
}

# Early warning thresholds 
# When inflation in a district crosses these levels
# the platform raises an alert flag
HIGH_PRESSURE_THRESHOLD   = 14.0  # % — High risk
MEDIUM_PRESSURE_THRESHOLD = 10.0  # % — Medium risk
FOOD_ALERT_THRESHOLD      = 15.0  # % — Food-specific alert
TRANSPORT_ALERT_THRESHOLD = 25.0  # % — Transport-specific alert


# ============================================================
# ENDPOINT 1 — Full District Pressure Index
# ============================================================
@router.get(
    "/district-index",
    summary     = "Get cost-of-living pressure index for all districts",
    description = """
    Returns the cost-of-living pressure index for all 30 districts
    of Rwanda, split by Urban and Rural — giving 60 district-area
    combinations in total.

    The pressure index is calculated by combining:
    1. NISR CPI inflation rates by category (monthly, live)
    2. District-level spending basket weights from EICV7 (2023-2024)

    Formula:
    Pressure Index = Sum of (basket_share × category_inflation)
    for all 12 spending categories

    This gives a weighted inflation rate that reflects what
    households in that specific district actually spend on —
    not the national average basket.

    IMPORTANT: District scores are modelled estimates — not directly
    measured district CPI. See methodology documentation.
    """
)
def get_district_index(
    risk_level : Optional[str] = None,
    area_type  : Optional[str] = None,
    sort_by    : Optional[str] = "pressure_index"
):
    """
    Return the pressure index for all districts.

    Parameters:
        risk_level : filter by risk — High, Medium, or Lower
        area_type  : filter by area — Urban or Rural
        sort_by    : sort field — pressure_index or district
    """

    if "district_index" not in data_store:
        raise HTTPException(
            status_code = 503,
            detail      = "District index not loaded — please try again"
        )

    df = data_store["district_index"].copy()

    # Apply filters if requested
    if risk_level:
        df = df[df["risk_level"].str.lower() == risk_level.lower()]
        if len(df) == 0:
            raise HTTPException(
                status_code = 404,
                detail      = f"No districts found with risk level '{risk_level}'. "
                              f"Use: High, Medium, or Lower"
            )

    if area_type:
        df = df[df["ur"].str.lower() == area_type.lower()]
        if len(df) == 0:
            raise HTTPException(
                status_code = 404,
                detail      = f"No districts found for area type '{area_type}'. "
                              f"Use: Urban or Rural"
            )

    # Sort
    if sort_by == "district":
        df = df.sort_values("district")
    else:
        df = df.sort_values("pressure_index", ascending=False)

    # Build response
    districts = []
    for _, row in df.iterrows():
        districts.append({
            "district"        : str(row["district"]),
            "area_type"       : str(row["ur"]),
            "pressure_index"  : round(float(row["pressure_index"]), 2),
            "risk_level"      : str(row["risk_level"]),
            "household_count" : int(row["household_count"]),
        })

    # Summary counts 
    high_count   = len(df[df["risk_level"] == "High"])
    medium_count = len(df[df["risk_level"] == "Medium"])
    lower_count  = len(df[df["risk_level"] == "Lower"])

    return {
        "data_month"         : LATEST_DATA_MONTH,
        "national_average"   : NATIONAL_INFLATION_LATEST,
        "total_combinations" : len(districts),
        "summary"            : {
            "high_risk"   : high_count,
            "medium_risk" : medium_count,
            "lower_risk"  : lower_count,
        },
        "districts"          : districts,
        "methodology_note"   : (
            "District scores are modelled estimates combining NISR CPI "
            "category trends with EICV7 district spending basket weights. "
            "Scores represent estimated cost-of-living pressure relative "
            "to a 2024 baseline. Not directly measured district CPI."
        ),
        "data_source"        : (
            "NISR CPI August 2026 + NISR EICV7 2023-2024"
        )
    }


# ============================================================
# ENDPOINT 2 — Single District Detail
# ============================================================
@router.get(
    "/district/{district_name}",
    summary     = "Get detailed breakdown for one district",
    description = """
    Returns the full spending basket breakdown for one specific
    district — showing exactly which categories are driving
    cost-of-living pressure in that district.

    Example: Nyaruguru Urban has a pressure index of 21.1%
    This endpoint shows which spending categories in Nyaruguru
    contribute most to that score.

    IMPORTANT: Modelled estimates — not directly measured district CPI.
    """
)
def get_district_detail(
    district_name : str,
    area_type     : Optional[str] = None
):
    """
    Return the full category breakdown for one district.

    Parameters:
        district_name : name of the district — e.g. Nyarugenge
        area_type     : Urban or Rural — if not specified,
                        returns both
    """

    if "district_weights" not in data_store:
        raise HTTPException(
            status_code = 503,
            detail      = "District weights not loaded"
        )

    if "cpi_latest" not in data_store:
        raise HTTPException(
            status_code = 503,
            detail      = "CPI data not loaded"
        )

    df_weights = data_store["district_weights"].copy()
    df_cpi     = data_store["cpi_latest"].copy()

    # Filter to the requested district 
    df_district = df_weights[
        df_weights["district"].str.lower() == district_name.lower()
    ]

    if len(df_district) == 0:
        raise HTTPException(
            status_code = 404,
            detail      = f"District '{district_name}' not found. "
                          f"Check spelling — e.g. Nyarugenge, Gasabo, Huye"
        )

    # Filter by area type if requested 
    if area_type:
        df_district = df_district[
            df_district["ur"].str.lower() == area_type.lower()
        ]
        if len(df_district) == 0:
            raise HTTPException(
                status_code = 404,
                detail      = f"No {area_type} data found for {district_name}"
            )

    # Get CPI inflation rates
    df_cpi_main = df_cpi[
        (df_cpi["COICOP"].astype(str).str.len() == 2) &
        (df_cpi["COICOP"].astype(str) != "00")
    ].copy()

    inflation_lookup = dict(
        zip(df_cpi_main["COICOP"].astype(str), df_cpi_main["YoY_pct"])
    )

    # Build breakdown per area type 
    result = []
    for area in df_district["ur"].unique():

        df_area = df_district[df_district["ur"] == area].copy()
        df_area = df_area.sort_values(
            "basket_share_pct", ascending=False
        )

        # Calculate pressure index for this area
        pressure_index = 0
        categories     = []

        for _, row in df_area.iterrows():
            cpi_code    = str(row["cpi_code"])
            share       = float(row["basket_share_pct"])
            inflation   = inflation_lookup.get(cpi_code, 0)
            contribution = round((share / 100) * inflation, 4)
            pressure_index += contribution

            categories.append({
                "cpi_code"        : cpi_code,
                "category_name"   : str(row["cpi_category"]),
                "basket_share_pct": round(share, 2),
                "yoy_inflation"   : round(inflation, 2),
                "contribution"    : round(contribution, 2),
                "household_count" : int(row["household_count"]),
            })

        # Assign risk level
        pressure_index = round(pressure_index, 2)
        if pressure_index >= HIGH_PRESSURE_THRESHOLD:
            risk_level = "High"
        elif pressure_index >= MEDIUM_PRESSURE_THRESHOLD:
            risk_level = "Medium"
        else:
            risk_level = "Lower"

        result.append({
            "district"       : district_name.title(),
            "area_type"      : area,
            "pressure_index" : pressure_index,
            "risk_level"     : risk_level,
            "categories"     : categories,
            "note"           : (
                "Basket shares show what proportion of household "
                "spending goes to each category in this district. "
                "Contribution shows how much each category adds "
                "to the overall pressure index."
            )
        })

    return {
        "data_month"  : LATEST_DATA_MONTH,
        "district"    : district_name.title(),
        "breakdown"   : result,
        "data_source" : "NISR CPI August 2026 + NISR EICV7 2023-2024"
    }


# ============================================================
# ENDPOINT 3 — Income Group Vulnerability
# ============================================================
@router.get(
    "/vulnerability",
    summary     = "Get inflation vulnerability by income group",
    description = """
    Returns inflation pressure scores for each income quintile
    (Q1 to Q5) — showing how differently inflation affects
    poor versus wealthy households.

    Derived from EICV7 household spending patterns combined
    with current CPI inflation rates.

    Key finding: Q5 (richest) currently faces slightly higher
    inflation than Q1 (poorest) because they spend more on
    transport and communication — the two fastest-rising
    categories in August 2026.
    """
)
def get_vulnerability():
    """
    Return vulnerability scores for all 5 income quintiles.
    """

    if "vulnerability" not in data_store:
        raise HTTPException(
            status_code = 503,
            detail      = "Vulnerability scores not loaded"
        )

    vulnerability = data_store["vulnerability"]

    result = []
    for quintile, data in vulnerability.items():
        result.append({
            "quintile"        : quintile,
            "label"           : QUINTILE_LABELS.get(quintile, quintile),
            "inflation_rate"  : data["inflation_rate"],
            "vulnerability"   : data["vulnerability"],
            "household_count" : data["household_count"],
            "interpretation"  : (
                f"{quintile} households ({QUINTILE_LABELS.get(quintile, '')}) "
                f"face an estimated {data['inflation_rate']}% inflation rate "
                f"based on their typical spending patterns."
            )
        })

    return {
        "data_month"       : LATEST_DATA_MONTH,
        "national_average" : NATIONAL_INFLATION_LATEST,
        "quintiles"        : result,
        "methodology_note" : (
            "Quintile inflation rates are calculated by applying "
            "current CPI category inflation rates to the average "
            "spending basket of each income quintile, derived from "
            "NISR EICV7 2023-2024 household survey data."
        ),
        "data_source"      : (
            "NISR CPI August 2026 + NISR EICV7 2023-2024"
        )
    }


# ============================================================
# ENDPOINT 4 — Early Warning Flags
# ============================================================
@router.get(
    "/early-warnings",
    summary     = "Get early warning flags for high-pressure situations",
    description = """
    Returns active early warning flags — districts or categories
    where cost-of-living pressure has crossed alert thresholds.

    Thresholds:
    - District pressure index ≥ 14% → High risk flag
    - Food inflation ≥ 15% → Food pressure alert
    - Transport inflation ≥ 25% → Transport pressure alert

    These flags are designed to support proactive policy
    decisions — identifying where intervention is needed
    before pressure becomes a crisis.
    """
)
def get_early_warnings():
    """
    Generate active early warning flags based on current data.
    """

    warnings = []

    # District-level warnings 
    if "district_index" in data_store:
        df_districts = data_store["district_index"].copy()

        high_risk = df_districts[
            df_districts["pressure_index"] >= HIGH_PRESSURE_THRESHOLD
        ].sort_values("pressure_index", ascending=False)

        for _, row in high_risk.iterrows():
            warnings.append({
                "warning_type"  : "District High Pressure",
                "severity"      : "High",
                "district"      : str(row["district"]),
                "area_type"     : str(row["ur"]),
                "pressure_index": round(float(row["pressure_index"]), 2),
                "message"       : (
                    f"{row['district']} {row['ur']} has a cost-of-living "
                    f"pressure index of {row['pressure_index']:.1f}% — "
                    f"above the High risk threshold of "
                    f"{HIGH_PRESSURE_THRESHOLD}%."
                ),
                "recommended_action": (
                    "Consider targeting social protection programs "
                    "and food security interventions in this area."
                )
            })

    # Category-level warnings
    if "cpi_latest" in data_store:
        df_cpi = data_store["cpi_latest"].copy()
        df_cpi = df_cpi[
            (df_cpi["COICOP"].astype(str).str.len() == 2) &
            (df_cpi["COICOP"].astype(str) != "00")
        ]

        # Food warning
        food_row = df_cpi[df_cpi["COICOP"].astype(str) == "01"]
        if len(food_row) > 0:
            food_inflation = float(food_row["YoY_pct"].values[0])
            if food_inflation >= FOOD_ALERT_THRESHOLD:
                warnings.append({
                    "warning_type"  : "Food Inflation Alert",
                    "severity"      : "High",
                    "district"      : "National",
                    "area_type"     : "All",
                    "pressure_index": round(food_inflation, 2),
                    "message"       : (
                        f"Food inflation is at {food_inflation:.1f}% — "
                        f"above the alert threshold of "
                        f"{FOOD_ALERT_THRESHOLD}%. "
                        f"Food takes 39% of the average Rwandan "
                        f"household budget."
                    ),
                    "recommended_action": (
                        "Review food price stabilization measures. "
                        "Consider temporary relief for low-income "
                        "households most exposed to food price rises."
                    )
                })

        # Transport warning
        transport_row = df_cpi[df_cpi["COICOP"].astype(str) == "07"]
        if len(transport_row) > 0:
            transport_inflation = float(
                transport_row["YoY_pct"].values[0]
            )
            if transport_inflation >= TRANSPORT_ALERT_THRESHOLD:
                warnings.append({
                    "warning_type"  : "Transport Inflation Alert",
                    "severity"      : "High",
                    "district"      : "National",
                    "area_type"     : "All",
                    "pressure_index": round(transport_inflation, 2),
                    "message"       : (
                        f"Transport inflation is at "
                        f"{transport_inflation:.1f}% — "
                        f"above the alert threshold of "
                        f"{TRANSPORT_ALERT_THRESHOLD}%."
                    ),
                    "recommended_action": (
                        "Review public transport subsidies and "
                        "fuel pricing policy."
                    )
                })

    return {
        "data_month"    : LATEST_DATA_MONTH,
        "total_warnings": len(warnings),
        "warnings"      : warnings,
        "thresholds"    : {
            "high_pressure_district" : HIGH_PRESSURE_THRESHOLD,
            "food_alert"             : FOOD_ALERT_THRESHOLD,
            "transport_alert"        : TRANSPORT_ALERT_THRESHOLD,
        },
        "note"          : (
            "Early warnings are generated automatically from "
            "current NISR data. They are advisory signals — "
            "not official government assessments."
        )
    }


# ============================================================
# ENDPOINT 5 — National Summary
# ============================================================
@router.get(
    "/summary",
    summary     = "Get national cost-of-living summary",
    description = """
    Returns a high-level national summary — the key numbers
    a policy briefing would contain. Designed for quick
    reference by senior decision-makers who need the
    headline figures without detailed breakdowns.
    """
)
def get_national_summary():
    """
    Return the key national cost-of-living figures
    for the current month.
    """

    summary = {
        "data_month"         : LATEST_DATA_MONTH,
        "national_inflation" : NATIONAL_INFLATION_LATEST,
    }

    # Highest and lowest pressure districts
    if "district_index" in data_store:
        df = data_store["district_index"].copy()
        df = df.sort_values("pressure_index", ascending=False)

        summary["highest_pressure_district"] = {
            "district"       : str(df.iloc[0]["district"]),
            "area_type"      : str(df.iloc[0]["ur"]),
            "pressure_index" : round(float(df.iloc[0]["pressure_index"]), 2),
            "risk_level"     : str(df.iloc[0]["risk_level"]),
        }
        summary["lowest_pressure_district"] = {
            "district"       : str(df.iloc[-1]["district"]),
            "area_type"      : str(df.iloc[-1]["ur"]),
            "pressure_index" : round(float(df.iloc[-1]["pressure_index"]), 2),
            "risk_level"     : str(df.iloc[-1]["risk_level"]),
        }
        summary["districts_at_high_risk"]   = int(
            len(df[df["risk_level"] == "High"])
        )
        summary["districts_at_medium_risk"] = int(
            len(df[df["risk_level"] == "Medium"])
        )
        summary["total_district_combinations"] = len(df)

    # Highest inflation category 
    if "cpi_latest" in data_store:
        df_cpi = data_store["cpi_latest"].copy()
        df_cpi = df_cpi[
            (df_cpi["COICOP"].astype(str).str.len() == 2) &
            (df_cpi["COICOP"].astype(str) != "00")
        ]
        df_cpi = df_cpi.sort_values("YoY_pct", ascending=False)

        summary["highest_inflation_category"] = {
            "category"    : str(df_cpi.iloc[0]["Category_Name"]),
            "yoy_pct"     : round(float(df_cpi.iloc[0]["YoY_pct"]), 2),
        }
        summary["lowest_inflation_category"] = {
            "category"    : str(df_cpi.iloc[-1]["Category_Name"]),
            "yoy_pct"     : round(float(df_cpi.iloc[-1]["YoY_pct"]), 2),
        }

    # Vulnerability summary
    if "vulnerability" in data_store:
        vulnerability = data_store["vulnerability"]
        summary["vulnerability_summary"] = {
            q: {
                "inflation_rate": data["inflation_rate"],
                "vulnerability" : data["vulnerability"],
            }
            for q, data in vulnerability.items()
        }

    summary["data_source"] = (
        "NISR Consumer Price Index August 2026 + "
        "NISR EICV7 Household Survey 2023-2024"
    )
    summary["methodology_note"] = (
        "District pressure indices are modelled estimates. "
        "See /api/government/district-index for full methodology."
    )

    return summary
