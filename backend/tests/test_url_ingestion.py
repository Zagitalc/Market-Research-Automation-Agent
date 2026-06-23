import socket

import httpx
import pytest
from django.core.cache import cache
from django.db import IntegrityError
from django.test import override_settings
from rest_framework.test import APIClient

from documents.models import Document, DocumentChunk
from documents.services.web_fetch import direct
from documents.services.web_fetch.exceptions import BlockedDestinationError


URL_THROTTLE_SETTINGS = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "1000/min",
        "research_run_create": "1000/min",
        "document_create": "1000/min",
        "document_url_create": "1/min",
    },
    "EXCEPTION_HANDLER": "config.exceptions.api_exception_handler",
}


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture(autouse=True)
def public_dns(monkeypatch):
    cache.clear()
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *args, **kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))
        ],
    )


def response(url: str, status_code: int, body: bytes, content_type: str, **headers) -> httpx.Response:
    return httpx.Response(
        status_code,
        headers={"content-type": content_type, **headers},
        content=body,
        request=httpx.Request("GET", url),
    )


def url_error(response) -> str:
    error = response.json()["url"]
    return error[0] if isinstance(error, list) else error


def mock_fetch(monkeypatch, responses: dict[str, httpx.Response], seen: list[str] | None = None):
    def fake_send(self, url: str, *, max_bytes: int):
        if seen is not None:
            seen.append(url)
        return responses[url]

    monkeypatch.setattr(direct.DirectWebFetchProvider, "_send_request", fake_send)


@pytest.mark.django_db
def test_url_import_example_dot_com_root_with_robots_404_allowed(api_client, monkeypatch):
    mock_fetch(
        monkeypatch,
        {
            "https://example.com/robots.txt": response(
                "https://example.com/robots.txt", 404, b"", "text/plain"
            ),
            "https://example.com/": response(
                "https://example.com/",
                200,
                b"""
                <html>
                  <head><title>Example Domain</title></head>
                  <body><h1>Example Domain</h1><p>This domain is for use in illustrative examples in documents.</p></body>
                </html>
                """,
                "text/html; charset=utf-8",
            ),
        },
    )

    create_response = api_client.post(
        "/api/documents/url/",
        {"url": "https://example.com/"},
        format="json",
    )

    assert create_response.status_code == 201
    body = create_response.json()
    assert body["title"] == "Example Domain"
    assert body["source_url"] == "https://example.com/"
    assert body["source_domain"] == "example.com"
    assert "illustrative examples" in body["content"]
    assert Document.objects.count() == 1
    assert DocumentChunk.objects.count() == 1


@pytest.mark.django_db
def test_url_import_creates_document_metadata_chunks_and_embeddings(api_client, monkeypatch):
    mock_fetch(
        monkeypatch,
        {
            "https://example.com/robots.txt": response(
                "https://example.com/robots.txt",
                200,
                b"User-agent: *\nAllow: /\n",
                "text/plain",
            ),
            "https://example.com/article": response(
                "https://example.com/article",
                200,
                b"""
                <html>
                  <head><title>Extracted page title</title><script>bad()</script></head>
                  <body><article><h1>AI tools adoption</h1><p>AI research tools are being adopted fastest by marketing and retail teams.</p></article></body>
                </html>
                """,
                "text/html; charset=utf-8",
            ),
        },
    )

    create_response = api_client.post(
        "/api/documents/url/",
        {"url": "https://example.com/article"},
        format="json",
    )

    assert create_response.status_code == 201
    body = create_response.json()
    assert body["title"] == "Extracted page title"
    assert body["source_type"] == "url"
    assert body["source_kind"] == "url"
    assert body["source_url"] == "https://example.com/article"
    assert body["source_domain"] == "example.com"
    assert body["fetch_provider"] == "direct"
    assert body["http_status"] == 200
    assert body["content_type"] == "text/html; charset=utf-8"
    assert body["fetched_at"]
    assert body["chunks"][0]["embedding"]
    assert "source_file" not in body
    assert "bad()" not in body["content"]
    assert "AI research tools" in body["content"]


@pytest.mark.django_db
def test_url_import_uses_supplied_title(api_client, monkeypatch):
    mock_fetch(
        monkeypatch,
        {
            "https://example.com/robots.txt": response(
                "https://example.com/robots.txt", 404, b"", "text/plain"
            ),
            "https://example.com/report": response(
                "https://example.com/report",
                200,
                b"<html><head><title>Ignored title</title></head><body><p>Readable market research evidence.</p></body></html>",
                "text/html",
            ),
        },
    )

    create_response = api_client.post(
        "/api/documents/url/",
        {"url": "https://example.com/report", "title": "  Custom title  "},
        format="json",
    )

    assert create_response.status_code == 201
    assert create_response.json()["title"] == "Custom title"


@pytest.mark.django_db
def test_robots_network_failure_allows_target_fetch(api_client, monkeypatch):
    seen = []

    def fake_send(self, url: str, *, max_bytes: int):
        seen.append(url)
        if url == "https://example.com/robots.txt":
            raise httpx.ConnectError("robots connection failed", request=httpx.Request("GET", url))
        return response(
            "https://example.com/report",
            200,
            b"<html><body><p>Readable market research evidence from a public page.</p></body></html>",
            "text/html",
        )

    monkeypatch.setattr(direct.DirectWebFetchProvider, "_send_request", fake_send)

    create_response = api_client.post(
        "/api/documents/url/",
        {"url": "https://example.com/report"},
        format="json",
    )

    assert create_response.status_code == 201
    assert seen == ["https://example.com/robots.txt", "https://example.com/report"]
    assert Document.objects.count() == 1


def test_send_request_does_not_double_decode_compressed_response(monkeypatch):
    body = b"<html><body><p>Readable compressed response body.</p></body></html>"

    class FakeStreamResponse:
        def __init__(self, url: str):
            self.status_code = 200
            self.headers = httpx.Headers(
                {
                    "content-type": "text/html",
                    "content-encoding": "gzip",
                    "content-length": "999",
                    "transfer-encoding": "chunked",
                }
            )
            self.request = httpx.Request("GET", url)
            self.extensions = {}

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def iter_bytes(self):
            yield body

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def stream(self, method: str, url: str):
            return FakeStreamResponse(url)

    monkeypatch.setattr(direct.httpx, "Client", FakeClient)

    fetched_response = direct.DirectWebFetchProvider()._send_request(
        "https://example.com/",
        max_bytes=1024,
    )

    assert fetched_response.content == body
    assert fetched_response.headers["content-type"] == "text/html"
    assert "content-encoding" not in fetched_response.headers
    assert fetched_response.headers["content-length"] == str(len(body))
    assert "transfer-encoding" not in fetched_response.headers


@pytest.mark.django_db
def test_duplicate_normalized_url_returns_conflict(api_client, monkeypatch):
    Document.objects.create(
        title="Existing",
        source_type="url",
        source_kind=Document.SourceKind.URL,
        source_url="https://example.com/report",
        content="Existing content",
    )

    duplicate_response = api_client.post(
        "/api/documents/url/",
        {"url": "https://EXAMPLE.com/report#section"},
        format="json",
    )

    assert duplicate_response.status_code == 409
    assert "already been imported" in duplicate_response.json()["detail"]


@pytest.mark.django_db
def test_url_uniqueness_constraint_only_applies_to_url_documents():
    Document.objects.create(title="Manual one", source_type="note", content="A", source_url="")
    Document.objects.create(title="Manual two", source_type="note", content="B", source_url="")
    Document.objects.create(
        title="URL one",
        source_type="url",
        source_kind=Document.SourceKind.URL,
        source_url="https://example.com/a",
        content="A",
    )

    with pytest.raises(IntegrityError):
        Document.objects.create(
            title="URL two",
            source_type="url",
            source_kind=Document.SourceKind.URL,
            source_url="https://example.com/a",
            content="B",
        )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "ftp://example.com/file",
        "https://user:pass@example.com",
        "http://localhost",
        "http://127.0.0.1",
        "http://169.254.169.254",
        "http://10.0.0.1",
        "http://192.168.1.1",
        "http://[::1]/",
        "http://[fe80::1]/",
        "http://[2001:db8::1]/",
        "https://example.com:4443/article",
    ],
)
def test_url_import_rejects_unsafe_destinations(api_client, url):
    rejected_response = api_client.post("/api/documents/url/", {"url": url}, format="json")

    assert rejected_response.status_code == 400
    assert Document.objects.count() == 0
    assert DocumentChunk.objects.count() == 0


@pytest.mark.django_db
def test_dns_resolution_to_blocked_address_is_rejected(api_client, monkeypatch):
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *args, **kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.2", 443))
        ],
    )

    rejected_response = api_client.post(
        "/api/documents/url/",
        {"url": "https://example.com/article"},
        format="json",
    )

    assert rejected_response.status_code == 400
    assert Document.objects.count() == 0


def test_public_ip_validation_allows_global_ipv4_and_ipv6():
    direct.validate_public_url("https://8.8.8.8/")
    direct.validate_public_url("https://[2606:2800:220:1:248:1893:25c8:1946]/")


def test_ipv6_literal_normalization_preserves_brackets():
    assert (
        direct.normalize_url_for_fetch("https://[2606:2800:220:1:248:1893:25c8:1946]/")
        == "https://[2606:2800:220:1:248:1893:25c8:1946]/"
    )


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/",
        "http://169.254.169.254/",
        "http://[::1]/",
        "http://[fe80::1]/",
        "http://[2001:db8::1]/",
    ],
)
def test_public_ip_validation_blocks_local_link_local_and_reserved_destinations(url):
    with pytest.raises(BlockedDestinationError):
        direct.validate_public_url(url)


@pytest.mark.django_db
def test_redirect_destination_is_revalidated(api_client, monkeypatch):
    seen = []
    mock_fetch(
        monkeypatch,
        {
            "https://example.com/robots.txt": response(
                "https://example.com/robots.txt", 404, b"", "text/plain"
            ),
            "https://example.com/article": response(
                "https://example.com/article",
                302,
                b"",
                "text/html",
                location="http://127.0.0.1/internal",
            ),
        },
        seen,
    )

    rejected_response = api_client.post(
        "/api/documents/url/",
        {"url": "https://example.com/article"},
        format="json",
    )

    assert rejected_response.status_code == 400
    assert seen == ["https://example.com/robots.txt", "https://example.com/article"]
    assert Document.objects.count() == 0


@pytest.mark.django_db
def test_robots_denial_is_rejected(api_client, monkeypatch):
    mock_fetch(
        monkeypatch,
        {
            "https://example.com/robots.txt": response(
                "https://example.com/robots.txt",
                200,
                b"User-agent: *\nDisallow: /blocked\n",
                "text/plain",
            ),
        },
    )

    rejected_response = api_client.post(
        "/api/documents/url/",
        {"url": "https://example.com/blocked"},
        format="json",
    )

    assert rejected_response.status_code == 400
    assert "robots" in url_error(rejected_response).lower()
    assert Document.objects.count() == 0


@pytest.mark.django_db
def test_non_html_response_creates_no_partial_records(api_client, monkeypatch):
    mock_fetch(
        monkeypatch,
        {
            "https://example.com/robots.txt": response(
                "https://example.com/robots.txt", 404, b"", "text/plain"
            ),
            "https://example.com/data.json": response(
                "https://example.com/data.json",
                200,
                b'{"market": "data"}',
                "application/json",
            ),
        },
    )

    rejected_response = api_client.post(
        "/api/documents/url/",
        {"url": "https://example.com/data.json"},
        format="json",
    )

    assert rejected_response.status_code == 400
    assert "html" in url_error(rejected_response).lower()
    assert Document.objects.count() == 0
    assert DocumentChunk.objects.count() == 0


@pytest.mark.django_db
def test_fetch_network_error_logs_safe_diagnostic(api_client, monkeypatch, caplog):
    def fake_send(self, url: str, *, max_bytes: int):
        if url == "https://example.com/robots.txt":
            return response(url, 404, b"", "text/plain")
        raise httpx.ConnectError(
            "socket failed via 10.0.0.5 with response body <secret>",
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(direct.DirectWebFetchProvider, "_send_request", fake_send)

    with caplog.at_level("WARNING", logger="documents.services.web_fetch.direct"):
        rejected_response = api_client.post(
            "/api/documents/url/",
            {"url": "https://example.com/report?token=secret"},
            format="json",
        )

    assert rejected_response.status_code == 400
    assert url_error(rejected_response) == "The webpage could not be reached."

    fetch_record = next(
        record
        for record in caplog.records
        if getattr(record, "url_ingestion_event", "") == "url_ingestion_fetch_failed"
    )
    assert fetch_record.url_ingestion_reason == "ConnectError"
    assert fetch_record.url_ingestion_host == "example.com"
    assert fetch_record.url_ingestion_query_present is True
    assert "10.0.0.5" not in fetch_record.message
    assert "<secret>" not in fetch_record.message
    assert "token=secret" not in fetch_record.message
    assert Document.objects.count() == 0


@pytest.mark.django_db
@override_settings(REST_FRAMEWORK=URL_THROTTLE_SETTINGS)
def test_url_import_has_dedicated_throttle(api_client, monkeypatch):
    cache.clear()
    mock_fetch(
        monkeypatch,
        {
            "https://example.com/robots.txt": response(
                "https://example.com/robots.txt", 404, b"", "text/plain"
            ),
            "https://example.com/one": response(
                "https://example.com/one",
                200,
                b"<html><body><p>Readable evidence for one import.</p></body></html>",
                "text/html",
            ),
            "https://example.com/two": response(
                "https://example.com/two",
                200,
                b"<html><body><p>Readable evidence for another import.</p></body></html>",
                "text/html",
            ),
        },
    )

    first_response = api_client.post(
        "/api/documents/url/",
        {"url": "https://example.com/one"},
        format="json",
    )
    throttled_response = api_client.post(
        "/api/documents/url/",
        {"url": "https://example.com/two"},
        format="json",
    )

    assert first_response.status_code == 201
    assert throttled_response.status_code == 429
    assert throttled_response.json()["code"] == "rate_limited"
