from http.client import HTTPSConnection
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from ghlang import exceptions
from ghlang.net.client import Response
from ghlang.net.client import Session
from ghlang.net.client import get


class TestResponse:
    """Tests for the Response wrapper"""

    def test_raise_for_status_ok(self) -> None:
        """Should not raise for 2xx status codes."""
        r = Response(200, MagicMock(), "", "https://example.com")
        r.raise_for_status()

    def test_raise_for_status_4xx(self) -> None:
        """Should raise HTTPError for 4xx status codes."""
        r = Response(404, MagicMock(), "", "https://example.com")
        with pytest.raises(exceptions.HTTPError) as exc_info:
            r.raise_for_status()
        assert exc_info.value.response.status_code == 404

    def test_raise_for_status_5xx(self) -> None:
        """Should raise HTTPError for 5xx status codes."""
        r = Response(500, MagicMock(), "", "https://example.com")
        with pytest.raises(exceptions.HTTPError):
            r.raise_for_status()


class TestGet:
    """Tests for the standalone get function"""

    def test_dns_failure_raises_request_error(self) -> None:
        """Should raise RequestError on DNS failure."""
        with pytest.raises(exceptions.RequestError):
            get("https://this-domain-does-not-exist.invalid", timeout=1)


class TestSession:
    """Tests for Session with connection reuse"""

    def test_headers_persist(self) -> None:
        """Should send persistent headers with every request."""
        session = Session()
        session.update_headers({"X-Custom": "test"})
        assert session.headers["X-Custom"] == "test"

    def test_stale_connection_reconnects(self) -> None:
        """Should reconnect on stale connection error."""
        session = Session()
        session.update_headers({"User-Agent": "ghlang-test"})

        call_count = 0
        original_do_get = session._do_get

        def flaky_get(conn: HTTPSConnection, path: str, url: str) -> Response:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise OSError("connection reset")
            return original_do_get(conn, path, url)

        with patch.object(session, "_do_get", side_effect=flaky_get):
            r = session.get("https://api.github.com")

        assert r.status_code == 200
        assert call_count == 2

    def test_connection_failure_raises_request_error(self) -> None:
        """Should raise RequestError when connection cannot be established."""
        session = Session()

        with (
            patch.object(session, "_do_get", side_effect=OSError("refused")),
            pytest.raises(exceptions.RequestError),
        ):
            session.get("https://api.github.com")
