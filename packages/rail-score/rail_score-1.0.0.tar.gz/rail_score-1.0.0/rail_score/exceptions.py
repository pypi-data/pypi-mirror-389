"""
Custom exceptions for RAIL Score SDK
"""


class RailScoreError(Exception):
    """Base exception for all RAIL Score SDK errors"""
    pass


class AuthenticationError(RailScoreError):
    """Raised when API key is invalid or missing (401)"""
    pass


class InsufficientCreditsError(RailScoreError):
    """Raised when account has insufficient credits (402)"""

    def __init__(self, message, balance=None, required=None):
        super().__init__(message)
        self.balance = balance
        self.required = required


class ValidationError(RailScoreError):
    """Raised when request parameters are invalid (400)"""
    pass


class RateLimitError(RailScoreError):
    """Raised when rate limit is exceeded (429)"""

    def __init__(self, message, retry_after=None):
        super().__init__(message)
        self.retry_after = retry_after


class PlanUpgradeRequired(RailScoreError):
    """Raised when endpoint requires higher plan tier (403)"""
    pass


class ServiceUnavailableError(RailScoreError):
    """Raised when RAIL API service is unavailable (503)"""
    pass


class TimeoutError(RailScoreError):
    """Raised when request times out"""
    pass
