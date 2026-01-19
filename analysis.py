import re
from typing import Dict, List, Optional


def extract_questions_from_text(text: str) -> List[str]:
    """
    Extract questions from PDF text using pattern matching.
    Looks for numbered questions, question marks, and common audit question patterns.
    """
    questions = []

    # Pattern 1: Numbered questions (1., 2., etc.)
    numbered_pattern = r"(?:^|\n)\s*(\d+[\.\)]\s*[^\n?]*\?)"
    matches = re.findall(numbered_pattern, text, re.MULTILINE | re.IGNORECASE)
    questions.extend(matches)

    # Pattern 2: Questions ending with question mark (with some context)
    question_pattern = r"([A-Z][^?]*\?)"
    matches = re.findall(question_pattern, text)
    questions.extend(matches)

    # Pattern 3: Audit-specific patterns (e.g., "Does the system...", "Is there...")
    audit_patterns = [
        r"(Does [^?]*\?)",
        r"(Is there [^?]*\?)",
        r"(Are [^?]*\?)",
        r"(Has [^?]*\?)",
        r"(Have [^?]*\?)",
        r"(Was [^?]*\?)",
        r"(Were [^?]*\?)",
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


def _normalize_bool(value: Optional[object]) -> Optional[bool]:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "yes", "y", "met", "compliant", "satisfied", "fulfilled"}:
            return True
        if lowered in {"false", "no", "n", "not met", "non-compliant", "missing", "fails"}:
            return False
    return None


def _derive_requirement_met(answer_value: Optional[object], requirement_value: Optional[object]) -> Optional[bool]:
    normalized = _normalize_bool(requirement_value)
    if normalized is not None:
        return normalized
    return _normalize_bool(answer_value)


def _parse_confidence(value: Optional[object], default: float = 0.3) -> float:
    try:
        return float(value) if value is not None else default
    except (TypeError, ValueError):
        return default


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
    positive_keywords = ["yes", "implemented", "compliant", "meets", "satisfies", "fulfills"]
    negative_keywords = ["no", "missing", "non-compliant", "fails", "violates", "lacks"]

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
        "reasoning": reasoning,
        "answer": None,
        "evidence": None,
    }


__all__ = [
    "extract_questions_from_text",
    "analyze_requirement",
    "_derive_requirement_met",
    "_parse_confidence",
]
