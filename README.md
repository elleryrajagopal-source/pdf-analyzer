# Audit Question Analyzer

A web application that extracts audit questions from PDF documents and analyzes whether each requirement is met.

## Features

- 📄 PDF document upload and text extraction
- 🔍 Automatic question extraction using pattern matching (LLM optional)
- ✅ Requirement status analysis for each question (LLM optional)
- 📊 Summary statistics and detailed results display
- 🎨 Modern, responsive web interface

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Navigate to the project directory:**
   ```bash
   cd audit-analyzer
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python app.py
   ```

4. **(Optional) Configure LLM analysis:**
   - Set `GEMINI_API_KEY` in your environment to enable LLM parsing and analysis
   - Optional overrides:
     - `GEMINI_MODEL` (default: `gemini-1.5-flash`)
     - `LLM_TEXT_LIMIT` (default: `12000`)
     - `LLM_MAX_QUESTIONS` (default: `200`)

5. **Open your browser and navigate to:**
   ```
   http://localhost:8000
   ```

## Deployment (Vercel)

This project can be deployed to Vercel using the Python serverless runtime.

1. **Push the repo to GitHub** (already done).
2. **Import the repo in Vercel** and set the framework to "Other".
3. **Configure environment variables (optional):**
   - `GEMINI_API_KEY`
   - `GEMINI_MODEL`, `LLM_TEXT_LIMIT`, `LLM_MAX_QUESTIONS` (optional overrides)
4. **Deploy.**

The included `vercel.json` routes all requests to `api/index.py`, which exposes the FastAPI app.

## Usage

1. Upload a PDF document containing audit questions
2. The app will automatically extract questions from the document
3. Each question will be analyzed to determine if the requirement is met
4. View the results with statistics and detailed analysis

### Test PDFs

Sample PDFs are available in `test_pdfs/`:
- `audit_questions.pdf` (contains clear questions, answers, and evidence)
- `no_questions.pdf` (no questions; should return a 400 response)
- `ambiguous_evidence.pdf` (questions with unclear or conflicting evidence)
- `policies_and_questions.pdf` (10 policies, then 20 audit questions; policies should not count as questions)

## How It Works

### Question Extraction

If `GEMINI_API_KEY` is set, the app uses an LLM to extract and analyze questions.
If not, it falls back to pattern matching:
- Numbered questions (1., 2., etc.)
- Questions ending with question marks
- Common audit question patterns (Does..., Is there..., Are..., etc.)

### Requirement Analysis

If `GEMINI_API_KEY` is set, the app uses an LLM to determine requirement status.
Otherwise, it falls back to keyword-based analysis. For production use, you may want to:
- Add evidence/documentation review capabilities
- Implement custom business logic for your specific audit requirements

## Project Structure

```
audit-analyzer/
├── app.py              # FastAPI backend application
├── api/
│   └── index.py        # Vercel serverless entrypoint
├── static/
│   └── index.html      # Frontend web interface
├── requirements.txt    # Python dependencies
├── vercel.json         # Vercel configuration
└── README.md          # This file
```

## Next Steps / Enhancements

1. **LLM Integration**: Replace keyword-based analysis with AI-powered analysis using OpenAI GPT, Anthropic Claude, or similar
2. **Evidence Upload**: Allow users to upload supporting documents for each question
3. **Export Results**: Add functionality to export results as CSV, PDF, or Excel
4. **Question Categorization**: Automatically categorize questions by type or domain
5. **Historical Tracking**: Store and track audit results over time
6. **User Authentication**: Add login/authentication for multi-user scenarios
7. **Database Storage**: Store audit results in a database for persistence

## API Endpoints

- `GET /` - Serve the main web interface
- `POST /upload` - Upload and process PDF file
  - Request: multipart/form-data with PDF file
  - Response: JSON with extracted questions and analysis results

## License

This project is provided as-is for development purposes.
