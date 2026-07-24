"""Custom exceptions for the MCPGRAM SDK."""

from typing import Any, Optional


class PlatformApiError(Exception):
    """
    Raised for any non-2xx response from the MCPGRAM API, except the 502
    "tool executed but the tool itself failed" case — that comes back as a
    normal ExecuteResult with status="error" instead of raising, since
    it's an expected outcome code should branch on, not an exceptional one.
    """

    def __init__(
        self,
        message: str,
        status: int,
        body: Any = None,
        retry_after_ms: Optional[float] = None,
    ):
        super().__init__(message)
        self.status = status
        self.body = body
        self.retry_after_ms = retry_after_ms
