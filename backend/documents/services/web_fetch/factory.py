from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from documents.services.web_fetch.base import WebFetchProvider
from documents.services.web_fetch.direct import DirectWebFetchProvider


def get_web_fetch_provider() -> WebFetchProvider:
    provider = settings.WEB_FETCH_PROVIDER.strip().lower()
    if provider == "direct":
        return DirectWebFetchProvider()
    raise ImproperlyConfigured(f"Unsupported WEB_FETCH_PROVIDER: {settings.WEB_FETCH_PROVIDER}")
