# ============================================================
# ai_advice.py — AI Advice Router
# Rwanda Cost-of-Living Navigator
# ============================================================
# This file handles all AI-powered endpoints.
#
# It uses the Anthropic Claude API to generate:
#   Level 1 — Personalized financial advice based on the
#             user's actual inflation numbers
#   Level 2 — Answers to specific questions the user asks
#             about their cost-of-living situation
#   Level 3 — All responses available in both English
#             and Kinyarwanda
#
# How it works:
#   1. Frontend sends user's calculated inflation results
#   2. We build a prompt with their real numbers
#   3. Claude generates a personalized response
#   4. We send it back to the frontend
#
# Privacy note:
#   Spending amounts sent to this endpoint are used only
#   to generate the AI response — never stored anywhere.
#   The Anthropic API processes the request and discards it.
#
# Endpoints in this file:
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

# Anthropic API settings 
# The API key is stored in an environment variable — never
# hardcoded in the code. This keeps it secure.
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_MODEL      = "claude-sonnet-4-6"
MAX_TOKENS        = 1000


# ============================================================
# INPUT MODELS — what the frontend sends to the AI endpoints
# ============================================================

class AIAdviceRequest(BaseModel):
    """
    The data sent to the AI advice endpoint.
    Contains the user's calculated inflation results
    so Claude can give specific, relevant advice.
    """

    # Core inflation results
    personal_inflation_rate  : float = Field(
        description="User's personal inflation rate",
        example=16.7
    )
    national_average         : float = Field(
        default=15.86,
        description="National average inflation rate",
        example=15.86
    )
    biggest_pressure         : str = Field(
        description="Category hitting the user hardest",
        example="Food and non-alcoholic beverages"
    )
    biggest_pressure_yoy     : float = Field(
        description="Inflation rate of the biggest pressure category",
        example=16.7
    )
    biggest_pressure_share   : float = Field(
        description="Share of budget going to biggest pressure",
        example=34.8
    )
    monthly_extra_cost       : float = Field(
        description="Extra RWF per month due to inflation",
        example=26449
    )

    # Optional context
    district                 : Optional[str] = Field(
        default=None,
        description="User's district — for location-specific advice",
        example="Gasabo"
    )
    area_type                : Optional[str] = Field(
        default=None,
        description="Urban or Rural",
        example="Urban"
    )
    profile_comparison       : Optional[str] = Field(
        default=None,
        description="How user compares to their profile group",
        example="3.7% above the average urban household"
    )

    # Language preference — Level 3 NLP
    language                 : Optional[str] = Field(
        default="en",
        description="Language for response — en (English) or rw (Kinyarwanda)",
        example="en"
    )


class AIQuestionRequest(BaseModel):
    """
    A specific question the user wants to ask about
    their cost-of-living situation.
    """

    question                 : str = Field(
        description="The user's question",
        example="Why is my inflation higher than the national average?"
    )
    personal_inflation_rate  : Optional[float] = Field(
        default=None,
        description="User's personal inflation rate for context",
        example=16.7
    )
    biggest_pressure         : Optional[str] = Field(
        default=None,
        description="User's biggest pressure category for context",
        example="Food"
    )
    district                 : Optional[str] = Field(
        default=None,
        description="User's district for context",
        example="Gasabo"
    )
    language                 : Optional[str] = Field(
        default="en",
        description="en or rw",
        example="en"
    )


# ============================================================
# HELPER — Build the AI prompt
# ============================================================

def build_advice_prompt(request: AIAdviceRequest) -> str:
    """
    Build a clear, context-rich prompt for Claude.

    The prompt includes:
    - The user's actual numbers
    - Their location context if provided
    - Instructions to give practical Rwanda-specific advice
    - Language instruction for Level 3 NLP
    """

    # Language instruction 
    if request.language == "rw":
        language_instruction = (
            "Ongera igisubizo mu Kinyarwanda, "
            "ukoresha amagambo yoroheje."
            # Translation: "Give the response in Kinyarwanda,
            # using simple words."
        )
        language_name = "Kinyarwanda"
    else:
        language_instruction = (
            "Give the response in clear, simple English. "
            "No economic jargon. Write as if explaining "
            "to a friend, not writing a report."
        )
        language_name = "English"

    # Location context 
    location_context = ""
    if request.district:
        location_context = (
            f"The user lives in {request.district} "
            f"({request.area_type or 'Rwanda'})."
        )

    # Comparison context 
    comparison_context = ""
    if request.profile_comparison:
        comparison_context = (
            f"Compared to similar households, "
            f"they are {request.profile_comparison}."
        )

    # Build the full prompt 
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
- Be encouraging but honest — do not minimize real difficulties
- Never use words like "CPI", "index", "basis points",
  "year-on-year" — use plain language instead
- Keep it conversational — maximum 4 sentences total

{language_instruction}
"""
    return prompt.strip()


def build_question_prompt(request: AIQuestionRequest) -> str:
    """
    Build a prompt for answering a specific user question.
    Includes whatever context is available about the user.
    """

    if request.language == "rw":
        language_instruction = (
            "Subiza mu Kinyarwanda, ukoresha amagambo yoroheje."
        )
    else:
        language_instruction = (
            "Answer in clear, simple English. No jargon."
        )

    # Build context from available information
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
        context_parts.append(f"Their district: {request.district}")

    context = "\n".join(context_parts) if context_parts else (
        "No personal context provided — answer generally."
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
Never use economic jargon — explain everything simply.
Data source: NISR Consumer Price Index, {LATEST_DATA_MONTH}.

{language_instruction}
"""
    return prompt.strip()


# ============================================================
# HELPER — Call the Claude API
# ============================================================

async def call_claude_api(prompt: str) -> str:
    """
    Send a prompt to the Claude API and return the response.

    Uses httpx for async HTTP requests — this means the server
    can handle other requests while waiting for Claude's response
    instead of being blocked.
    """

    # Get API key from environment variable
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        raise HTTPException(
            status_code = 503,
            detail      = (
                "AI service not configured — "
                "ANTHROPIC_API_KEY environment variable not set"
            )
        )

    # Build the request body
    request_body = {
        "model"      : CLAUDE_MODEL,
        "max_tokens" : MAX_TOKENS,
        "messages"   : [
            {
                "role"   : "user",
                "content": prompt
            }
        ]
    }

    # Set request headers
    headers = {
        "Content-Type"      : "application/json",
        "x-api-key"         : api_key,
        "anthropic-version" : "2023-06-01"
    }

    try:
        # Send the request to Claude API
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                ANTHROPIC_API_URL,
                json    = request_body,
                headers = headers
            )

        # Check if the request succeeded
        if response.status_code != 200:
            logger.error(
                f"Claude API error: {response.status_code} "
                f"— {response.text}"
            )
            raise HTTPException(
                status_code = 503,
                detail      = "AI service temporarily unavailable"
            )

        # Extract the text from Claude's response
        response_data = response.json()
        ai_text = response_data["content"][0]["text"]
        return ai_text.strip()

    except httpx.TimeoutException:
        raise HTTPException(
            status_code = 504,
            detail      = "AI service timed out — please try again"
        )
    except Exception as e:
        logger.error(f"Claude API call failed: {e}")
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
    Claude AI.

    The advice is:
    - Based on the user's actual numbers — not generic tips
    - Written in plain language — no economic jargon
    - Rwanda-specific — mentions real local options
    - Available in English or Kinyarwanda (Level 3 NLP)

    Privacy: spending data is used only to generate this response
    and is never stored anywhere.
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

    # Build the prompt with the user's real numbers
    prompt = build_advice_prompt(request)

    # Call Claude API
    ai_response = await call_claude_api(prompt)

    return {
        "advice"          : ai_response,
        "language"        : request.language,
        "data_month"      : LATEST_DATA_MONTH,
        "generated_by"    : "Claude AI (Anthropic)",
        "privacy_note"    : (
            "This advice was generated using your spending data. "
            "No personal data was stored — this request is "
            "processed and immediately discarded."
        ),
        "disclaimer"      : (
            "This is AI-generated financial guidance based on "
            "NISR public data. It is not professional financial "
            "advice. For major financial decisions, consult a "
            "qualified financial advisor."
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

    Examples of questions users can ask:
    - "Why is my inflation higher than the national average?"
    - "What does housing inflation mean for my rent?"
    - "Will food prices keep rising?"
    - "How can I protect my family from inflation?"

    Available in English or Kinyarwanda.
    """
)
async def ask_question(request: AIQuestionRequest):
    """
    Answer a specific user question using Claude AI.
    """

    # Validate that a question was actually provided
    if not request.question or len(request.question.strip()) < 5:
        raise HTTPException(
            status_code = 400,
            detail      = "Please enter a question of at least 5 characters"
        )

    logger.info(
        f"AI question received — "
        f"language: {request.language}"
    )

    # Build the prompt
    prompt = build_question_prompt(request)

    # Call Claude API
    ai_response = await call_claude_api(prompt)

    return {
        "question"     : request.question,
        "answer"       : ai_response,
        "language"     : request.language,
        "data_month"   : LATEST_DATA_MONTH,
        "generated_by" : "Claude AI (Anthropic)",
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
    summary     = "Check if AI service is available",
    description = """
    Returns the status of the AI service.
    If the ANTHROPIC_API_KEY is not configured, the AI
    endpoints will not work — this endpoint tells you that
    clearly before a user tries to use them.
    """
)
def check_ai_health():
    """
    Check whether the AI service is properly configured.
    """

    api_key_configured = bool(os.getenv("ANTHROPIC_API_KEY"))

    return {
        "ai_service_available" : api_key_configured,
        "model"                : CLAUDE_MODEL,
        "levels_available"     : {
            "level_1_personal_advice"     : api_key_configured,
            "level_2_question_answering"  : api_key_configured,
            "level_3_kinyarwanda_support" : api_key_configured,
        },
        "status" : (
            "AI service ready"
            if api_key_configured
            else "AI service not configured — set ANTHROPIC_API_KEY"
        )
    }
