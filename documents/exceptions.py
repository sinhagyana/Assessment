import logging

from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger("documents")


def custom_exception_handler(exc, context):
    """
    Wraps DRF's default exception handler to guarantee a consistent
    error response shape: {"error": {"message": ..., "detail": ...}}
    Also catches unhandled exceptions and returns a generic 500 response
    instead of leaking a stack trace.
    """
    response = exception_handler(exc, context)

    if response is not None:
        response.data = {
            "error": {
                "message": "Request failed.",
                "detail": response.data,
            }
        }
        return response

    logger.exception("Unhandled exception in %s", context.get("view"))
    return Response(
        {
            "error": {
                "message": "Internal server error.",
                "detail": str(exc),
            }
        },
        status=500,
    )
