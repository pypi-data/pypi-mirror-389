"""Custom exceptions for the Lumen SDK."""


class LumenError(Exception):
    """Base exception for all Lumen SDK errors."""

    pass


class LumenAPIError(LumenError):
    """Exception raised when API requests fail."""

    def __init__(self, message: str, status_code: int = 0) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class LumenConfigurationError(LumenError):
    """Exception raised when SDK is misconfigured."""

    pass


class LumenValidationError(LumenError):
    """Exception raised when input validation fails."""

    pass

