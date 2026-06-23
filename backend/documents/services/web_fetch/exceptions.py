from rest_framework.exceptions import APIException


class WebFetchError(Exception):
    default_message = "Could not import this webpage."

    def __init__(self, message: str | None = None):
        super().__init__(message or self.default_message)
        self.message = message or self.default_message


class URLValidationError(WebFetchError):
    default_message = "Enter a valid public HTTP or HTTPS URL."


class BlockedDestinationError(WebFetchError):
    default_message = "This URL is not allowed. Use a public webpage URL."


class RobotsDeniedError(WebFetchError):
    default_message = "This page is disallowed by robots.txt for this application."


class FetchTimeoutError(WebFetchError):
    default_message = "The webpage took too long to respond."


class FetchNetworkError(WebFetchError):
    default_message = "The webpage could not be reached."


class FetchHTTPError(WebFetchError):
    default_message = "The webpage returned an unsuccessful HTTP response."


class RedirectError(WebFetchError):
    default_message = "The webpage redirects to an unsupported or unsafe destination."


class OversizedResponseError(WebFetchError):
    default_message = "The webpage is too large to import."


class UnsupportedContentTypeError(WebFetchError):
    default_message = "Only public HTML webpages can be imported."


class ExtractionError(WebFetchError):
    default_message = "The webpage does not contain enough readable text to import."


class DuplicateURLError(APIException):
    status_code = 409
    default_detail = "This URL has already been imported."
    default_code = "duplicate_url"
