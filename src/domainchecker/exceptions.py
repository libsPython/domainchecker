"""
Custom exceptions for DomainChecker library.
"""


class DomainCheckerError(Exception):
    """Base exception for DomainChecker library."""
    pass


class ValidationError(DomainCheckerError):
    """Raised when domain validation fails."""
    pass


class WHOISError(DomainCheckerError):
    """Raised when WHOIS lookup fails."""
    pass


class DNSError(DomainCheckerError):
    """Raised when DNS resolution fails."""
    pass


class CacheError(DomainCheckerError):
    """Raised when cache operations fail."""
    pass


class RateLimitError(DomainCheckerError):
    """Raised when rate limit is exceeded."""
    pass


class TimeoutError(DomainCheckerError):
    """Raised when operation times out."""
    pass
