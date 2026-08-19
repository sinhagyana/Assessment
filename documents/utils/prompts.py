
SYSTEM_PROMPT = (
    "You are a precise document analysis assistant. You will be given the "
    "raw text of a document. Analyze it and respond with ONLY a valid JSON "
    "object (no markdown fences, no commentary, no preamble) containing "
    "exactly these keys:\n"
    '  "title": a concise descriptive title for the document (string)\n'
    '  "summary": a clear, well-written summary of the document, '
    "3-6 sentences (string)\n"
    '  "keywords": 5-10 relevant keywords or key phrases (array of strings)\n'
    '  "language": the primary language of the document, e.g. "English" '
    "(string)\n"
    "Return valid JSON and nothing else."
)

DOCUMENT_ANALYSIS_PROMPT_TEMPLATE = (
    "Analyze the following document and return the JSON object described "
    "in your instructions.\n\n"
    "--- DOCUMENT START ---\n"
    "{document_text}\n"
    "--- DOCUMENT END ---"
)

MAX_DOCUMENT_CHARS_FOR_LLM = 20000


def build_analysis_prompt(document_text: str) -> str:
    truncated = document_text[:MAX_DOCUMENT_CHARS_FOR_LLM]
    return DOCUMENT_ANALYSIS_PROMPT_TEMPLATE.format(document_text=truncated)
