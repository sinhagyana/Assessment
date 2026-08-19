# Document AI Backend

A Django REST Framework API that accepts a document (PDF, DOCX, or TXT), extracts
its text, sends the content to an LLM (via LangChain), and returns a structured
JSON summary (title, summary, keywords, language, word count).

Authentication is **disabled** for this assessment — all endpoints are open.

## Features

- File upload API for PDF / DOCX / TXT with validation (type, size, empty file).
- Text extraction using `PyPDF2` (PDF) and `python-docx` (DOCX).
- LLM integration via LangChain, provider-agnostic (Anthropic or OpenAI),
  returning structured JSON (title, summary, keywords, language).
- Document metadata, extracted text, LLM response, status, and timestamps
  persisted in the database.
- List and detail APIs for processed documents.
- Consistent error handling for invalid files, empty documents, LLM/API
  failures, and malformed LLM JSON responses.

### Bonus features implemented (2 of the listed options)

1. **Retry logic for LLM calls** — `documents/utils/llm_service.py` uses
   `tenacity` to retry transient errors (timeouts, rate limits, connection
   issues) with exponential backoff, configurable via `LLM_MAX_RETRIES`
   and `LLM_TIMEOUT_SECONDS`.
2. **Configurable prompt templates** — prompts live in
   `documents/utils/prompts.py`, separate from application logic, so they
   can be tuned without touching request-handling code.

Additionally implemented for robustness (not counted toward the "any two"
bonus, but included): **unit tests** (`documents/tests/`) and a
**structured logging middleware** (`documents/middleware.py`), plus
**Docker support** (`Dockerfile` / `docker-compose.yml`).

## Project Structure

```
doc_ai_api/
├── doc_ai_api/              # Django project config (settings, urls, wsgi/asgi)
├── documents/                # Main app
│   ├── models.py             # Document model
│   ├── serializers.py        # DRF serializers
│   ├── views.py               # Upload / List / Detail API views
│   ├── urls.py
│   ├── services.py           # Orchestrates extraction + LLM pipeline
│   ├── exceptions.py         # Custom DRF exception handler
│   ├── middleware.py         # Request logging middleware
│   ├── admin.py
│   ├── utils/
│   │   ├── text_extraction.py
│   │   ├── llm_service.py    # LangChain-based LLM integration + retries
│   │   └── prompts.py        # Configurable prompt templates
│   └── tests/                # Unit + API tests
├── media/uploads/            # Uploaded files stored here
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
source venv/bin/activate   # Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your values (see table below).

### 4. Run migrations

```bash
python manage.py migrate
```

### 5. (Optional) Create a superuser for the Django admin

```bash
python manage.py createsuperuser
```

### 6. Run the development server

```bash
python manage.py runserver
```

The API is now available at `http://127.0.0.1:8000/api/`.

### Running with Docker

```bash
cp .env.example .env   # fill in your LLM API key
docker compose up --build
```

### Running tests

```bash
python manage.py test documents
```

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | Django secret key | — |
| `DEBUG` | Debug mode | `True` |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts | `127.0.0.1,localhost` |
| `LLM_PROVIDER` | `anthropic` or `openai` | `anthropic` |
| `ANTHROPIC_API_KEY` | Anthropic API key (if using Anthropic) | — |
| `ANTHROPIC_MODEL` | Anthropic model name | `claude-sonnet-4-6` |
| `OPENAI_API_KEY` | OpenAI API key (if using OpenAI) | — |
| `OPENAI_MODEL` | OpenAI model name | `gpt-4o-mini` |
| `LLM_MAX_RETRIES` | Max retry attempts for transient LLM errors | `3` |
| `LLM_TIMEOUT_SECONDS` | Per-request LLM timeout | `60` |
| `MAX_UPLOAD_SIZE_MB` | Max allowed upload size in MB | `10` |

## API Reference

Base URL: `/api/`

### 1. Upload a document

`POST /api/documents/upload/`

**Request:** `multipart/form-data`

| Field | Type | Required |
|---|---|---|
| `file` | file (.pdf, .docx, .txt) | yes |

**Sample request (cURL):**

```bash
curl -X POST http://127.0.0.1:8000/api/documents/upload/ \
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
  "llm_keywords": ["finance", "quarterly report", "revenue", "growth"],
  "llm_language": "English",
  "status": "completed",
  "error_message": "",
  "created_at": "2026-08-19T10:00:00Z",
  "updated_at": "2026-08-19T10:00:05Z",
  "processed_at": "2026-08-19T10:00:05Z"
}
```

If extraction or the LLM call fails, the document is still saved
(`status: "failed"`, `error_message` populated) and the API responds with
`422 Unprocessable Entity`.

**Sample validation error response (`400 Bad Request`):**

```json
{
  "error": {
    "message": "Request failed.",
    "detail": {
      "file": ["Unsupported file type '.exe'. Allowed types: .pdf, .docx, .txt"]
    }
  }
}
```

### 2. List documents

`GET /api/documents/`

Optional query param: `?status=completed|pending|processing|failed`

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

### 3. Retrieve document detail

`GET /api/documents/<uuid:id>/`

Returns the full record, including `extracted_text` and the complete LLM
analysis (same shape as the upload response).

## Error Handling

All errors follow a consistent shape:

```json
{ "error": { "message": "...", "detail": "..." } }
```

Handled cases:
- Missing / unsupported file type
- Empty file / empty extracted text
- File exceeding `MAX_UPLOAD_SIZE_MB`
- LLM API failures (after retries) — document is marked `failed` with
  `error_message` set, rather than raising a 500
- Malformed / non-JSON LLM responses — parsed defensively, and treated as
  a failure if parsing is impossible
- Document not found — standard `404`
- Any unhandled exception — caught by the custom DRF exception handler and
  returned as a generic `500` rather than leaking a stack trace

## Design Notes

- **Processing model:** the current implementation processes documents
  synchronously within the upload request for simplicity in this
  assessment. The pipeline (`documents/services.py`) is isolated from the
  view layer specifically so it can be dropped into a Celery task with
  minimal changes if asynchronous processing is required.
- **LLM provider abstraction:** `llm_service.py` builds a LangChain chat
  model based on `LLM_PROVIDER`, so switching between Anthropic and OpenAI
  (or adding another provider) requires no changes to calling code.
- **Prompts as configuration:** all prompt text lives in `prompts.py` and
  is model/logic-agnostic, so prompt engineering iteration doesn't touch
  the service layer.
