# DomainChecker

[![PyPI version](https://badge.fury.io/py/domainchecker.svg)](https://badge.fury.io/py/domainchecker)
[![Python Support](https://img.shields.io/pypi/pyversions/domainchecker.svg)](https://pypi.org/project/domainchecker/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/taxlien-online/domainchecker)

**Comprehensive domain checking, WHOIS lookup, and DNS resolution library for Python**

DomainChecker is a powerful Python library that provides comprehensive domain checking capabilities including WHOIS lookups, DNS resolution, expiration monitoring, and batch processing with caching support.

## ✨ Features

- 🔍 **WHOIS Lookups** - Get detailed domain registration information
- 🌐 **DNS Resolution** - Check A, AAAA, MX, NS, TXT, and CNAME records
- ⏰ **Expiration Monitoring** - Track domain expiration dates and get alerts
- 🚀 **Batch Processing** - Check hundreds of domains concurrently
- 💾 **Intelligent Caching** - SQLite-based caching to reduce API calls
- 🎯 **Rate Limiting** - Built-in rate limiting to respect WHOIS servers
- 📊 **Export Support** - Export results to CSV format
- 🖥️ **CLI Interface** - Command-line tool for domain checking
- 🛡️ **Error Handling** - Robust error handling and validation
- 📈 **Progress Tracking** - Real-time progress updates for batch operations

## 🚀 Quick Start

### Installation

```bash
pip install domainchecker
```

### Basic Usage

```python
from domainchecker import DomainChecker

# Create checker instance
checker = DomainChecker()

# Check a single domain
result = checker.check_domain("example.com")

if result.success:
    domain_info = result.domain_info
    print(f"Domain: {domain_info.domain}")
    print(f"Status: {domain_info.status}")
    print(f"Expires in: {domain_info.expires_in_days} days")
    
    if domain_info.whois_data:
        print(f"Registrar: {domain_info.whois_data.registrar}")
        print(f"Creation Date: {domain_info.whois_data.creation_date}")
```

### Batch Processing

```python
from domainchecker import BatchChecker

# Check multiple domains
domains = ["example.com", "google.com", "github.com"]
batch_checker = BatchChecker(max_workers=10)

batch_result = batch_checker.check_domains(domains)

print(f"Checked {batch_result.total_domains} domains")
print(f"Success rate: {batch_result.success_rate:.1f}%")

# Save results to CSV
batch_checker.save_results_to_csv(batch_result, "results.csv")
```

### WHOIS Lookups

```python
from domainchecker import WHOISClient

client = WHOISClient()
whois_data = client.lookup("example.com")

print(f"Registrar: {whois_data.registrar}")
print(f"Expiration: {whois_data.expiration_date}")
print(f"Days until expiration: {whois_data.days_until_expiration}")
```

### DNS Resolution

```python
from domainchecker import DNSChecker

dns_checker = DNSChecker()

# Check specific record type
a_records = dns_checker.resolve("example.com", "A")
for record in a_records:
    print(f"A Record: {record.value}")

# Check all common records
all_records = dns_checker.check_all_records("example.com")
for record in all_records:
    print(f"{record.record_type}: {record.value}")
```

### Caching

```python
from domainchecker import CacheManager

# Create cache manager
cache = CacheManager("my_cache.db", default_ttl=3600)

# Check if domain is cached
cached_info = cache.get("example.com")
if cached_info:
    print("Found in cache!")
else:
    # Perform fresh check
    result = checker.check_domain("example.com")
    if result.success:
        cache.set("example.com", result.domain_info)

# Get cache statistics
stats = cache.get_stats()
print(f"Cache entries: {stats['total_entries']}")
```

## 🖥️ Command Line Interface

DomainChecker includes a powerful CLI for domain checking:

```bash
# Check single domain
domainchecker example.com

# Check domains from file
domainchecker --file domains.txt

# Batch processing with CSV output
domainchecker --batch --file domains.txt --output results.csv

# Show only expiring domains
domainchecker --expiring-only --expiring-threshold 30 domains.txt

# Use custom number of workers
domainchecker --batch --workers 20 domains.txt

# Skip DNS checking for faster results
domainchecker --no-dns domains.txt

# Verbose output
domainchecker --verbose domains.txt
```

### CLI Examples

```bash
# Check single domain with verbose output
domainchecker -v example.com

# Batch check with custom cache file
domainchecker --batch --cache-file my_cache.db domains.txt

# Export only expiring domains to CSV
domainchecker --expiring-only --threshold 7 --output expiring.csv domains.txt

# High-performance batch check
domainchecker --batch --workers 50 --no-dns domains.txt
```

## 📊 Data Models

### DomainInfo

Complete domain information including WHOIS and DNS data:

```python
@dataclass
class DomainInfo:
    domain: str
    whois_data: Optional[WHOISData]
    dns_records: List[DNSRecord]
    status: DomainStatus
    last_checked: Optional[datetime]
    error_message: Optional[str]
```

### WHOISData

Domain registration information:

```python
@dataclass
class WHOISData:
    domain: str
    registrar: Optional[str]
    creation_date: Optional[datetime]
    expiration_date: Optional[datetime]
    updated_date: Optional[datetime]
    name_servers: List[str]
    status: List[str]
    raw_data: Optional[str]
```

### DNSRecord

DNS record information:

```python
@dataclass
class DNSRecord:
    record_type: str
    name: str
    value: str
    ttl: Optional[int]
```

## ⚙️ Configuration

### DomainChecker Options

```python
checker = DomainChecker(
    whois_timeout=30,        # WHOIS lookup timeout
    dns_timeout=10,          # DNS resolution timeout
    rate_limit_delay=1.0,    # Delay between requests
    check_dns=True          # Enable DNS checking
)
```

### BatchChecker Options

```python
batch_checker = BatchChecker(
    max_workers=10,          # Concurrent workers
    delay_between_batches=1.0,  # Delay between batches
    progress_callback=None   # Progress callback function
)
```

### CacheManager Options

```python
cache = CacheManager(
    cache_file="cache.db",   # SQLite cache file
    default_ttl=3600        # Default TTL in seconds
)
```

## 🔧 Advanced Usage

### Custom Progress Callback

```python
def progress_callback(current, total, result):
    print(f"Progress: {current}/{total} - {result.domain}")

batch_checker = BatchChecker(progress_callback=progress_callback)
```

### Error Handling

```python
from domainchecker import DomainCheckerError, WHOISError, DNSError

try:
    result = checker.check_domain("example.com")
    if not result.success:
        print(f"Error: {result.error_message}")
except DomainCheckerError as e:
    print(f"DomainChecker error: {e}")
except WHOISError as e:
    print(f"WHOIS error: {e}")
except DNSError as e:
    print(f"DNS error: {e}")
```

### Domain Validation

```python
from domainchecker.core import DomainValidator

# Validate domain
if DomainValidator.is_valid_domain("example.com"):
    print("Valid domain")

# Normalize domain
normalized = DomainValidator.normalize_domain("https://www.EXAMPLE.COM/")
print(normalized)  # "example.com"
```

## 📁 File Formats

### Input File Format

Create a text file with one domain per line:

```
example.com
google.com
github.com
stackoverflow.com
```

### CSV Output Format

The CLI exports results to CSV with the following columns:

- Domain
- Success
- Status
- Registrar
- Creation Date
- Expiration Date
- Days Until Expiration
- Name Servers
- Error Message
- Check Duration
- Cached

## 🛠️ Development

### Installation from Source

```bash
git clone https://github.com/taxlien-online/domainchecker.git
cd domainchecker
pip install -e .
```

### Running Tests

```bash
pip install -e ".[dev]"
pytest
```

### Code Quality

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/
```

## 📋 Requirements

- Python 3.8+
- requests >= 2.31.0
- python-whois >= 0.8.0
- dnspython >= 2.4.0
- python-dateutil >= 2.9.0
- colorama >= 0.4.6

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## 📞 Support

- 📧 Email: team@taxlien.online
- 🐛 Issues: [GitHub Issues](https://github.com/taxlien-online/domainchecker/issues)
- 📖 Documentation: [Read the Docs](https://domainchecker.readthedocs.io)

## 🙏 Acknowledgments

- Based on the original domain checking script by Matty and Andrey Klimov
- Uses python-whois for WHOIS lookups
- Uses dnspython for DNS resolution
- Inspired by the needs of the TaxLien.online project

---

**Made with ❤️ by the TaxLien Team**
