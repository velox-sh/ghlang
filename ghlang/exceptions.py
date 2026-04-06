from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .net import client


class GhlangError(Exception):
    """Base exception for ghlang."""


class ConfigError(GhlangError):
    """Raised when config is invalid or missing."""


class MissingTokenError(ConfigError):
    """Raised when GitHub token is not configured.

    Attributes
    ----------
    config_path : str | None
        Path to the config file, shown in the error message when available.
    """

    def __init__(self, config_path: str | None = None):
        msg = "It looks like your GitHub token isn't set up yet!\n"

        if config_path:
            msg += f"Add it to: {config_path}\n"

        msg += "Generate one at: https://github.com/settings/tokens"
        super().__init__(msg)


class TokountError(GhlangError):
    """Raised when tokount fails.

    Attributes
    ----------
    kind : str | None
        Machine-readable error category from tokount's JSON stderr.
    details : dict[str, str]
        Extra context fields from tokount's error payload.
    """

    def __init__(
        self,
        message: str,
        kind: str | None = None,
        details: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.kind = kind
        self.details = details or {}


class TokountArgumentError(TokountError):
    """Raised when tokount is called with invalid arguments."""


class TokountNotFoundError(TokountError):
    """Raised when tokount binary is not found in PATH."""

    def __init__(
        self,
        message: str | None = None,
        kind: str | None = None,
        details: dict[str, str] | None = None,
    ) -> None:
        if message is None:
            message = (
                "tokount not found in PATH!\n"
                "Install it from: https://github.com/MihaiStreames/tokount\n"
                "Or via cargo: cargo install tokount"
            )
        super().__init__(message, kind=kind, details=details)


class TokountIoError(TokountError):
    """Raised when tokount encounters an IO error."""


class HTTPError(GhlangError):
    """HTTP error with status code and response access.

    Attributes
    ----------
    response : client.Response
        The response object that triggered the error. Has ``status_code`` and ``url``.
    """

    def __init__(self, response: client.Response) -> None:
        self.response = response
        super().__init__(f"{response.status_code} {response.url}")


class RequestError(GhlangError):
    """Network-level error (DNS, connection refused, timeout, etc.)."""
