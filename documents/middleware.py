import logging
import time

logger = logging.getLogger("documents")


class RequestLoggingMiddleware:
    """
    Structured logging middleware that records method, path, status code,
    and duration for every request. (Bonus: Logging Middleware)
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.monotonic()
        response = self.get_response(request)
        duration_ms = (time.monotonic() - start) * 1000

        logger.info(
            "method=%s path=%s status=%s duration_ms=%.2f",
            request.method,
            request.path,
            response.status_code,
            duration_ms,
        )
        return response
