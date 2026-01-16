from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import pdfplumber
import re
from typing import List, Dict, Optional
import os
import json
import time
import urllib.request
import urllib.error
from pydantic import BaseModel

app = FastAPI(title="Audit Question Analyzer")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
LLM_MAX_QUESTIONS = int(os.getenv("LLM_MAX_QUESTIONS", "200"))
LLM_TEXT_LIMIT = int(os.getenv("LLM_TEXT_LIMIT", "12000"))

LOG_PATH = r"c:\Users\eller\audit-analyzer\.cursor\debug.log"


def log_debug(location: str, message: str, data: Dict, hypothesis_id: str, run_id: str = "pre-fix") -> None:
    payload = {
        "sessionId": "debug-session",
        "runId": run_id,
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data,
        "timestamp": int(time.time() * 1000),
    }
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(payload) + "\n")
    except Exception:
        pass

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")


class QuestionResult(BaseModel):
    question: str
    requirement_met: Optional[bool]
    confidence: float
    reasoning: str


class AnalysisResponse(BaseModel):
    questions: List[QuestionResult]
    total_questions: int
    met_count: int
    not_met_count: int


def extract_questions_from_text(text: str) -> List[str]:
    """
    Extract questions from PDF text using pattern matching.
    Looks for numbered questions, question marks, and common audit question patterns.
    """
    questions = []
    
    # Pattern 1: Numbered questions (1., 2., etc.)
    numbered_pattern = r'(?:^|\n)\s*(\d+[\.\)]\s*[^\n?]*\?)'
    matches = re.findall(numbered_pattern, text, re.MULTILINE | re.IGNORECASE)
    questions.extend(matches)
    
    # Pattern 2: Questions ending with question mark (with some context)
    question_pattern = r'([A-Z][^?]*\?)'
    matches = re.findall(question_pattern, text)
    questions.extend(matches)
    
    # Pattern 3: Audit-specific patterns (e.g., "Does the system...", "Is there...")
    audit_patterns = [
        r'(Does [^?]*\?)',
        r'(Is there [^?]*\?)',
        r'(Are [^?]*\?)',
        r'(Has [^?]*\?)',
        r'(Have [^?]*\?)',
        r'(Was [^?]*\?)',
        r'(Were [^?]*\?)',
    ]
    
    for pattern in audit_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        questions.extend(matches)
    
    # Clean and deduplicate questions
    cleaned_questions = []
    seen = set()
    for q in questions:
        q = q.strip()
        if len(q) > 10 and q not in seen:  # Filter out very short matches
            cleaned_questions.append(q)
            seen.add(q)
    
    return cleaned_questions


def analyze_requirement(question: str) -> Dict:
    """
    Analyze whether an audit requirement is met.
    This is a placeholder that uses keyword matching.
    For production, you'd want to use an LLM (OpenAI, Anthropic, etc.)
    or a more sophisticated NLP approach.
    """
    question_lower = question.lower()
    
    # Simple keyword-based analysis (placeholder)
    # Positive indicators
    positive_keywords = ['yes', 'implemented', 'compliant', 'meets', 'satisfies', 'fulfills']
    negative_keywords = ['no', 'missing', 'non-compliant', 'fails', 'violates', 'lacks']
    
    # Check for explicit answers in the question (if it's a statement)
    has_positive = any(keyword in question_lower for keyword in positive_keywords)
    has_negative = any(keyword in question_lower for keyword in negative_keywords)
    
    # Default: assume not met (conservative approach for audits)
    requirement_met = False
    confidence = 0.5
    reasoning = "Question extracted from document. Manual review recommended."
    
    if has_positive and not has_negative:
        requirement_met = True
        confidence = 0.7
        reasoning = "Question contains positive indicators suggesting requirement may be met."
    elif has_negative:
        requirement_met = False
        confidence = 0.7
        reasoning = "Question contains negative indicators suggesting requirement may not be met."
    else:
        # For actual questions (not statements), we can't determine from text alone
        requirement_met = None  # Needs manual review
        confidence = 0.3
        reasoning = "Cannot determine requirement status from question text alone. Requires evidence review."
    
    return {
        "requirement_met": requirement_met,
        "confidence": confidence,
        "reasoning": reasoning
    }


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main HTML page"""
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()


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


def llm_extract_and_analyze(text: str) -> Optional[List[Dict]]:
    # region agent log
    log_debug(
        "app.py:llm_extract_and_analyze:entry",
        "LLM extraction entry",
        {
            "has_key": bool(OPENAI_API_KEY),
            "key_length": len(OPENAI_API_KEY or ""),
            "model": OPENAI_MODEL,
        },
        hypothesis_id="H4",
    )
    # endregion
    if not OPENAI_API_KEY:
        return None
    trimmed_text = text[:LLM_TEXT_LIMIT]
    prompt = (
        "Extract audit questions and analyze them. "
        "Return ONLY valid JSON with this schema: "
        "{"
        "\"questions\":["
        "{"
        "\"question\":string,"
        "\"requirement_met\":true|false|null,"
        "\"confidence\":number,"
        "\"reasoning\":string"
        "}"
        "]"
        "}. "
        "If no questions are found, return {\"questions\":[]}. "
        "Text:\n"
        f"{trimmed_text}"
    )
    payload = {
        "model": OPENAI_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        # region agent log
        log_debug(
            "app.py:llm_extract_and_analyze:before_request",
            "Sending LLM request",
            {"text_length": len(trimmed_text)},
            hypothesis_id="H4",
        )
        # endregion
        with urllib.request.urlopen(request, timeout=60) as response:
            response_body = response.read().decode("utf-8")
        response_json = json.loads(response_body)
        content = response_json["choices"][0]["message"]["content"]
        # region agent log
        log_debug(
            "app.py:llm_extract_and_analyze:response_ok",
            "Received LLM response",
            {"content_length": len(content)},
            hypothesis_id="H4",
        )
        # endregion
        parsed = _extract_json_from_text(content)
        if not parsed or "questions" not in parsed:
            return None
        questions = parsed["questions"]
        if not isinstance(questions, list):
            return None
        return questions[:LLM_MAX_QUESTIONS]
    except (urllib.error.URLError, urllib.error.HTTPError, KeyError, json.JSONDecodeError) as exc:
        # region agent log
        log_debug(
            "app.py:llm_extract_and_analyze:exception",
            "LLM request failed",
            {"type": type(exc).__name__, "error": str(exc)},
            hypothesis_id="H4",
        )
        # endregion
        return None


@app.post("/upload", response_model=AnalysisResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload and process PDF file to extract and analyze audit questions.
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    try:
        # Read PDF content
        contents = await file.read()
        
        # Save temporarily
        temp_path = f"temp_{file.filename}"
        with open(temp_path, "wb") as f:
            f.write(contents)
        
        # Extract text from PDF
        text = ""
        with pdfplumber.open(temp_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        
        # Clean up temp file
        os.remove(temp_path)
        
        if not text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from PDF")
        
        # Extract questions (LLM if available, otherwise regex-based fallback)
        llm_questions = llm_extract_and_analyze(text)
        # region agent log
        log_debug(
            "app.py:upload_pdf:llm_result",
            "LLM extraction result",
            {
                "llm_used": llm_questions is not None,
                "llm_count": len(llm_questions) if llm_questions else 0,
            },
            hypothesis_id="H4",
        )
        # endregion
        questions = []
        if llm_questions is not None:
            for item in llm_questions:
                if not isinstance(item, dict):
                    continue
                question_text = item.get("question")
                if not question_text:
                    continue
                questions.append(question_text.strip())
        else:
            questions = extract_questions_from_text(text)
        
        if not questions:
            raise HTTPException(
                status_code=400, 
                detail="No questions found in PDF. Please ensure the document contains audit questions."
            )
        
        # Analyze each question
        results = []
        if llm_questions is not None:
            for item in llm_questions:
                if not isinstance(item, dict):
                    continue
                question_text = item.get("question", "").strip()
                if not question_text:
                    continue
                results.append(QuestionResult(
                    question=question_text,
                    requirement_met=item.get("requirement_met"),
                    confidence=float(item.get("confidence", 0.3)),
                    reasoning=item.get("reasoning", "LLM analysis provided.")
                ))
        else:
            for question in questions:
                analysis = analyze_requirement(question)
                results.append(QuestionResult(
                    question=question,
                    requirement_met=analysis["requirement_met"],
                    confidence=analysis["confidence"],
                    reasoning=analysis["reasoning"]
                ))
        
        # Calculate statistics
        met_count = sum(1 for r in results if r.requirement_met is True)
        not_met_count = sum(1 for r in results if r.requirement_met is False)
        
        return AnalysisResponse(
            questions=results,
            total_questions=len(results),
            met_count=met_count,
            not_met_count=not_met_count
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
