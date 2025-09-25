"""
Data models for DomainChecker library.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class DomainStatus(Enum):
    """Domain status enumeration."""
    ACTIVE = "active"
    EXPIRED = "expired"
    EXPIRING_SOON = "expiring_soon"
    UNKNOWN = "unknown"
    ERROR = "error"


@dataclass
class WHOISData:
    """WHOIS data model."""
    domain: str
    registrar: Optional[str] = None
    creation_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    updated_date: Optional[datetime] = None
    name_servers: List[str] = None
    status: List[str] = None
    raw_data: Optional[str] = None
    
    def __post_init__(self):
        if self.name_servers is None:
            self.name_servers = []
        if self.status is None:
            self.status = []

    @property
    def days_until_expiration(self) -> Optional[int]:
        """Calculate days until domain expiration."""
        if not self.expiration_date:
            return None
        
        delta = self.expiration_date - datetime.now()
        return delta.days

    @property
    def is_expiring_soon(self, days_threshold: int = 30) -> bool:
        """Check if domain is expiring soon."""
        days = self.days_until_expiration
        return days is not None and days <= days_threshold


@dataclass
class DNSRecord:
    """DNS record model."""
    record_type: str
    name: str
    value: str
    ttl: Optional[int] = None


@dataclass
class DomainInfo:
    """Complete domain information."""
    domain: str
    whois_data: Optional[WHOISData] = None
    dns_records: List[DNSRecord] = None
    status: DomainStatus = DomainStatus.UNKNOWN
    last_checked: Optional[datetime] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.dns_records is None:
            self.dns_records = []
        if self.last_checked is None:
            self.last_checked = datetime.now()

    @property
    def expires_in_days(self) -> Optional[int]:
        """Get days until expiration from WHOIS data."""
        if self.whois_data:
            return self.whois_data.days_until_expiration
        return None

    @property
    def is_expiring_soon(self, days_threshold: int = 30) -> bool:
        """Check if domain is expiring soon."""
        if self.whois_data:
            return self.whois_data.is_expiring_soon(days_threshold)
        return False


@dataclass
class CheckResult:
    """Result of domain check operation."""
    domain: str
    success: bool
    domain_info: Optional[DomainInfo] = None
    error_message: Optional[str] = None
    check_duration: Optional[float] = None
    cached: bool = False


@dataclass
class BatchResult:
    """Result of batch domain check operation."""
    total_domains: int
    successful_checks: int
    failed_checks: int
    cached_results: int
    results: List[CheckResult]
    total_duration: float
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_domains == 0:
            return 0.0
        return (self.successful_checks / self.total_domains) * 100
