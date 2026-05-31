from __future__ import annotations


class KlaaroError(Exception):
    """Base exception for the Klaaro SDK."""


class KlaaroAPIError(KlaaroError):
    """Raised when the Klaaro API returns a non-2xx response."""

    def __init__(
        self,
        status: int,
        code: str,
        message: str,
        param: str | None = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.param = param
        self.request_id = request_id

    def __repr__(self) -> str:
        return (
            f"KlaaroAPIError(status={self.status!r}, code={self.code!r}, "
            f"message={self.message!r}, param={self.param!r}, "
            f"request_id={self.request_id!r})"
        )
