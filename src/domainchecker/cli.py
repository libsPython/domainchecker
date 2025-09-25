"""
Command-line interface for DomainChecker library.
"""

import argparse
import sys
from typing import List, Optional
from pathlib import Path

from .core import DomainChecker
from .batch import BatchChecker
from .cache import CacheManager
from .exceptions import DomainCheckerError


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="DomainChecker - Comprehensive domain checking tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  domainchecker example.com                    # Check single domain
  domainchecker --file domains.txt             # Check domains from file
  domainchecker --batch domains.txt --csv output.csv  # Batch check with CSV output
  domainchecker --expiring-only domains.txt    # Show only expiring domains
        """
    )
    
    parser.add_argument(
        'domains',
        nargs='*',
        help='Domain names to check'
    )
    
    parser.add_argument(
        '--file', '-f',
        type=str,
        help='File containing domains (one per line)'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Output file for results (CSV format)'
    )
    
    parser.add_argument(
        '--batch',
        action='store_true',
        help='Enable batch processing mode'
    )
    
    parser.add_argument(
        '--workers', '-w',
        type=int,
        default=10,
        help='Number of worker threads for batch processing (default: 10)'
    )
    
    parser.add_argument(
        '--expiring-threshold', '-t',
        type=int,
        default=30,
        help='Days threshold for expiring domains (default: 30)'
    )
    
    parser.add_argument(
        '--expiring-only',
        action='store_true',
        help='Show only domains expiring within threshold'
    )
    
    parser.add_argument(
        '--no-dns',
        action='store_true',
        help='Skip DNS record checking'
    )
    
    parser.add_argument(
        '--cache-file',
        type=str,
        help='SQLite cache file path'
    )
    
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Disable caching'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    try:
        # Determine domains to check
        domains = []
        if args.domains:
            domains.extend(args.domains)
        if args.file:
            file_path = Path(args.file)
            if not file_path.exists():
                print(f"Error: File not found: {args.file}", file=sys.stderr)
                sys.exit(1)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                file_domains = [line.strip() for line in f if line.strip()]
                domains.extend(file_domains)
        
        if not domains:
            print("Error: No domains specified. Use --file or provide domain names.", file=sys.stderr)
            parser.print_help()
            sys.exit(1)
        
        # Create checker
        checker = DomainChecker(check_dns=not args.no_dns)
        
        if args.batch or len(domains) > 1:
            # Batch processing
            batch_checker = BatchChecker(max_workers=args.workers)
            
            def progress_callback(current, total, result):
                if args.verbose:
                    status = "✓" if result.success else "✗"
                    print(f"{status} [{current}/{total}] {result.domain}")
            
            print(f"Checking {len(domains)} domains...")
            batch_result = batch_checker.check_domains(
                domains, 
                checker, 
                show_progress=args.verbose
            )
            
            # Filter expiring domains if requested
            if args.expiring_only:
                expiring_domains = batch_checker.filter_expiring_domains(
                    batch_result, 
                    args.expiring_threshold
                )
                batch_result.results = expiring_domains
                batch_result.successful_checks = len(expiring_domains)
            
            # Save to CSV if requested
            if args.output:
                batch_checker.save_results_to_csv(batch_result, args.output)
                print(f"Results saved to: {args.output}")
            
            # Print summary
            print(f"\nSummary:")
            print(f"  Total domains: {batch_result.total_domains}")
            print(f"  Successful checks: {batch_result.successful_checks}")
            print(f"  Failed checks: {batch_result.failed_checks}")
            print(f"  Success rate: {batch_result.success_rate:.1f}%")
            print(f"  Total time: {batch_result.total_duration:.2f}s")
            
            # Print expiring domains
            if args.expiring_only or args.verbose:
                expiring = batch_checker.filter_expiring_domains(batch_result, args.expiring_threshold)
                if expiring:
                    print(f"\nDomains expiring within {args.expiring_threshold} days:")
                    for result in expiring:
                        if result.success and result.domain_info:
                            days = result.domain_info.expires_in_days
                            print(f"  {result.domain}: {days} days")
        
        else:
            # Single domain check
            domain = domains[0]
            print(f"Checking domain: {domain}")
            
            result = checker.check_domain(domain)
            
            if result.success and result.domain_info:
                info = result.domain_info
                print(f"\nDomain: {info.domain}")
                print(f"Status: {info.status.value}")
                
                if info.whois_data:
                    whois_data = info.whois_data
                    print(f"Registrar: {whois_data.registrar or 'N/A'}")
                    print(f"Creation Date: {whois_data.creation_date or 'N/A'}")
                    print(f"Expiration Date: {whois_data.expiration_date or 'N/A'}")
                    print(f"Days Until Expiration: {whois_data.days_until_expiration or 'N/A'}")
                    
                    if whois_data.name_servers:
                        print(f"Name Servers: {', '.join(whois_data.name_servers)}")
                
                if info.dns_records and args.verbose:
                    print(f"\nDNS Records:")
                    for record in info.dns_records:
                        print(f"  {record.record_type}: {record.value}")
                
                print(f"Check Duration: {result.check_duration:.2f}s")
                
            else:
                print(f"Error: {result.error_message}")
                sys.exit(1)
    
    except DomainCheckerError as e:
        print(f"DomainChecker Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
