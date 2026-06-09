from rest_framework.exceptions import Throttled
from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None and isinstance(exc, Throttled):
        response.data = {
            "detail": "Rate limit exceeded. Please wait before trying again.",
            "code": "rate_limited",
            "retry_after": exc.wait,
        }
    return response
