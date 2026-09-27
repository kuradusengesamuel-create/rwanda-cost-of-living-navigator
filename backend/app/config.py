# ============================================================
# config.py — Rwanda Cost-of-Living Navigator
# ============================================================
# This file holds all settings and file paths used by the
# backend. Instead of writing file paths in every file,
# we write them once here and import them everywhere else.
# Think of it as the "settings page" of the backend.
# ============================================================

import os
from pathlib import Path

# Where is this file located? 
# This gives us the absolute path to the backend folder
# so all other paths work correctly no matter where the
# code is running (locally, on Render, etc.)
BASE_DIR = Path(__file__).resolve().parent.parent

# Data folder 
# This is where the backend looks for all processed data files
DATA_DIR = BASE_DIR / "data"

# CPI data files
# These come from our data pipeline Phase 3 outputs
CPI_LATEST_FILE   = DATA_DIR / "cpi_latest_month.csv"
CPI_HISTORY_FILE  = DATA_DIR / "cpi_clean_long.csv"
BASKET_FILE       = DATA_DIR / "basket_weights.csv"

# Personal tier files (Tier 1) 
PROFILES_FILE     = DATA_DIR / "profile_benchmarks.json"
TIPS_FILE         = DATA_DIR / "tips_library.json"

# Business tier files (Tier 2) 
FORECASTS_FILE    = DATA_DIR / "inflation_forecasts.csv"

# Government tier files (Tier 3)
DISTRICT_INDEX_FILE   = DATA_DIR / "district_pressure_index.csv"
DISTRICT_WEIGHTS_FILE = DATA_DIR / "district_basket_weights.csv"
VULNERABILITY_FILE    = DATA_DIR / "vulnerability_scores.json"

# Shared files (used by all tiers)
HOUSEHOLDS_FILE   = DATA_DIR / "households.csv"

# API settings
# The name shown in the API documentation page
API_TITLE   = "Rwanda Cost-of-Living Navigator API"
API_VERSION = "1.0.0"
API_DESCRIPTION = """
A REST API that transforms official NISR statistics into
personalized cost-of-living intelligence for Rwandan
households, businesses, and government planners.

Data sources:
- NISR Consumer Price Index (monthly)
- NISR EICV7 Household Survey (2023-2024)
"""

# CORS settings 
# These are the web addresses allowed to talk to this API
# During development, we allow everything (*)
# During deployment, we will restrict to our actual frontend URL
ALLOWED_ORIGINS = [
    "*",                              # allow all during development
    "http://localhost:3000",          # local frontend development
    "https://rwanda-clnp.vercel.app", # deployed frontend (update later)
]

# National inflation reference 
# Used as the baseline comparison in all three tiers
NATIONAL_INFLATION_LATEST = 15.86   # August 2026 — update monthly
LATEST_DATA_MONTH         = "August 2026"
FORECAST_MONTHS           = ["September 2026",
                              "October 2026",
                              "November 2026"]
