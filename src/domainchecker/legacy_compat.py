"""
Legacy compatibility module for DomainChecker.

This module provides compatibility with the original domain checking code
from the TaxLien project.
"""

import os
import sys
import time
import csv
from datetime import datetime
from typing import List, Dict, Tuple, Union, Optional, Sequence, Callable, Type, Any
from pathlib import Path

from .core import DomainChecker, WHOISClient, DNSChecker
from .batch import BatchChecker
from .cache import CacheManager
from .models import DomainInfo, CheckResult, BatchResult
from .exceptions import DomainCheckerError

# Legacy imports for compatibility
try:
    import whois
    import dateutil.parser
    from colorama import init as colorama_init
    colorama_init()
except ImportError:
    pass


class LegacyDomainChecker:
    """
    Legacy compatibility class that mimics the original domain checking functionality
    from pbn/pbn/domains/check_domains/check_domains_whois/__main__.py
    """
    
    def __init__(self, cache_dir: str = "data/cache/www"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize modern components
        self.checker = DomainChecker()
        self.batch_checker = BatchChecker()
        self.cache_manager = CacheManager(str(self.cache_dir / "domain_cache.db"))
        
        # Legacy settings
        self.delay_on_error = 120
        self.delay_on_timeout = 60
        self.get_timeout = 120
    
    def check_domain_expiration(self, domain: str) -> Dict[str, Any]:
        """
        Check domain expiration (legacy method).
        
        Args:
            domain: Domain name to check
            
        Returns:
            Dictionary with domain information
        """
        try:
            result = self.checker.check_domain(domain)
            
            if result.success and result.domain_info:
                info = result.domain_info
                whois_data = info.whois_data
                
                return {
                    'domain': domain,
                    'status': 'success',
                    'expiration_date': whois_data.expiration_date.isoformat() if whois_data and whois_data.expiration_date else None,
                    'days_until_expiration': whois_data.days_until_expiration if whois_data else None,
                    'registrar': whois_data.registrar if whois_data else None,
                    'creation_date': whois_data.creation_date.isoformat() if whois_data and whois_data.creation_date else None,
                    'name_servers': whois_data.name_servers if whois_data else [],
                    'raw_whois': whois_data.raw_data if whois_data else None,
                    'checked_at': datetime.now().isoformat(),
                }
            else:
                return {
                    'domain': domain,
                    'status': 'error',
                    'error': result.error_message,
                    'checked_at': datetime.now().isoformat(),
                }
                
        except Exception as e:
            return {
                'domain': domain,
                'status': 'error',
                'error': str(e),
                'checked_at': datetime.now().isoformat(),
            }
    
    def check_domains_batch(self, domains: List[str], 
                           show_progress: bool = True,
                           save_csv: bool = True,
                           output_file: Optional[str] = None) -> BatchResult:
        """
        Check multiple domains in batch (legacy method).
        
        Args:
            domains: List of domains to check
            show_progress: Whether to show progress
            save_csv: Whether to save results to CSV
            output_file: Output CSV file path
            
        Returns:
            BatchResult with all check results
        """
        def progress_callback(current, total, result):
            if show_progress:
                status = "✓" if result.success else "✗"
                print(f"{status} [{current}/{total}] {result.domain}")
        
        batch_checker = BatchChecker(progress_callback=progress_callback)
        batch_result = batch_checker.check_domains(domains, self.checker)
        
        # Save to CSV if requested
        if save_csv:
            if output_file is None:
                output_file = f"domain_check_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            batch_checker.save_results_to_csv(batch_result, output_file)
            print(f"Results saved to: {output_file}")
        
        return batch_result
    
    def check_domains_from_file(self, input_file: str, 
                               output_file: Optional[str] = None) -> BatchResult:
        """
        Check domains from file (legacy method).
        
        Args:
            input_file: Input file with domains (one per line)
            output_file: Output CSV file
            
        Returns:
            BatchResult with all check results
        """
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                domains = [line.strip() for line in f if line.strip()]
            
            return self.check_domains_batch(domains, output_file=output_file)
            
        except FileNotFoundError:
            raise DomainCheckerError(f"Input file not found: {input_file}")
    
    def get_cache_path(self, domain: str) -> str:
        """
        Get cache path for domain (legacy method).
        
        Args:
            domain: Domain name
            
        Returns:
            Cache file path
        """
        first_letter = domain[0].lower()
        tld = domain.split('.')[-1] if '.' in domain else 'unknown'
        return str(self.cache_dir / tld / first_letter / domain)
    
    def read_file_content(self, filename: str) -> Tuple[int, bytes]:
        """
        Read file content (legacy method).
        
        Args:
            filename: File path
            
        Returns:
            Tuple of (status_code, content)
        """
        try:
            with open(filename, 'rb') as file:
                return 200, file.read()
        except FileNotFoundError:
            return -1, b""
    
    def write_file_content(self, filename: str, content: bytes) -> None:
        """
        Write file content (legacy method).
        
        Args:
            filename: File path
            content: Content to write
        """
        directory = Path(filename).parent
        directory.mkdir(parents=True, exist_ok=True)
        with open(filename, "wb") as file:
            file.write(content)


# Legacy function compatibility
def get_domain_tld(domain: str) -> str:
    """Get TLD from domain (legacy function)."""
    return domain.split('.')[-1] if '.' in domain else 'unknown'


def read_file_content(filename: str) -> Tuple[int, bytes]:
    """Read file content (legacy function)."""
    try:
        with open(filename, 'rb') as file:
            return 200, file.read()
    except FileNotFoundError:
        return -1, b""


def write_file_content(filename: str, content: bytes) -> None:
    """Write file content (legacy function)."""
    directory = Path(filename).parent
    directory.mkdir(parents=True, exist_ok=True)
    with open(filename, "wb") as file:
        file.write(content)


def get_cache_path(domain: str) -> str:
    """Get cache path for domain (legacy function)."""
    first_letter = domain[0].lower()
    tld = get_domain_tld(domain)
    return f"{tld}/{first_letter}/{domain}"


# Main legacy compatibility function
def main_legacy():
    """
    Main function for legacy compatibility.
    Mimics the original __main__.py functionality.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Domain Expiration Checker")
    parser.add_argument('domains', nargs='*', help='Domain names to check')
    parser.add_argument('--file', '-f', help='File containing domains')
    parser.add_argument('--output', '-o', help='Output CSV file')
    parser.add_argument('--cache-dir', default='data/cache/www', help='Cache directory')
    
    args = parser.parse_args()
    
    checker = LegacyDomainChecker(args.cache_dir)
    
    if args.file:
        # Check domains from file
        try:
            batch_result = checker.check_domains_from_file(args.file, args.output)
            print(f"\nSummary:")
            print(f"Total domains: {batch_result.total_domains}")
            print(f"Successful: {batch_result.successful_checks}")
            print(f"Failed: {batch_result.failed_checks}")
            print(f"Success rate: {batch_result.success_rate:.1f}%")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    
    elif args.domains:
        # Check individual domains
        for domain in args.domains:
            result = checker.check_domain_expiration(domain)
            if result['status'] == 'success':
                print(f"✓ {domain}: {result['days_until_expiration']} days until expiration")
            else:
                print(f"✗ {domain}: {result['error']}")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main_legacy()
