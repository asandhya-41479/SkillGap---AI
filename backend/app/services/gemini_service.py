import json

from fastapi import HTTPException, status
from google import genai

from app.core.config import settings
from app.services.prompts import JOB_EXTRACTION_PROMPT

_client = genai.Client(api_key=settings.gemini_api_key)


def extract_requirements(job_description: str) -> list[dict]:
    prompt = JOB_EXTRACTION_PROMPT.format(job_description=job_description)

    try:
        response = _client.models.generate_content(model="gemini-3.6-flash", contents=prompt)
        raw_text = response.text.strip()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Gemini API call failed: {e}")

    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
        raw_text = raw_text.strip()

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Gemini returned malformed output.")

    if not isinstance(parsed, list):
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Gemini returned an unexpected format.")

    return parsed