import json
import logging
import re

from django.conf import settings

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .prompts import SYSTEM_PROMPT, build_analysis_prompt


logger = logging.getLogger("documents")


class LLMServiceError(Exception):
    """Raised when the LLM call fails or response parsing fails."""


class TransientLLMError(Exception):
    """Raised for retryable LLM errors."""


def _get_chat_model():
    provider = settings.LLM_PROVIDER.lower()

    if provider == "groq":

        from langchain_groq import ChatGroq

        if not settings.GROQ_API_KEY:
            raise LLMServiceError(
                "GROQ_API_KEY is not configured."
            )

        return ChatGroq(
            model=settings.GROQ_MODEL,
            groq_api_key=settings.GROQ_API_KEY,
            temperature=0,
            max_tokens=1024,
            timeout=settings.LLM_TIMEOUT_SECONDS,
        )


def _extract_json(raw_text: str) -> dict:

    text = raw_text.strip()

    # Remove markdown code fences
    fence_match = re.search(
        r"```(?:json)?\s*(.*?)\s*```",
        text,
        re.DOTALL,
    )

    if fence_match:
        text = fence_match.group(1).strip()

    # Try direct JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting JSON object
    brace_match = re.search(
        r"\{.*\}",
        text,
        re.DOTALL,
    )

    if brace_match:

        try:
            return json.loads(
                brace_match.group(0)
            )

        except json.JSONDecodeError as exc:

            raise LLMServiceError(
                f"LLM response is not valid JSON: {exc}"
            ) from exc

    raise LLMServiceError(
        "LLM response did not contain a JSON object."
    )


@retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(
        multiplier=1,
        min=1,
        max=10,
    ),
    retry=retry_if_exception_type(
        TransientLLMError
    ),
)
def _call_llm(model, messages):

    try:

        return model.invoke(messages)

    except Exception as exc:

        message = str(exc).lower()

        transient_markers = (
            "timeout",
            "timed out",
            "rate limit",
            "429",
            "overloaded",
            "connection",
            "temporarily",
            "503",
            "502",
        )

        if any(
            marker in message
            for marker in transient_markers
        ):

            logger.warning(
                "Transient LLM error, will retry: %s",
                exc,
            )

            raise TransientLLMError(
                str(exc)
            ) from exc

        raise LLMServiceError(
            f"LLM call failed: {exc}"
        ) from exc


def analyze_document(document_text: str) -> dict:

    max_retries = settings.LLM_MAX_RETRIES

    @retry(
        reraise=True,
        stop=stop_after_attempt(max_retries),
        wait=wait_exponential(
            multiplier=1,
            min=1,
            max=10,
        ),
        retry=retry_if_exception_type(
            TransientLLMError
        ),
    )
    def _run():

        model = _get_chat_model()

        prompt = build_analysis_prompt(
            document_text
        )

        messages = [
            (
                "system",
                SYSTEM_PROMPT,
            ),
            (
                "human",
                prompt,
            ),
        ]

        response = _call_llm(
            model,
            messages,
        )

        raw_content = (
            response.content
            if hasattr(response, "content")
            else str(response)
        )

        # Some LangChain providers may return
        # content as a list of blocks.
        if isinstance(raw_content, list):

            raw_content = "".join(
                block.get("text", "")
                if isinstance(block, dict)
                else str(block)
                for block in raw_content
            )

        parsed = _extract_json(
            raw_content
        )

        required_keys = {
            "title",
            "summary",
            "keywords",
            "language",
        }

        missing = (
            required_keys - parsed.keys()
        )

        if missing:

            raise LLMServiceError(
                f"LLM response missing keys: {missing}"
            )

        if not isinstance(
            parsed.get("keywords"),
            list,
        ):

            parsed["keywords"] = [
                str(
                    parsed.get("keywords")
                )
            ]

        return parsed

    try:

        result = _run()

    except TransientLLMError as exc:

        raise LLMServiceError(
            f"LLM call failed after "
            f"{max_retries} retries: {exc}"
        ) from exc

    word_count = (
        len(document_text.split())
        if document_text
        else 0
    )

    return {
        "title": str(
            result.get("title", "")
        ).strip(),

        "summary": str(
            result.get("summary", "")
        ).strip(),

        "keywords": [
            str(k).strip()
            for k in result.get(
                "keywords",
                [],
            )
        ],

        "language": str(
            result.get("language", "")
        ).strip(),

        "word_count": word_count,

        "raw_response": result,
    }