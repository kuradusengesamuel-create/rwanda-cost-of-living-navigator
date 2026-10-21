# ============================================================
# ai_advice.py — AI Advice Router (Groq version)
# Rwanda Cost-of-Living Navigator
# ============================================================
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import httpx
import os
import logging

from app.config import NATIONAL_INFLATION_LATEST, LATEST_DATA_MONTH

logger = logging.getLogger(__name__)
router = APIRouter()

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL   = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
MAX_TOKENS   = 1000

class AIAdviceRequest(BaseModel):
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
    question                : str             = Field(example="Why is my inflation higher?")
    personal_inflation_rate : Optional[float] = Field(default=None)
    biggest_pressure        : Optional[str]   = Field(default=None)
    district                : Optional[str]   = Field(default=None)
    language                : Optional[str]   = Field(default="en")

def build_advice_prompt(request: AIAdviceRequest) -> str:
    language_instruction = "Subiza mu Kinyarwanda, ukoresha amagambo yoroheje." if request.language == "rw" else "Give the response in clear, simple English. No economic jargon."
    location_context = f"The user lives in {request.district} ({request.area_type or 'Rwanda'})." if request.district else ""
    comparison_context = f"Compared to similar households, they are {request.profile_comparison}." if request.profile_comparison else ""
    prompt = f"""You are a friendly financial advisor helping a Rwandan household understand their cost-of-living situation in {LATEST_DATA_MONTH}.
Here is their specific situation:
- Personal inflation rate: {request.personal_inflation_rate}%
- National average inflation: {request.national_average}%
- Biggest financial pressure: {request.biggest_pressure} (rising {request.biggest_pressure_yoy}% this year, taking {request.biggest_pressure_share}% of their budget)
- Extra cost vs last year: RWF {request.monthly_extra_cost:,.0f} per month
{location_context}
{comparison_context}
In 3-4 sentences: explain what their numbers mean, give one practical action they can take this month, and one honest note about coming months. Mention real Rwanda options (Ecofleet buses, Kimironko market, Mutuelle de Sante, Bboxx). Never use CPI, index, basis points. Keep it conversational.
{language_instruction}"""
    return prompt.strip()

def build_question_prompt(request: AIQuestionRequest) -> str:
    language_instruction = "Subiza mu Kinyarwanda, ukoresha amagambo yoroheje." if request.language == "rw" else "Answer in clear, simple English. No jargon."
    context_parts = []
    if request.personal_inflation_rate:
        context_parts.append(f"Their personal inflation rate: {request.personal_inflation_rate}%")
    if request.biggest_pressure:
        context_parts.append(f"Their biggest pressure: {request.biggest_pressure}")
    if request.district:
        context_parts.append(f"Their district: {request.district}")
    context = "\n".join(context_parts) if context_parts else "No personal context provided."
    prompt = f"""You are a friendly financial advisor helping a Rwandan household.
Context: {context}
Question: "{request.question}"
Answer in 2-3 sentences. Be specific and practical. Mention Rwanda-specific options where relevant. Never use economic jargon. Data source: NISR CPI, {LATEST_DATA_MONTH}.
{language_instruction}"""
    return prompt.strip()

def get_api_key() -> str:
    # Prefer GROQ_API_KEY; fall back to the old GEMINI_API_KEY name so the
    # existing Render setting keeps working.
    return os.getenv("GROQ_API_KEY") or os.getenv("GEMINI_API_KEY") or ""

async def call_groq_api(prompt: str) -> str:
    api_key = get_api_key()
    if not api_key:
        raise HTTPException(status_code=503, detail="AI service not configured — GROQ_API_KEY not set")
    body = {"model": GROQ_MODEL, "messages": [{"role": "user", "content": prompt}], "max_tokens": MAX_TOKENS, "temperature": 0.7}
    if "gpt-oss" in GROQ_MODEL:
        body["reasoning_effort"] = "low"  # keeps answers short and fast
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                GROQ_API_URL,
                json=body,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            )
        if response.status_code != 200:
            logger.error(f"Groq API error: {response.status_code} — {response.text}")
            raise HTTPException(status_code=503, detail="AI service temporarily unavailable")
        return response.json()["choices"][0]["message"]["content"].strip()
    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="AI service timed out — please try again")
    except Exception as e:
        logger.error(f"Groq API call failed: {e}")
        raise HTTPException(status_code=503, detail="AI service temporarily unavailable")

@router.post("/advice")
async def get_ai_advice(request: AIAdviceRequest):
    logger.info(f"AI advice requested — personal rate: {request.personal_inflation_rate}%, language: {request.language}")
    prompt = build_advice_prompt(request)
    ai_response = await call_groq_api(prompt)
    return {"advice": ai_response, "language": request.language, "data_month": LATEST_DATA_MONTH, "generated_by": f"Groq AI ({GROQ_MODEL})", "privacy_note": "No personal data was stored.", "disclaimer": "AI-generated guidance based on NISR public data. Not professional financial advice."}

@router.post("/question")
async def ask_question(request: AIQuestionRequest):
    if not request.question or len(request.question.strip()) < 5:
        raise HTTPException(status_code=400, detail="Please enter a question of at least 5 characters")
    logger.info(f"AI question received — language: {request.language}")
    prompt = build_question_prompt(request)
    ai_response = await call_groq_api(prompt)
    return {"question": request.question, "answer": ai_response, "language": request.language, "data_month": LATEST_DATA_MONTH, "generated_by": f"Groq AI ({GROQ_MODEL})", "disclaimer": "AI-generated answer based on NISR public data. Not professional financial advice."}

@router.get("/health")
def check_ai_health():
    api_key_configured = bool(get_api_key())
    return {"ai_service_available": api_key_configured, "model": GROQ_MODEL, "provider": "Groq", "status": "AI service ready" if api_key_configured else "AI service not configured"}
