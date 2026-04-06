from __future__ import annotations

from http.client import HTTPMessage
from http.client import HTTPResponse
from http.client import HTTPSConnection
import json
from typing import Any
from urllib.error import HTTPError as _UrllibHTTPError
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.parse import urlparse
from urllib.request import Request
from urllib.request import urlopen

from ghlang import exceptions
from ghlang import log


class Response:
    """Thin wrapper over an HTTP response.

    Attributes
    ----------
    status_code : int
        HTTP status code.
    url : str
        The request URL.
    """

    def __init__(self, status_code: int, headers: HTTPMessage, body: str, url: str) -> None:
        self.status_code = status_code
        self.url = url
        self._headers = headers
        self._body = body

    @classmethod
    def from_urllib(cls, raw: HTTPResponse | _UrllibHTTPError, url: str) -> Response:
        """Build from a urllib HTTPResponse or HTTPError."""
        status = raw.code if isinstance(raw, _UrllibHTTPError) else raw.status
        return cls(status, raw.headers, raw.read().decode("utf-8"), url)  # type: ignore[arg-type]

    @property
    def headers(self) -> HTTPMessage:
        return self._headers

    @property
    def text(self) -> str:
        return self._body

    def json(self) -> Any:
        """Parse response body as JSON."""
        return json.loads(self._body)

    def raise_for_status(self) -> None:
        """Raise HTTPError for 4xx/5xx responses."""
        if self.status_code >= 400:
            raise exceptions.HTTPError(self)


def get(url: str, *, timeout: int = 10, headers: dict[str, str] | None = None) -> Response:
    """Send a simple GET request with no connection reuse.

    Parameters
    ----------
    url : str
        Request URL.
    timeout : int
        Timeout in seconds.
    headers : dict[str, str] | None
        Optional request headers.

    Returns
    -------
    Response
        The HTTP response.
    """
    req = Request(url, headers=headers or {})

    try:
        raw = urlopen(req, timeout=timeout)  # noqa: S310
    except _UrllibHTTPError as e:
        return Response.from_urllib(e, url)
    except URLError as e:
        raise exceptions.RequestError(str(e.reason)) from e

    return Response.from_urllib(raw, url)


class Session:
    """HTTP session with persistent headers and connection reuse.

    Attributes
    ----------
    headers : dict[str, str]
        Default headers sent with every request.
    """

    def __init__(self) -> None:
        self.headers: dict[str, str] = {}
        self._conns: dict[str, HTTPSConnection] = {}

    def update_headers(self, headers: dict[str, str]) -> None:
        """Merge headers into the session defaults."""
        self.headers.update(headers)

    def _get_conn(self, host: str) -> HTTPSConnection:
        """Get or create a persistent connection for a host"""
        if host not in self._conns:
            self._conns[host] = HTTPSConnection(host, timeout=30)
        return self._conns[host]

    def _do_get(self, conn: HTTPSConnection, path: str, url: str) -> Response:
        """Execute a GET on an existing connection"""
        conn.request("GET", path, headers=self.headers)
        raw = conn.getresponse()
        body = raw.read().decode("utf-8")
        return Response(raw.status, raw.headers, body, url)

    def _log_rate_limit(self, response: Response) -> None:
        """Log remaining API rate limit from response headers"""
        remaining = response.headers.get("X-RateLimit-Remaining")
        limit = response.headers.get("X-RateLimit-Limit")

        if remaining and limit:
            log.logger.debug(f"Rate limit: {remaining}/{limit} remaining")

    def get(self, url: str, params: dict[str, Any] | None = None) -> Response:
        """Send a GET request with connection reuse and rate-limit logging.

        Parameters
        ----------
        url : str
            Request URL.
        params : dict[str, Any] | None
            Query parameters appended to the URL.

        Returns
        -------
        Response
            The HTTP response.
        """
        if params:
            url = f"{url}?{urlencode(params)}"

        parsed = urlparse(url)
        host = parsed.hostname or ""
        conn = self._get_conn(host)
        path = parsed.path

        if parsed.query:
            path = f"{path}?{parsed.query}"

        try:
            r = self._do_get(conn, path, url)
        except (OSError, ConnectionError):
            # stale connection, reconnect once
            self._conns.pop(host, None)
            conn = self._get_conn(host)
            try:
                r = self._do_get(conn, path, url)
            except (OSError, ConnectionError) as e:
                raise exceptions.RequestError(str(e)) from e

        self._log_rate_limit(r)
        r.raise_for_status()
        return r
