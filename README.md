# Document AI Backend

A Django REST Framework API that accepts a document (PDF, DOCX, or TXT), extracts its text, sends the content to an LLM via LangChain, and returns a structured JSON analysis containing title, summary, keywords, language, and word count.

Authentication is **disabled** for this assessment — all endpoints are open.

## Features

* File upload API for PDF / DOCX / TXT with validation (type, size, empty file).
* Text extraction using `PyPDF2` (PDF) and `python-docx` (DOCX).
* LLM integration via LangChain with configurable providers including **Groq, Anthropic, and OpenAI**.
* Groq integration using `langchain-groq`.
* Structured LLM output containing title, summary, keywords, and language.
* Document metadata, extracted text, LLM response, status, and timestamps persisted in the database.
* List and detail APIs for processed documents.
* Consistent error handling for invalid files, empty documents, LLM/API failures, and malformed LLM JSON responses.

### Bonus features implemented (2 of the listed options)

1. **Retry logic for LLM calls** — `documents/utils/llm_service.py` uses `tenacity` to retry transient errors such as timeouts, rate limits, and connection issues with exponential backoff. Retry behavior is configurable through `LLM_MAX_RETRIES` and `LLM_TIMEOUT_SECONDS`.

2. **Configurable prompt templates** — prompts live in `documents/utils/prompts.py`, separate from application logic, so they can be tuned without modifying request-handling code.

Additionally implemented for robustness (not counted toward the "any two" bonus, but included):

* **Unit tests** in `documents/tests/`
* **Structured logging middleware** in `documents/middleware.py`
* **Docker support** using `Dockerfile` and `docker-compose.yml`

## Project Structure

```text
doc_ai_api/
├── doc_ai_api/              # Django project config (settings, urls, wsgi/asgi)
├── documents/               # Main app
│   ├── models.py            # Document model
│   ├── serializers.py       # DRF serializers
│   ├── views.py             # Upload / List / Detail API views
│   ├── urls.py
│   ├── services.py          # Orchestrates extraction + LLM pipeline
│   ├── exceptions.py        # Custom DRF exception handler
│   ├── middleware.py        # Request logging middleware
│   ├── admin.py
│   ├── utils/
│   │   ├── text_extraction.py
│   │   ├── llm_service.py   # LangChain LLM integration + retries
│   │   └── prompts.py       # Configurable prompt templates
│   └── tests/               # Unit + API tests
├── media/uploads/           # Uploaded files stored here
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── postman_collection.json
└── README.md
```

## Setup Instructions

### 1. Clone and create a virtual environment

```bash
git clone <your-repo-url>
cd doc_ai_api
python -m venv venv
```

#### Windows

```powershell
venv\Scripts\activate
```

#### Linux / macOS

```bash
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

The project uses `langchain-groq` for Groq integration.

### 3. Configure environment variables

Copy the example environment file:

#### Windows

```powershell
copy .env.example .env
```

#### Linux / macOS

```bash
cp .env.example .env
```

Then edit `.env` and configure your LLM provider.

For Groq:

```env
LLM_PROVIDER=groq
GROQ_API_KEY=your-groq-api-key
GROQ_MODEL=openai/gpt-oss-120b
```

> **Security:** Never commit your `.env` file or expose your API key in source code or version control.

### 4. Run migrations

```bash
python manage.py migrate
```

### 5. Optional: Create a superuser

```bash
python manage.py createsuperuser
```

### 6. Run the development server

```bash
python manage.py runserver
```

The API is available at:

```text
http://127.0.0.1:8000/api/
```

### Running with Docker

Create and configure your `.env` file:

```bash
cp .env.example .env
```

Then run:

```bash
docker compose up --build
```

Make sure the required LLM API key is configured in `.env`.

### Running tests

```bash
python manage.py test documents
```

## Environment Variables

| Variable              | Description                                     | Default               |
| --------------------- | ----------------------------------------------- | --------------------- |
| `SECRET_KEY`          | Django secret key                               | —                     |
| `DEBUG`               | Django debug mode                               | `True`                |
| `ALLOWED_HOSTS`       | Comma-separated allowed hosts                   | `127.0.0.1,localhost` |
| `LLM_PROVIDER`        | LLM provider: `groq`                            | `groq`                |
| `GROQ_API_KEY`        | Groq API key when using Groq                    | —                     |
| `GROQ_MODEL`          | Groq model name                                 | `openai/gpt-oss-120b` |
| `LLM_MAX_RETRIES`     | Maximum retry attempts for transient LLM errors | `3`                   |
| `LLM_TIMEOUT_SECONDS` | Per-request LLM timeout in seconds              | `60`                  |
| `MAX_UPLOAD_SIZE_MB`  | Maximum allowed upload size in MB               | `10`                  |

### Groq Configuration

The current configuration uses Groq:

```env
LLM_PROVIDER=groq
GROQ_API_KEY=your-groq-api-key
GROQ_MODEL=openai/gpt-oss-120b
```

The application uses LangChain's `ChatGroq` integration to communicate with the Groq API.

The model can be changed through the `GROQ_MODEL` environment variable without changing application code, provided the selected model is available to the configured Groq account.

## API Reference

Base URL:

```text
/api/
```

### 1. Upload a Document

`POST /api/documents/upload/`

Uploads a PDF, DOCX, or TXT file, extracts its text, sends the extracted content to the configured LLM, and returns the processed document record.

**Request:**

`multipart/form-data`

| Field  | Type                           | Required |
| ------ | ------------------------------ | -------- |
| `file` | file (`.pdf`, `.docx`, `.txt`) | yes      |

**cURL — Windows PowerShell:**

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/documents/upload/" -F "file=@sample.pdf"
```

**cURL — Linux / macOS:**

```bash
curl -X POST "http://127.0.0.1:8000/api/documents/upload/" \
  -F "file=@sample.pdf"
```

**Sample success response (`201 Created`):**

```json
{
  "id": "b3f1c2a4-1234-4a5b-8b1e-abcdef123456",
  "original_filename": "sample.pdf",
  "file": "/media/uploads/9f8a7b6c.pdf",
  "file_type": ".pdf",
  "file_size": 24576,
  "extracted_text": "Full extracted text of the document...",
  "word_count": 812,
  "llm_title": "Quarterly Financial Report Summary",
  "llm_summary": "This document outlines Q2 financial results...",
  "llm_keywords": [
    "finance",
    "quarterly report",
    "revenue",
    "growth"
  ],
  "llm_language": "English",
  "status": "completed",
  "error_message": "",
  "created_at": "2026-08-19T10:00:00Z",
  "updated_at": "2026-08-19T10:00:05Z",
  "processed_at": "2026-08-19T10:00:05Z"
}
```

If extraction or the LLM call fails, the document is still saved with:

```json
{
  "status": "failed",
  "error_message": "..."
}
```

The API responds with `422 Unprocessable Entity`.

**Sample validation error response (`400 Bad Request`):**

```json
{
  "error": {
    "message": "Request failed.",
    "detail": {
      "file": [
        "Unsupported file type '.exe'. Allowed types: .pdf, .docx, .txt"
      ]
    }
  }
}
```

### 2. List Documents

`GET /api/documents/`

Optional query parameter:

```text
?status=completed
```

Supported status values:

```text
completed
pending
processing
failed
```

**Sample response (`200 OK`):**

```json
[
  {
    "id": "b3f1c2a4-1234-4a5b-8b1e-abcdef123456",
    "original_filename": "sample.pdf",
    "file_type": ".pdf",
    "file_size": 24576,
    "status": "completed",
    "llm_title": "Quarterly Financial Report Summary",
    "word_count": 812,
    "created_at": "2026-08-19T10:00:00Z",
    "updated_at": "2026-08-19T10:00:05Z"
  }
]
```

### 3. Retrieve Document Detail

`GET /api/documents/<uuid:id>/`

Returns the complete document record, including extracted text and LLM analysis.

## Error Handling

All errors follow a consistent response format:

```json
{
  "error": {
    "message": "...",
    "detail": "..."
  }
}
```

Handled cases include:

* Missing file
* Unsupported file type
* Empty file
* Empty extracted text
* File exceeding `MAX_UPLOAD_SIZE_MB`
* LLM API failures
* LLM authentication/configuration failures
* LLM model errors
* LLM rate limits and transient failures
* Malformed or non-JSON LLM responses
* Document not found
* Unexpected server exceptions

LLM failures are handled gracefully. The document is persisted with `status: "failed"` and the relevant error is stored in `error_message` instead of leaking an internal stack trace.

## Design Notes

### Processing Model

The current implementation processes documents synchronously within the upload request for simplicity in this assessment.

The processing pipeline is isolated in:

```text
documents/services.py
```

This separation makes it possible to move document processing into a Celery background task with minimal changes if asynchronous processing is required.

### LLM Provider Abstraction

LLM integration is isolated in:

```text
documents/utils/llm_service.py
```

The service builds the appropriate LangChain chat model based on `LLM_PROVIDER`.

Supported providers:

```text
groq
```

For example:

```env
LLM_PROVIDER=groq
GROQ_MODEL=openai/gpt-oss-120b
```

Changing the provider does not require changes to the API views or document-processing pipeline.

### Prompt Configuration

All prompt templates are maintained in:

```text
documents/utils/prompts.py
```

This keeps prompt engineering separate from application and request-handling logic.

### Retry and Resilience

Transient LLM errors such as timeouts, rate limits, and temporary connection failures are retried using `tenacity` with exponential backoff.

Retry behavior is configurable through:

```env
LLM_MAX_RETRIES=3
LLM_TIMEOUT_SECONDS=60
```

### Database Persistence

Each uploaded document stores:

* Original filename
* Uploaded file
* File type
* File size
* Extracted text
* Word count
* LLM-generated title
* LLM-generated summary
* LLM-generated keywords
* Detected language
* Processing status
* Error message, if any
* Creation timestamp
* Update timestamp
* Processing timestamp

## Example Processing Flow

```text
Client
   |
   | POST /api/documents/upload/
   v
Django REST Framework
   |
   v
File Validation
   |
   v
Text Extraction
   |
   +---- PDF  -> PyPDF2
   |
   +---- DOCX -> python-docx
   |
   +---- TXT  -> text decoding
   |
   v
LLM Service
   |
   v
LangChain
   |
   v
Groq / Anthropic / OpenAI
   |
   v
Structured JSON
   |
   v
Database
   |
   v
API Response
```

## Security Notes

* Authentication is intentionally disabled for this assessment.
* API keys must be stored in environment variables.
* `.env` should never be committed to version control.
* Do not hard-code LLM API keys in Python source files.
* Uploaded documents should be handled according to the security requirements of the deployment environment.

## Docker Support

The project includes:

```text
Dockerfile
docker-compose.yml
```

To run the application using Docker:

```bash
docker compose up --build
```

Configure the required environment variables in `.env` before starting the containers.

## Testing

Run the complete test suite with:

```bash
python manage.py test documents
```

The test suite covers document validation, API behavior, extraction, and LLM-related processing.

## Current LLM Configuration

The default configuration for this project is:

```env
LLM_PROVIDER=groq
GROQ_MODEL=openai/gpt-oss-120b
```

The Groq API key should be supplied through:

```env
GROQ_API_KEY=your-groq-api-key
```

No API key should be committed to the repository.
