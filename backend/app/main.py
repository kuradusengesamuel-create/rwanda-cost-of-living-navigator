
# main.py — Rwanda Cost-of-Living Navigator

# This is the entry point of the entire backend.
# When the server starts, it runs this file first.

# Think of this file as the reception desk of a building:
# - It welcomes everyone who arrives (API requests)
# - It directs them to the right department (routers)
# - It handles general building rules (CORS, errors)
# - It shows a directory of all available services (docs)


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import pandas as pd
import json
import logging

from app.config import (
    API_TITLE,
    API_VERSION,
    API_DESCRIPTION,
    ALLOWED_ORIGINS,
    CPI_LATEST_FILE,
    CPI_HISTORY_FILE,
    BASKET_FILE,
    FORECASTS_FILE,
    DISTRICT_INDEX_FILE,
    DISTRICT_WEIGHTS_FILE,
    VULNERABILITY_FILE,
    PROFILES_FILE,
    TIPS_FILE,
    HOUSEHOLDS_FILE,
)

# Set up logging 
# This prints helpful messages to the server console
# so we can see what is happening when the server runs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



# DATA STORE

# This dictionary holds all our data in memory after loading.
# Loading from files once at startup is much faster than
# reading files every time someone makes a request.
# Think of it as loading all the books onto a desk at the
# start of the day instead of going to the shelf every time.
# ---------------------------------------------------------------
data_store = {}


def load_all_data():
    """
    Load all processed data files into memory when the
    server starts. If a file is missing, log a warning
    but do not crash — the server still runs.
    """

    logger.info("Loading all data files into memory...")

    # CPI data 
    try:
        data_store["cpi_latest"] = pd.read_csv(CPI_LATEST_FILE)
        logger.info(f" CPI latest month loaded — "
                    f"{len(data_store['cpi_latest'])} rows")
    except Exception as e:
        logger.warning(f" Could not load CPI latest: {e}")

    try:
        data_store["cpi_history"] = pd.read_csv(CPI_HISTORY_FILE)
        data_store["cpi_history"]["Date"] = pd.to_datetime(
            data_store["cpi_history"]["Date"]
        )
        logger.info(f"CPI history loaded — "
                    f"{len(data_store['cpi_history'])} rows")
    except Exception as e:
        logger.warning(f"Could not load CPI history: {e}")

    try:
        data_store["basket_weights"] = pd.read_csv(BASKET_FILE)
        logger.info(f"Basket weights loaded — "
                    f"{len(data_store['basket_weights'])} rows")
    except Exception as e:
        logger.warning(f"Could not load basket weights: {e}")

    # Forecast data 
    try:
        data_store["forecasts"] = pd.read_csv(FORECASTS_FILE)
        logger.info(f"Forecasts loaded — "
                    f"{len(data_store['forecasts'])} rows")
    except Exception as e:
        logger.warning(f"Could not load forecasts: {e}")

    # Government tier data 
    try:
        data_store["district_index"] = pd.read_csv(
            DISTRICT_INDEX_FILE
        )
        logger.info(f"District pressure index loaded — "
                    f"{len(data_store['district_index'])} rows")
    except Exception as e:
        logger.warning(f"Could not load district index: {e}")

    try:
        data_store["district_weights"] = pd.read_csv(
            DISTRICT_WEIGHTS_FILE
        )
        logger.info(f"District weights loaded — "
                    f"{len(data_store['district_weights'])} rows")
    except Exception as e:
        logger.warning(f"Could not load district weights: {e}")

    try:
        with open(VULNERABILITY_FILE, "r") as f:
            data_store["vulnerability"] = json.load(f)
        logger.info("Vulnerability scores loaded")
    except Exception as e:
        logger.warning(f"Could not load vulnerability scores: {e}")

    # Personal tier data 
    try:
        with open(PROFILES_FILE, "r") as f:
            data_store["profiles"] = json.load(f)
        logger.info("Profile benchmarks loaded")
    except Exception as e:
        logger.warning(f"Could not load profiles: {e}")

    try:
        with open(TIPS_FILE, "r") as f:
            data_store["tips"] = json.load(f)
        logger.info("Tips library loaded")
    except Exception as e:
        logger.warning(f"Could not load tips: {e}")

    # Household data 
    try:
        data_store["households"] = pd.read_csv(HOUSEHOLDS_FILE)
        logger.info(f"✓ Households loaded — "
                    f"{len(data_store['households'])} rows")
    except Exception as e:
        logger.warning(f"✗ Could not load households: {e}")

    logger.info("All data loading complete.")


# ============================================================
# APPLICATION LIFECYCLE
# ============================================================
# This runs once when the server starts (startup) and once
# when it shuts down (shutdown). We use startup to load
# all our data files into memory so they are ready instantly.
# ============================================================
  
@asynccontextmanager
async def lifespan(app: FastAPI):
    # On startup
    logger.info("Rwanda Cost-of-Living Navigator API starting...")
    load_all_data()
    logger.info("API is ready to serve requests.")
    yield
    # On shutdown 
    logger.info("API shutting down — clearing data from memory.")
    data_store.clear()


# ============================================================
# CREATE THE FASTAPI APPLICATION
# ============================================================
app = FastAPI(
    title       = API_TITLE,
    version     = API_VERSION,
    description = API_DESCRIPTION,
    lifespan    = lifespan,

    # These URLs show the interactive API documentation
    # Visit /docs to see and test all endpoints in a browser
    docs_url    = "/docs",
    redoc_url   = "/redoc",
)


# ============================================================
# CORS MIDDLEWARE
# ============================================================
# CORS (Cross-Origin Resource Sharing) allows our frontend
# to talk to this backend even though they are on different
# servers. Without this, the browser would block all requests.
# Think of it as giving our frontend a visitor's pass.
# ============================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ALLOWED_ORIGINS,
    allow_credentials = True,
    allow_methods     = ["*"],   # allow GET, POST, etc.
    allow_headers     = ["*"],   # allow all headers
)


# ============================================================
# INCLUDE ROUTERS
# ============================================================
# Each router handles one tier of the platform.
# We import them here and register them with the app.
# This keeps the code organized — personal tier logic
# stays in personal.py, not mixed into this file.

from app.routers import personal, business, government, ai_advice

app.include_router(
    personal.router,
    prefix = "/api/personal",
    tags   = ["Personal Tier — Household inflation calculator"],
)

app.include_router(
    business.router,
    prefix = "/api/business",
    tags   = ["Business Tier — Cost pressure and budgeting"],
)

app.include_router(
    government.router,
    prefix = "/api/government",
    tags   = ["Government Tier — District pressure index"],
)

app.include_router(
    ai_advice.router,
    prefix = "/api/ai",
    tags   = ["AI Tier — Personalized advice and chat"],
)


# ============================================================
# ROOT ENDPOINT
# ============================================================
# This is the home page of the API — visiting the base URL
# returns a simple welcome message confirming the API is live.
# ============================================================
@app.get("/", tags=["Health check"])
def root():
    """
    Health check endpoint.
    Returns a welcome message confirming the API is running.
    Visit /docs to see all available endpoints.
    """
    return {
        "message"     : "Rwanda Cost-of-Living Navigator API is running",
        "version"     : API_VERSION,
        "data_month"  : "August 2026",
        "tiers"       : [
            "Personal — /api/personal",
            "Business — /api/business",
            "Government — /api/government",
            "AI Advice — /api/ai",
        ],
        "documentation": "/docs",
        "status"      : "healthy",
    }


@app.get("/health", tags=["Health check"])
def health_check():
    """
    Detailed health check.
    Shows which data files loaded successfully.
    """
    return {
        "status"        : "healthy",
        "data_loaded"   : {
            key: len(value) if hasattr(value, '__len__') else "loaded"
            for key, value in data_store.items()
        }
    }
