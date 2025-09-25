"""
Caching functionality for DomainChecker library.
"""

import json
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path

from .models import DomainInfo, CheckResult
from .exceptions import CacheError


class CacheManager:
    """SQLite-based cache manager for domain check results."""
    
    def __init__(self, cache_file: str = "domainchecker_cache.db", 
                 default_ttl: int = 3600):
        self.cache_file = Path(cache_file)
        self.default_ttl = default_ttl
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for caching."""
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            
            with sqlite3.connect(str(self.cache_file)) as conn:
                cursor = conn.cursor()
                
                # Create cache table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS domain_cache (
                        domain TEXT PRIMARY KEY,
                        data TEXT NOT NULL,
                        created_at REAL NOT NULL,
                        expires_at REAL NOT NULL
                    )
                """)
                
                # Create index for expiration cleanup
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_expires_at 
                    ON domain_cache(expires_at)
                """)
                
                conn.commit()
                
        except Exception as e:
            raise CacheError(f"Failed to initialize cache database: {str(e)}")
    
    def _cleanup_expired(self):
        """Remove expired entries from cache."""
        try:
            current_time = time.time()
            
            with sqlite3.connect(str(self.cache_file)) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM domain_cache WHERE expires_at < ?",
                    (current_time,)
                )
                conn.commit()
                
        except Exception as e:
            raise CacheError(f"Failed to cleanup expired cache entries: {str(e)}")
    
    def get(self, domain: str) -> Optional[DomainInfo]:
        """
        Get cached domain information.
        
        Args:
            domain: Domain name to lookup
            
        Returns:
            Cached DomainInfo or None if not found/expired
        """
        try:
            current_time = time.time()
            
            with sqlite3.connect(str(self.cache_file)) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT data, expires_at FROM domain_cache 
                    WHERE domain = ? AND expires_at > ?
                """, (domain, current_time))
                
                row = cursor.fetchone()
                
                if row:
                    data_json, expires_at = row
                    data = json.loads(data_json)
                    
                    # Convert back to DomainInfo object
                    domain_info = self._dict_to_domain_info(data)
                    return domain_info
                
                return None
                
        except Exception as e:
            raise CacheError(f"Failed to get cached data for {domain}: {str(e)}")
    
    def set(self, domain: str, domain_info: DomainInfo, ttl: Optional[int] = None) -> None:
        """
        Cache domain information.
        
        Args:
            domain: Domain name to cache
            domain_info: DomainInfo object to cache
            ttl: Time to live in seconds (uses default if None)
        """
        try:
            if ttl is None:
                ttl = self.default_ttl
            
            current_time = time.time()
            expires_at = current_time + ttl
            
            # Convert DomainInfo to dictionary
            data_dict = self._domain_info_to_dict(domain_info)
            data_json = json.dumps(data_dict, default=self._json_serializer)
            
            with sqlite3.connect(str(self.cache_file)) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO domain_cache 
                    (domain, data, created_at, expires_at) 
                    VALUES (?, ?, ?, ?)
                """, (domain, data_json, current_time, expires_at))
                
                conn.commit()
            
            # Cleanup expired entries periodically
            if current_time % 100 == 0:  # Cleanup every ~100 operations
                self._cleanup_expired()
                
        except Exception as e:
            raise CacheError(f"Failed to cache data for {domain}: {str(e)}")
    
    def delete(self, domain: str) -> None:
        """
        Delete cached domain information.
        
        Args:
            domain: Domain name to remove from cache
        """
        try:
            with sqlite3.connect(str(self.cache_file)) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM domain_cache WHERE domain = ?", (domain,))
                conn.commit()
                
        except Exception as e:
            raise CacheError(f"Failed to delete cached data for {domain}: {str(e)}")
    
    def clear(self) -> None:
        """Clear all cached data."""
        try:
            with sqlite3.connect(str(self.cache_file)) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM domain_cache")
                conn.commit()
                
        except Exception as e:
            raise CacheError(f"Failed to clear cache: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            with sqlite3.connect(str(self.cache_file)) as conn:
                cursor = conn.cursor()
                
                # Total entries
                cursor.execute("SELECT COUNT(*) FROM domain_cache")
                total_entries = cursor.fetchone()[0]
                
                # Expired entries
                current_time = time.time()
                cursor.execute(
                    "SELECT COUNT(*) FROM domain_cache WHERE expires_at < ?",
                    (current_time,)
                )
                expired_entries = cursor.fetchone()[0]
                
                # Cache size
                cache_size = self.cache_file.stat().st_size if self.cache_file.exists() else 0
                
                return {
                    'total_entries': total_entries,
                    'active_entries': total_entries - expired_entries,
                    'expired_entries': expired_entries,
                    'cache_file_size_bytes': cache_size,
                    'cache_file': str(self.cache_file)
                }
                
        except Exception as e:
            raise CacheError(f"Failed to get cache stats: {str(e)}")
    
    def _domain_info_to_dict(self, domain_info: DomainInfo) -> Dict[str, Any]:
        """Convert DomainInfo to dictionary for JSON serialization."""
        result = {
            'domain': domain_info.domain,
            'status': domain_info.status.value,
            'last_checked': domain_info.last_checked.isoformat() if domain_info.last_checked else None,
            'error_message': domain_info.error_message,
            'dns_records': []
        }
        
        # Convert WHOIS data
        if domain_info.whois_data:
            whois_data = domain_info.whois_data
            result['whois_data'] = {
                'domain': whois_data.domain,
                'registrar': whois_data.registrar,
                'creation_date': whois_data.creation_date.isoformat() if whois_data.creation_date else None,
                'expiration_date': whois_data.expiration_date.isoformat() if whois_data.expiration_date else None,
                'updated_date': whois_data.updated_date.isoformat() if whois_data.updated_date else None,
                'name_servers': whois_data.name_servers,
                'status': whois_data.status,
                'raw_data': whois_data.raw_data
            }
        
        # Convert DNS records
        for record in domain_info.dns_records:
            result['dns_records'].append({
                'record_type': record.record_type,
                'name': record.name,
                'value': record.value,
                'ttl': record.ttl
            })
        
        return result
    
    def _dict_to_domain_info(self, data: Dict[str, Any]) -> DomainInfo:
        """Convert dictionary back to DomainInfo object."""
        from .models import DomainStatus, WHOISData, DNSRecord
        
        # Convert WHOIS data
        whois_data = None
        if 'whois_data' in data and data['whois_data']:
            whois_dict = data['whois_data']
            whois_data = WHOISData(
                domain=whois_dict['domain'],
                registrar=whois_dict.get('registrar'),
                creation_date=datetime.fromisoformat(whois_dict['creation_date']) if whois_dict.get('creation_date') else None,
                expiration_date=datetime.fromisoformat(whois_dict['expiration_date']) if whois_dict.get('expiration_date') else None,
                updated_date=datetime.fromisoformat(whois_dict['updated_date']) if whois_dict.get('updated_date') else None,
                name_servers=whois_dict.get('name_servers', []),
                status=whois_dict.get('status', []),
                raw_data=whois_dict.get('raw_data')
            )
        
        # Convert DNS records
        dns_records = []
        for record_dict in data.get('dns_records', []):
            dns_records.append(DNSRecord(
                record_type=record_dict['record_type'],
                name=record_dict['name'],
                value=record_dict['value'],
                ttl=record_dict.get('ttl')
            ))
        
        return DomainInfo(
            domain=data['domain'],
            whois_data=whois_data,
            dns_records=dns_records,
            status=DomainStatus(data['status']),
            last_checked=datetime.fromisoformat(data['last_checked']) if data.get('last_checked') else None,
            error_message=data.get('error_message')
        )
    
    def _json_serializer(self, obj):
        """Custom JSON serializer for datetime objects."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
