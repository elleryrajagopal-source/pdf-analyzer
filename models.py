from typing import List, Optional

from pydantic import BaseModel


class QuestionResult(BaseModel):
    question: str
    requirement_met: Optional[bool]
    confidence: float
    reasoning: str
    answer: Optional[str] = None
    evidence: Optional[str] = None


class AnalysisResponse(BaseModel):
    questions: List[QuestionResult]
    total_questions: int
    met_count: int
    not_met_count: int
