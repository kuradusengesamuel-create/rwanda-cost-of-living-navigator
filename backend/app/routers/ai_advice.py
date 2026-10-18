# ============================================================
# ai_advice.py — AI Advice Router (Gemini version)
# Rwanda Cost-of-Living Navigator
# ============================================================
# This file handles all AI-powered endpoints.
# Updated to use Google Gemini API (free tier)
# instead of Anthropic Claude API.
#
# Endpoints:
#   POST /api/ai/advice      — personalized AI advice
#   POST /api/ai/question    — answer a specific question
#   GET  /api/ai/health      — check AI service is available
# ============================================================

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import httpx
import os
import logging

from app.config import NATIONAL_INFLATION_LATEST, LATEST_DATA_MONTH

# Set up logging 
logger = logging.getLogger(__name__)

# Create the router 
router = APIRouter()

# Gemini API settings 
GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com"
    "/v1beta/models/gemini-1.5-flash:generateContent"
)
MAX_TOKENS = 1000


# ============================================================
# INPUT MODELS
# ============================================================

class AIAdviceRequest(BaseModel):
    """
    The data sent to the AI advice endpoint.
    Contains the user's calculated inflation results
    so Gemini can give specific, relevant advice.
    """
    personal_inflation_rate : float = Field(example=16.7)
    national_average        : float = Field(default=15.86)
    biggest_pressure        : str   = Field(example="Food")
    biggest_pressure_yoy    : float = Field(example=16.7)
    biggest_pressure_share  : float = Field(example=34.8)
    monthly_extra_cost      : float = Field(example=26449)
    district                : Optional[str]   = Field(default=None)
    area_type               : Optional[str]   = Field(default=None)
    profile_comparison      : Optional[str]   = Field(default=None)
    language                : Optional[str]   = Field(default="en")


class AIQuestionRequest(BaseModel):
    """
    A specific question the user wants to ask.
    """
    question                : str           = Field(example="Why is my inflation higher?")
    personal_inflation_rate : Optional[float] = Field(default=None)
    biggest_pressure        : Optional[str]   = Field(default=None)
    district                : Optional[str]   = Field(default=None)
    language                : Optional[str]   = Field(default="en")


# ============================================================
# HELPER — Build prompts
# ============================================================

def build_advice_prompt(request: AIAdviceRequest) -> str:
    """
    Build a clear prompt for Gemini with the user's
    real inflation numbers and Rwanda-specific context.
    """

    if request.language == "rw":
        language_instruction = (
            "Subiza mu Kinyarwanda, ukoresha amagambo yoroheje. "
            "Ntukoresha amagambo y'ubukungu agoye."
        )
    else:
        language_instruction = (
            "Give the response in clear, simple English. "
            "No economic jargon. Write as if explaining "
            "to a friend, not writing a report."
        )

    location_context = ""
    if request.district:
        location_context = (
            f"The user lives in {request.district} "
            f"({request.area_type or 'Rwanda'})."
        )

    comparison_context = ""
    if request.profile_comparison:
        comparison_context = (
            f"Compared to similar households, "
            f"they are {request.profile_comparison}."
        )

    prompt = f"""
You are a friendly financial advisor helping a Rwandan household
understand their cost-of-living situation in {LATEST_DATA_MONTH}.

Here is their specific situation:
- Personal inflation rate: {request.personal_inflation_rate}%
- National average inflation: {request.national_average}%
- Biggest financial pressure: {request.biggest_pressure}
  (rising {request.biggest_pressure_yoy}% this year,
   taking {request.biggest_pressure_share}% of their budget)
- Extra cost vs last year: RWF {request.monthly_extra_cost:,.0f} per month
{location_context}
{comparison_context}

In 3-4 sentences, give them:
1. A clear explanation of what their numbers mean in plain language
2. One specific, practical action they can take this month
3. One honest note about what to expect in the coming months

Important rules:
- Mention real options available in Rwanda where relevant
  (e.g. Ecofleet buses, Kimironko market, Mutuelle de Santé,
   solar companies like Bboxx, local markets)
- Be encouraging but honest
- Never use words like CPI, index, basis points, year-on-year
- Keep it conversational — maximum 4 sentences total

{language_instruction}
"""
    return prompt.strip()


def build_question_prompt(request: AIQuestionRequest) -> str:
    """
    Build a prompt for answering a specific user question.
    """

    if request.language == "rw":
        language_instruction = (
            "Subiza mu Kinyarwanda, ukoresha amagambo yoroheje."
        )
    else:
        language_instruction = (
            "Answer in clear, simple English. No jargon."
        )

    context_parts = []
    if request.personal_inflation_rate:
        context_parts.append(
            f"Their personal inflation rate: "
            f"{request.personal_inflation_rate}%"
        )
    if request.biggest_pressure:
        context_parts.append(
            f"Their biggest pressure: {request.biggest_pressure}"
        )
    if request.district:
        context_parts.append(
            f"Their district: {request.district}"
        )

    context = (
        "\n".join(context_parts)
        if context_parts
        else "No personal context provided — answer generally."
    )

    prompt = f"""
You are a friendly financial advisor helping a Rwandan household
understand their cost-of-living situation.

Context about this user:
{context}

The user's question: "{request.question}"

Answer their question in 2-3 sentences maximum.
Be specific, practical, and mention Rwanda-specific
options where relevant.
Never use economic jargon.
Data source: NISR Consumer Price Index, {LATEST_DATA_MONTH}.

{language_instruction}
"""
    return prompt.strip()


# ============================================================
# HELPER — Call Gemini API
# ============================================================

async def call_gemini_api(prompt: str) -> str:
    """
    Send a prompt to Google Gemini API and return the response.
    Uses the free gemini-1.5-flash model.
    """

    from dotenv import load_dotenv; load_dotenv(); api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise HTTPException(
            status_code = 503,
            detail      = (
                "AI service not configured — "
                "GEMINI_API_KEY environment variable not set"
            )
        )

    # Build the request URL with API key
    url = f"{GEMINI_API_URL}?key={api_key}"

    # Build the request body — Gemini format
    request_body = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "maxOutputTokens" : MAX_TOKENS,
            "temperature"     : 0.7,
        }
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                url,
                json = request_body,
                headers = {"Content-Type": "application/json"}
            )

        if response.status_code != 200:
            logger.error(
                f"Gemini API error: {response.status_code} "
                f"— {response.text}"
            )
            raise HTTPException(
                status_code = 503,
                detail      = "AI service temporarily unavailable"
            )

        # Extract text from Gemini response
        response_data = response.json()
        ai_text = (
            response_data["candidates"][0]
            ["content"]["parts"][0]["text"]
        )
        return ai_text.strip()

    except httpx.TimeoutException:
        raise HTTPException(
            status_code = 504,
            detail      = "AI service timed out — please try again"
        )
    except Exception as e:
        logger.error(f"Gemini API call failed: {e}")
        raise HTTPException(
            status_code = 503,
            detail      = "AI service temporarily unavailable"
        )


# ============================================================
# ENDPOINT 1 — Personalized AI Advice (Level 1)
# ============================================================
@router.post(
    "/advice",
    summary     = "Get personalized AI advice based on inflation results",
    description = """
    Takes a household's calculated inflation results and returns
    a personalized 3-4 sentence advice paragraph generated by
    Google Gemini AI. Available in English or Kinyarwanda.
    """
)
async def get_ai_advice(request: AIAdviceRequest):
    """
    Generate personalized AI advice for a household.
    """

    logger.info(
        f"AI advice requested — "
        f"personal rate: {request.personal_inflation_rate}%, "
        f"language: {request.language}"
    )

    prompt      = build_advice_prompt(request)
    ai_response = await call_gemini_api(prompt)

    return {
        "advice"       : ai_response,
        "language"     : request.language,
        "data_month"   : LATEST_DATA_MONTH,
        "generated_by" : "Google Gemini AI (gemini-1.5-flash)",
        "privacy_note" : (
            "This advice was generated using your spending data. "
            "No personal data was stored."
        ),
        "disclaimer"   : (
            "AI-generated financial guidance based on NISR public "
            "data. Not professional financial advice."
        )
    }


# ============================================================
# ENDPOINT 2 — AI Question Answering (Level 2)
# ============================================================
@router.post(
    "/question",
    summary     = "Ask a specific question about your cost-of-living",
    description = """
    Allows users to ask any specific question about their
    cost-of-living situation and get an AI-generated answer.
    Available in English or Kinyarwanda.
    """
)
async def ask_question(request: AIQuestionRequest):
    """
    Answer a specific user question using Gemini AI.
    """

    if not request.question or len(request.question.strip()) < 5:
        raise HTTPException(
            status_code = 400,
            detail      = "Please enter a question of at least 5 characters"
        )

    logger.info(f"AI question received — language: {request.language}")

    prompt      = build_question_prompt(request)
    ai_response = await call_gemini_api(prompt)

    return {
        "question"     : request.question,
        "answer"       : ai_response,
        "language"     : request.language,
        "data_month"   : LATEST_DATA_MONTH,
        "generated_by" : "Google Gemini AI (gemini-1.5-flash)",
        "disclaimer"   : (
            "AI-generated answer based on NISR public data. "
            "Not professional financial advice."
        )
    }


# ============================================================
# ENDPOINT 3 — AI Service Health Check
# ============================================================
@router.get(
    "/health",
    summary = "Check if AI service is available"
)
def check_ai_health():
    """
    Check whether the Gemini AI service is configured.
    """

    api_key_configured = bool(os.getenv("GEMINI_API_KEY"))

    return {
        "ai_service_available" : api_key_configured,
        "model"                : "gemini-1.5-flash (free tier)",
        "provider"             : "Google Gemini",
        "levels_available"     : {
            "level_1_personal_advice"    : api_key_configured,
            "level_2_question_answering" : api_key_configured,
            "level_3_kinyarwanda"        : api_key_configured,
        },
        "status" : (
            "AI service ready"
            if api_key_configured
            else "AI service not configured — set GEMINI_API_KEY"
        )
    }


