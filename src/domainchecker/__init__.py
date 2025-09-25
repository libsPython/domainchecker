"""
DomainChecker - Comprehensive domain checking, WHOIS lookup, and DNS resolution library.

A powerful Python library for checking domain expiration, performing WHOIS lookups,
DNS resolution, and batch domain processing with caching and error handling.
"""

__version__ = "1.0.0"
__author__ = "TaxLien Team"
__email__ = "team@taxlien.online"

from .core import DomainChecker, WHOISClient, DNSChecker
from .models import DomainInfo, WHOISData, DNSRecord, CheckResult
from .batch import BatchChecker
from .cache import CacheManager
from .exceptions import (
    DomainCheckerError,
    WHOISError,
    DNSError,
    CacheError,
    ValidationError,
)

__all__ = [
    # Core classes
    "DomainChecker",
    "WHOISClient", 
    "DNSChecker",
    "BatchChecker",
    "CacheManager",
    
    # Models
    "DomainInfo",
    "WHOISData",
    "DNSRecord",
    "CheckResult",
    
    # Exceptions
    "DomainCheckerError",
    "WHOISError",
    "DNSError",
    "CacheError",
    "ValidationError",
    
    # Version info
    "__version__",
    "__author__",
    "__email__",
]
