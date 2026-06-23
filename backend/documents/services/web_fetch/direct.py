import ipaddress
import socket
from datetime import UTC, datetime
from urllib.parse import urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

import httpx
from django.conf import settings

from documents.services.web_fetch.base import FetchResult
from documents.services.web_fetch.exceptions import (
    BlockedDestinationError,
    FetchHTTPError,
    FetchNetworkError,
    FetchTimeoutError,
    OversizedResponseError,
    RedirectError,
    RobotsDeniedError,
    UnsupportedContentTypeError,
    URLValidationError,
)


SAFE_PORTS = {80, 443}


class DirectWebFetchProvider:
    provider_name = "direct"

    def fetch(self, url: str) -> FetchResult:
        target_url = normalize_url_for_fetch(url)
        self._check_robots(target_url)
        return self._fetch_url(
            target_url,
            max_bytes=settings.URL_INGESTION_MAX_BYTES,
            require_html=True,
        )

    def _check_robots(self, target_url: str) -> None:
        parts = urlsplit(target_url)
        robots_url = urlunsplit((parts.scheme, parts.netloc, "/robots.txt", "", ""))
        try:
            result = self._fetch_url(
                robots_url,
                max_bytes=settings.URL_INGESTION_ROBOTS_MAX_BYTES,
                require_html=False,
                allow_http_errors=True,
            )
        except (FetchTimeoutError, FetchNetworkError, FetchHTTPError, OversizedResponseError):
            return

        if result.status_code >= 400:
            return

        parser = RobotFileParser()
        parser.set_url(robots_url)
        try:
            parser.parse(result.body.decode("utf-8", errors="ignore").splitlines())
        except Exception:
            return

        if not parser.can_fetch(settings.URL_INGESTION_USER_AGENT, target_url):
            raise RobotsDeniedError()

    def _fetch_url(
        self,
        url: str,
        *,
        max_bytes: int,
        require_html: bool,
        allow_http_errors: bool = False,
    ) -> FetchResult:
        requested_url = normalize_url_for_fetch(url)
        current_url = requested_url
        visited = set()

        for redirect_count in range(settings.URL_INGESTION_MAX_REDIRECTS + 1):
            validate_public_url(current_url)
            normalized_current = normalize_url_for_dedup(current_url)
            if normalized_current in visited:
                raise RedirectError("The webpage redirects in a loop.")
            visited.add(normalized_current)

            try:
                response = self._send_request(current_url, max_bytes=max_bytes)
            except httpx.TimeoutException as exc:
                raise FetchTimeoutError() from exc
            except (httpx.HTTPError, OSError) as exc:
                raise FetchNetworkError() from exc

            if 300 <= response.status_code < 400 and response.headers.get("location"):
                if redirect_count >= settings.URL_INGESTION_MAX_REDIRECTS:
                    raise RedirectError("The webpage exceeded the redirect limit.")
                current_url = normalize_url_for_fetch(str(response.url.join(response.headers["location"])))
                continue

            if not allow_http_errors and response.status_code >= 400:
                raise FetchHTTPError("The webpage returned an unsuccessful HTTP response.")

            content_type = response.headers.get("content-type", "")
            if require_html and not is_html_content_type(content_type):
                raise UnsupportedContentTypeError()

            return FetchResult(
                requested_url=requested_url,
                final_url=normalize_url_for_dedup(str(response.url)),
                status_code=response.status_code,
                content_type=content_type,
                body=response.content,
                headers={"content-type": content_type},
                fetched_at=datetime.now(UTC),
                provider=self.provider_name,
            )

        raise RedirectError("The webpage exceeded the redirect limit.")

    def _send_request(self, url: str, *, max_bytes: int) -> httpx.Response:
        headers = {"User-Agent": settings.URL_INGESTION_USER_AGENT}
        timeout = httpx.Timeout(settings.URL_INGESTION_TIMEOUT_SECONDS)
        with httpx.Client(follow_redirects=False, timeout=timeout, headers=headers) as client:
            with client.stream("GET", url) as response:
                chunks = []
                total_bytes = 0
                for chunk in response.iter_bytes():
                    total_bytes += len(chunk)
                    if total_bytes > max_bytes:
                        raise OversizedResponseError()
                    chunks.append(chunk)
                return httpx.Response(
                    status_code=response.status_code,
                    headers=response.headers,
                    content=b"".join(chunks),
                    request=response.request,
                    extensions=response.extensions,
                )


def normalize_url_for_fetch(url: str) -> str:
    raw_url = url.strip()
    try:
        parts = urlsplit(raw_url)
    except ValueError as exc:
        raise URLValidationError() from exc

    if parts.scheme.lower() not in {"http", "https"}:
        raise URLValidationError("Only HTTP and HTTPS URLs can be imported.")
    if not parts.hostname:
        raise URLValidationError()
    if parts.username or parts.password:
        raise BlockedDestinationError("URLs with embedded credentials are not allowed.")
    try:
        port = parts.port
    except ValueError as exc:
        raise BlockedDestinationError("This URL uses an invalid port.") from exc
    if port is not None and port not in SAFE_PORTS:
        raise BlockedDestinationError("This URL uses an unsupported port.")

    hostname = parts.hostname.lower().encode("idna").decode("ascii")
    netloc = hostname
    if port and not is_default_port(parts.scheme.lower(), port):
        netloc = f"{hostname}:{port}"
    path = parts.path or "/"
    return urlunsplit((parts.scheme.lower(), netloc, path, parts.query, ""))


def normalize_url_for_dedup(url: str) -> str:
    normalized = normalize_url_for_fetch(url)
    parts = urlsplit(normalized)
    return urlunsplit((parts.scheme, parts.netloc, parts.path or "/", parts.query, ""))


def validate_public_url(url: str) -> None:
    parts = urlsplit(normalize_url_for_fetch(url))
    hostname = parts.hostname or ""
    if hostname == "localhost" or hostname.endswith(".localhost"):
        raise BlockedDestinationError()

    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        for resolved in resolve_hostname(hostname):
            validate_public_ip(resolved)
    else:
        validate_public_ip(address)


def resolve_hostname(hostname: str) -> list[ipaddress.IPv4Address | ipaddress.IPv6Address]:
    try:
        infos = socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise FetchNetworkError("The URL hostname could not be resolved.") from exc

    addresses = []
    for info in infos:
        sockaddr = info[4]
        addresses.append(ipaddress.ip_address(sockaddr[0]))
    if not addresses:
        raise FetchNetworkError("The URL hostname could not be resolved.")
    return addresses


def validate_public_ip(address: ipaddress.IPv4Address | ipaddress.IPv6Address) -> None:
    if (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
        or not address.is_global
    ):
        raise BlockedDestinationError()


def is_default_port(scheme: str, port: int) -> bool:
    return (scheme == "http" and port == 80) or (scheme == "https" and port == 443)


def is_html_content_type(content_type: str) -> bool:
    return "text/html" in content_type.lower() or "application/xhtml+xml" in content_type.lower()
