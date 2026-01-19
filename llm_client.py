import json
import os
import urllib.error
import urllib.request
from typing import Dict, List, Optional

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-2.0-flash")
LLM_MAX_QUESTIONS = int(os.getenv("LLM_MAX_QUESTIONS", "200"))
LLM_TEXT_LIMIT = int(os.getenv("LLM_TEXT_LIMIT", "12000"))


def _extract_json_from_text(text: str) -> Optional[Dict]:
    text = text.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None


def _call_gemini(prompt: str, model_name: str) -> Optional[List[Dict]]:
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }
    request_url = f"https://generativelanguage.googleapis.com/v1/models/{model_name}:generateContent"
    request = urllib.request.Request(
        f"{request_url}?key={GEMINI_API_KEY}",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            response_body = response.read().decode("utf-8")
        response_json = json.loads(response_body)
        content = response_json["candidates"][0]["content"]["parts"][0]["text"]
        parsed = _extract_json_from_text(content)
        if not parsed or "questions" not in parsed:
            return None
        questions = parsed["questions"]
        if not isinstance(questions, list):
            return None
        return questions[:LLM_MAX_QUESTIONS]
    except (urllib.error.URLError, urllib.error.HTTPError, KeyError, json.JSONDecodeError):
        return None


def llm_extract_and_analyze(text: str) -> Optional[List[Dict]]:
    if not GEMINI_API_KEY:
        return None
    trimmed_text = text[:LLM_TEXT_LIMIT]
    prompt = (
        "You are an audit analyst. First, count the number of audit questions "
        "present in the document. Then, for each question, determine the answer "
        "using evidence from elsewhere in the document. Only provide an answer "
        "and evidence when they are clearly supported by the text; otherwise use null. "
        "Return ONLY valid JSON with this schema: "
        "{"
        "\"question_count\":number,"
        "\"questions\":["
        "{"
        "\"question\":string,"
        "\"answer\":string|null,"
        "\"evidence\":string|null,"
        "\"requirement_met\":true|false|null,"
        "\"confidence\":number,"
        "\"reasoning\":string"
        "}"
        "]"
        "}. "
        "If no questions are found, return {\"question_count\":0,\"questions\":[]}. "
        "Use short, direct quotes for evidence when available. "
        "Text:\n"
        f"{trimmed_text}"
    )
    model_name = GEMINI_MODEL
    if model_name.startswith("models/"):
        model_name = model_name[len("models/") :]
    fallback_model = GEMINI_FALLBACK_MODEL
    if fallback_model.startswith("models/"):
        fallback_model = fallback_model[len("models/") :]
    result = _call_gemini(prompt, model_name)
    if result is not None:
        return result
    if fallback_model and fallback_model != model_name:
        return _call_gemini(prompt, fallback_model)
    return None


__all__ = ["llm_extract_and_analyze"]
