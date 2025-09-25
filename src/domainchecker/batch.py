"""
Batch processing functionality for DomainChecker library.
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional, Callable, Dict, Any
import threading

from .models import CheckResult, BatchResult
from .core import DomainChecker
from .exceptions import DomainCheckerError


class BatchChecker:
    """Batch domain checking with concurrent processing."""
    
    def __init__(self,
                 max_workers: int = 10,
                 delay_between_batches: float = 1.0,
                 progress_callback: Optional[Callable] = None):
        self.max_workers = max_workers
        self.delay_between_batches = delay_between_batches
        self.progress_callback = progress_callback
        self._lock = threading.Lock()
    
    def check_domains(self, 
                     domains: List[str],
                     checker: Optional[DomainChecker] = None,
                     show_progress: bool = True) -> BatchResult:
        """
        Check multiple domains concurrently.
        
        Args:
            domains: List of domain names to check
            checker: DomainChecker instance (creates new if None)
            show_progress: Whether to show progress updates
            
        Returns:
            BatchResult with all check results
        """
        if checker is None:
            checker = DomainChecker()
        
        start_time = time.time()
        results = []
        successful_checks = 0
        failed_checks = 0
        cached_results = 0
        
        total_domains = len(domains)
        
        # Process domains in batches
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_domain = {
                executor.submit(checker.check_domain, domain): domain 
                for domain in domains
            }
            
            # Process completed tasks
            for i, future in enumerate(as_completed(future_to_domain), 1):
                try:
                    result = future.result()
                    results.append(result)
                    
                    if result.success:
                        successful_checks += 1
                    else:
                        failed_checks += 1
                    
                    if result.cached:
                        cached_results += 1
                    
                    # Progress callback
                    if show_progress and self.progress_callback:
                        self.progress_callback(i, total_domains, result)
                    
                    # Rate limiting between batches
                    if i % self.max_workers == 0:
                        time.sleep(self.delay_between_batches)
                        
                except Exception as e:
                    domain = future_to_domain[future]
                    error_result = CheckResult(
                        domain=domain,
                        success=False,
                        error_message=f"Batch processing error: {str(e)}"
                    )
                    results.append(error_result)
                    failed_checks += 1
        
        total_duration = time.time() - start_time
        
        return BatchResult(
            total_domains=total_domains,
            successful_checks=successful_checks,
            failed_checks=failed_checks,
            cached_results=cached_results,
            results=results,
            total_duration=total_duration
        )
    
    def check_domains_from_file(self, 
                               file_path: str,
                               checker: Optional[DomainChecker] = None) -> BatchResult:
        """
        Check domains from a text file (one domain per line).
        
        Args:
            file_path: Path to file containing domains
            checker: DomainChecker instance (creates new if None)
            
        Returns:
            BatchResult with all check results
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                domains = [line.strip() for line in f if line.strip()]
            
            return self.check_domains(domains, checker)
            
        except FileNotFoundError:
            raise DomainCheckerError(f"File not found: {file_path}")
        except Exception as e:
            raise DomainCheckerError(f"Error reading file {file_path}: {str(e)}")
    
    def save_results_to_csv(self, 
                           batch_result: BatchResult, 
                           output_file: str) -> None:
        """
        Save batch results to CSV file.
        
        Args:
            batch_result: BatchResult to save
            output_file: Output CSV file path
        """
        import csv
        
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow([
                    'Domain',
                    'Success',
                    'Status',
                    'Registrar',
                    'Creation Date',
                    'Expiration Date',
                    'Days Until Expiration',
                    'Name Servers',
                    'Error Message',
                    'Check Duration',
                    'Cached'
                ])
                
                # Write results
                for result in batch_result.results:
                    domain_info = result.domain_info
                    whois_data = domain_info.whois_data if domain_info else None
                    
                    writer.writerow([
                        result.domain,
                        result.success,
                        domain_info.status.value if domain_info else 'ERROR',
                        whois_data.registrar if whois_data else '',
                        whois_data.creation_date.isoformat() if whois_data and whois_data.creation_date else '',
                        whois_data.expiration_date.isoformat() if whois_data and whois_data.expiration_date else '',
                        whois_data.days_until_expiration if whois_data else '',
                        '; '.join(whois_data.name_servers) if whois_data and whois_data.name_servers else '',
                        result.error_message or '',
                        f"{result.check_duration:.2f}s" if result.check_duration else '',
                        result.cached
                    ])
                    
        except Exception as e:
            raise DomainCheckerError(f"Error saving results to CSV: {str(e)}")
    
    def filter_expiring_domains(self, 
                               batch_result: BatchResult, 
                               days_threshold: int = 30) -> List[CheckResult]:
        """
        Filter domains that are expiring soon from batch results.
        
        Args:
            batch_result: BatchResult to filter
            days_threshold: Days threshold for "soon" expiration
            
        Returns:
            List of CheckResult objects for expiring domains
        """
        expiring_domains = []
        
        for result in batch_result.results:
            if (result.success and 
                result.domain_info and 
                result.domain_info.is_expiring_soon(days_threshold)):
                expiring_domains.append(result)
        
        return expiring_domains
