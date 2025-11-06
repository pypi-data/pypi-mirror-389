"""Custom exceptions for x402tools SDK."""


class X402Error(Exception):
    """Base exception for all x402tools errors."""
    pass


class AuthenticationError(X402Error):
    """Raised when authentication fails."""
    pass


class APIError(X402Error):
    """Raised when the API returns an error."""
    
    def __init__(self, message: str, status_code: int = None, response: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class RateLimitError(X402Error):
    """Raised when rate limit is exceeded."""
    pass


class ValidationError(X402Error):
    """Raised when request validation fails."""
    pass


class EnvelopeNotFoundError(X402Error):
    """Raised when an envelope is not found."""
    pass


class UsageLimitExceededError(X402Error):
    """Raised when usage limit is exceeded."""
    pass
