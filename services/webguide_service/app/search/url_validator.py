import asyncio
import ipaddress
import socket
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit

import httpx


@dataclass(frozen=True)
class URLValidationResult:
    is_valid: bool
    status_code: int | None
    final_url: str | None
    reason: str


Resolver = Callable[[str], Awaitable[list[str]]]


async def _resolve_host(host: str) -> list[str]:
    """Resolve a hostname to its IP addresses."""
    loop = asyncio.get_running_loop()
    records = await loop.getaddrinfo(
        host,
        None,
        type=socket.SOCK_STREAM,
    )
    return list({record[4][0] for record in records})


def _is_public_address(address: str) -> bool:
    try:
        return ipaddress.ip_address(address).is_global
    except ValueError:
        return False


class URLValidator:
    def __init__(
        self,
        timeout: float = 5.0,
        max_redirects: int = 3,
        transport: httpx.AsyncBaseTransport | None = None,
        resolver: Resolver = _resolve_host,
    ) -> None:
        if timeout <= 0:
            raise ValueError("timeout must be greater than 0.")
        if max_redirects < 0:
            raise ValueError("max_redirects cannot be negative.")

        self.timeout = timeout
        self.max_redirects = max_redirects
        self.transport = transport
        self.resolver = resolver

    async def _check_url(self, url: str) -> str | None:
        """Return an error reason if the URL is unsafe or malformed."""
        try:
            parsed = urlsplit(url)
            hostname = parsed.hostname
            # Accessing .port also validates the port syntax.
            _ = parsed.port
        except ValueError:
            return "Malformed URL."

        if parsed.scheme.lower() not in {"http", "https"}:
            return "Only HTTP and HTTPS URLs are allowed."

        if not hostname:
            return "URL has no hostname."

        if parsed.username is not None or parsed.password is not None:
            return "URLs containing credentials are not allowed."

        hostname = hostname.lower().rstrip(".")

        if hostname == "localhost" or hostname.endswith(".localhost"):
            return "Localhost URLs are not allowed."

        try:
            addresses = await self.resolver(hostname)
        except (OSError, socket.gaierror):
            return "Could not resolve hostname."

        if not addresses:
            return "Hostname did not resolve to an IP address."

        if any(not _is_public_address(address) for address in addresses):
            return "URL resolves to a non-public IP address."

        return None

    async def validate(self, url: str) -> URLValidationResult:
        if not url.strip():
            return URLValidationResult(False, None, None, "URL cannot be empty.")

        current_url = url.strip()

        async with httpx.AsyncClient(
            timeout=self.timeout,
            transport=self.transport,
            follow_redirects=False,
        ) as client:
            for redirect_count in range(self.max_redirects + 1):
                error = await self._check_url(current_url)
                if error:
                    return URLValidationResult(False, None, current_url, error)

                try:
                    response = await client.head(current_url)

                    # Some websites do not support HEAD.
                    if response.status_code in {405, 501}:
                        async with client.stream(
                            "GET",
                            current_url,
                            headers={"Range": "bytes=0-0"},
                        ) as get_response:
                            status_code = get_response.status_code
                            location = get_response.headers.get("location")
                    else:
                        status_code = response.status_code
                        location = response.headers.get("location")

                except httpx.TimeoutException:
                    return URLValidationResult(
                        False, None, current_url, "Request timed out."
                    )
                except httpx.RequestError:
                    return URLValidationResult(
                        False, None, current_url, "Could not reach the URL."
                    )

                if 300 <= status_code < 400:
                    if not location:
                        return URLValidationResult(
                            False,
                            status_code,
                            current_url,
                            "Redirect response has no destination.",
                        )

                    if redirect_count >= self.max_redirects:
                        return URLValidationResult(
                            False,
                            status_code,
                            current_url,
                            "Maximum redirect count exceeded.",
                        )

                    current_url = urljoin(current_url, location)
                    continue

                if 200 <= status_code < 300:
                    return URLValidationResult(
                        True, status_code, current_url, "URL is reachable."
                    )

                return URLValidationResult(
                    False,
                    status_code,
                    current_url,
                    f"URL returned HTTP {status_code}.",
                )

        return URLValidationResult(False, None, current_url, "URL validation failed.")
