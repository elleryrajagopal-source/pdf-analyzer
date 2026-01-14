# Audit Question Analyzer

A web application that extracts audit questions from PDF documents and analyzes whether each requirement is met.

## Features

- 📄 PDF document upload and text extraction
- 🔍 Automatic question extraction using pattern matching
- ✅ Requirement status analysis for each question
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

4. **Open your browser and navigate to:**
   ```
   http://localhost:8000
   ```

## Usage

1. Upload a PDF document containing audit questions
2. The app will automatically extract questions from the document
3. Each question will be analyzed to determine if the requirement is met
4. View the results with statistics and detailed analysis

## How It Works

### Question Extraction

The app uses pattern matching to identify questions in the PDF text:
- Numbered questions (1., 2., etc.)
- Questions ending with question marks
- Common audit question patterns (Does..., Is there..., Are..., etc.)

### Requirement Analysis

Currently, the app uses keyword-based analysis to determine requirement status. For production use, you may want to:

- Integrate with an LLM API (OpenAI, Anthropic, etc.) for more sophisticated analysis
- Add evidence/documentation review capabilities
- Implement custom business logic for your specific audit requirements

## Project Structure

```
audit-analyzer/
├── app.py              # FastAPI backend application
├── static/
│   └── index.html      # Frontend web interface
├── requirements.txt    # Python dependencies
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
