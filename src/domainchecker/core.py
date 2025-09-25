"""
Core functionality for DomainChecker library.
"""

import re
import time
import socket
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import dns.resolver
import dns.exception
import whois
import requests
from urllib.parse import urlparse

from .models import DomainInfo, WHOISData, DNSRecord, DomainStatus, CheckResult
from .exceptions import (
    ValidationError,
    WHOISError,
    DNSError,
    RateLimitError,
    TimeoutError,
)


class DomainValidator:
    """Domain validation utilities."""
    
    DOMAIN_REGEX = re.compile(
        r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$'
    )
    
    @classmethod
    def is_valid_domain(cls, domain: str) -> bool:
        """Check if domain is valid."""
        if not domain or len(domain) > 253:
            return False
        
        # Remove protocol if present
        domain = domain.lower().strip()
        if domain.startswith(('http://', 'https://')):
            parsed = urlparse(domain)
            domain = parsed.netloc
        
        # Remove www prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        
        return bool(cls.DOMAIN_REGEX.match(domain))
    
    @classmethod
    def normalize_domain(cls, domain: str) -> str:
        """Normalize domain name."""
        domain = domain.lower().strip()
        
        # Remove protocol
        if domain.startswith(('http://', 'https://')):
            parsed = urlparse(domain)
            domain = parsed.netloc
        
        # Remove www prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        
        # Remove trailing slash
        domain = domain.rstrip('/')
        
        return domain


class WHOISClient:
    """WHOIS client for domain information lookup."""
    
    def __init__(self, timeout: int = 30, rate_limit_delay: float = 1.0):
        self.timeout = timeout
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0
    
    def _rate_limit(self):
        """Implement rate limiting."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        self.last_request_time = time.time()
    
    def lookup(self, domain: str) -> WHOISData:
        """
        Perform WHOIS lookup for domain.
        
        Args:
            domain: Domain name to lookup
            
        Returns:
            WHOISData object with domain information
            
        Raises:
            ValidationError: If domain is invalid
            WHOISError: If WHOIS lookup fails
        """
        if not DomainValidator.is_valid_domain(domain):
            raise ValidationError(f"Invalid domain: {domain}")
        
        domain = DomainValidator.normalize_domain(domain)
        
        try:
            self._rate_limit()
            
            # Perform WHOIS lookup
            w = whois.whois(domain)
            
            # Parse WHOIS data
            whois_data = WHOISData(
                domain=domain,
                registrar=w.registrar,
                creation_date=w.creation_date,
                expiration_date=w.expiration_date,
                updated_date=w.updated_date,
                name_servers=w.name_servers if w.name_servers else [],
                status=w.status if w.status else [],
                raw_data=str(w) if hasattr(w, '__str__') else None
            )
            
            return whois_data
            
        except Exception as e:
            raise WHOISError(f"WHOIS lookup failed for {domain}: {str(e)}")


class DNSChecker:
    """DNS resolution and record checking."""
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
    
    def resolve(self, domain: str, record_type: str = 'A') -> List[DNSRecord]:
        """
        Resolve DNS records for domain.
        
        Args:
            domain: Domain name to resolve
            record_type: DNS record type (A, AAAA, MX, etc.)
            
        Returns:
            List of DNSRecord objects
            
        Raises:
            ValidationError: If domain is invalid
            DNSError: If DNS resolution fails
        """
        if not DomainValidator.is_valid_domain(domain):
            raise ValidationError(f"Invalid domain: {domain}")
        
        domain = DomainValidator.normalize_domain(domain)
        
        try:
            records = []
            resolver = dns.resolver.Resolver()
            resolver.timeout = self.timeout
            
            answers = resolver.resolve(domain, record_type)
            
            for rdata in answers:
                record = DNSRecord(
                    record_type=record_type,
                    name=domain,
                    value=str(rdata),
                    ttl=getattr(rdata, 'ttl', None)
                )
                records.append(record)
            
            return records
            
        except dns.exception.DNSException as e:
            raise DNSError(f"DNS resolution failed for {domain}: {str(e)}")
    
    def check_all_records(self, domain: str) -> List[DNSRecord]:
        """
        Check all common DNS records for domain.
        
        Args:
            domain: Domain name to check
            
        Returns:
            List of all DNS records found
        """
        all_records = []
        record_types = ['A', 'AAAA', 'MX', 'NS', 'TXT', 'CNAME']
        
        for record_type in record_types:
            try:
                records = self.resolve(domain, record_type)
                all_records.extend(records)
            except DNSError:
                # Continue with other record types if one fails
                continue
        
        return all_records


class DomainChecker:
    """Main domain checking class."""
    
    def __init__(self, 
                 whois_timeout: int = 30,
                 dns_timeout: int = 10,
                 rate_limit_delay: float = 1.0,
                 check_dns: bool = True):
        self.whois_client = WHOISClient(whois_timeout, rate_limit_delay)
        self.dns_checker = DNSChecker(dns_timeout)
        self.check_dns = check_dns
    
    def check_domain(self, domain: str) -> CheckResult:
        """
        Perform comprehensive domain check.
        
        Args:
            domain: Domain name to check
            
        Returns:
            CheckResult object with all domain information
        """
        start_time = time.time()
        
        try:
            # Validate domain
            if not DomainValidator.is_valid_domain(domain):
                return CheckResult(
                    domain=domain,
                    success=False,
                    error_message=f"Invalid domain: {domain}"
                )
            
            domain = DomainValidator.normalize_domain(domain)
            
            # Get WHOIS data
            whois_data = self.whois_client.lookup(domain)
            
            # Get DNS records if enabled
            dns_records = []
            if self.check_dns:
                try:
                    dns_records = self.dns_checker.check_all_records(domain)
                except DNSError as e:
                    # Continue even if DNS fails
                    pass
            
            # Determine domain status
            status = DomainStatus.ACTIVE
            if whois_data.expiration_date:
                if whois_data.expiration_date < datetime.now():
                    status = DomainStatus.EXPIRED
                elif whois_data.is_expiring_soon():
                    status = DomainStatus.EXPIRING_SOON
            
            # Create domain info
            domain_info = DomainInfo(
                domain=domain,
                whois_data=whois_data,
                dns_records=dns_records,
                status=status,
                last_checked=datetime.now()
            )
            
            duration = time.time() - start_time
            
            return CheckResult(
                domain=domain,
                success=True,
                domain_info=domain_info,
                check_duration=duration
            )
            
        except Exception as e:
            duration = time.time() - start_time
            return CheckResult(
                domain=domain,
                success=False,
                error_message=str(e),
                check_duration=duration
            )
    
    def is_domain_expiring_soon(self, domain: str, days_threshold: int = 30) -> bool:
        """
        Check if domain is expiring soon.
        
        Args:
            domain: Domain name to check
            days_threshold: Days threshold for "soon" expiration
            
        Returns:
            True if domain is expiring within threshold
        """
        result = self.check_domain(domain)
        if result.success and result.domain_info:
            return result.domain_info.is_expiring_soon(days_threshold)
        return False
    
    def get_expiration_date(self, domain: str) -> Optional[datetime]:
        """
        Get domain expiration date.
        
        Args:
            domain: Domain name to check
            
        Returns:
            Expiration date or None if not available
        """
        result = self.check_domain(domain)
        if result.success and result.domain_info and result.domain_info.whois_data:
            return result.domain_info.whois_data.expiration_date
        return None
