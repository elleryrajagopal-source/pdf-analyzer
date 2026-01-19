from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import pdfplumber
import io

from analysis import analyze_requirement, extract_questions_from_text, _derive_requirement_met, _parse_confidence
from llm_client import llm_extract_and_analyze
from models import AnalysisResponse, QuestionResult

app = FastAPI(title="Audit Question Analyzer")

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


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main HTML page"""
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()


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
        
        # Use in-memory buffer to avoid filesystem writes (Vercel is read-only).
        pdf_buffer = io.BytesIO(contents)
        
        # Extract text from PDF
        text = ""
        with pdfplumber.open(pdf_buffer) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        
        if not text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from PDF")
        
        # Extract questions (LLM if available, otherwise regex-based fallback)
        llm_questions = llm_extract_and_analyze(text)
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
                answer = item.get("answer")
                if isinstance(answer, str):
                    answer = answer.strip() or None
                evidence = item.get("evidence")
                if isinstance(evidence, str):
                    evidence = evidence.strip() or None
                results.append(QuestionResult(
                    question=question_text,
                    requirement_met=_derive_requirement_met(answer, item.get("requirement_met")),
                    confidence=_parse_confidence(item.get("confidence"), 0.3),
                    reasoning=item.get("reasoning", "LLM analysis provided."),
                    answer=answer,
                    evidence=evidence,
                ))
        else:
            for question in questions:
                analysis = analyze_requirement(question)
                results.append(QuestionResult(
                    question=question,
                    requirement_met=analysis["requirement_met"],
                    confidence=analysis["confidence"],
                    reasoning=analysis["reasoning"],
                    answer=analysis["answer"],
                    evidence=analysis["evidence"],
                ))
        
        # Calculate statistics
        met_count = sum(1 for r in results if r.requirement_met is True)
        not_met_count = sum(1 for r in results if r.requirement_met is False)
        
        return AnalysisResponse(
            questions=results,
            total_questions=len(results),
            met_count=met_count,
            not_met_count=not_met_count,
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
