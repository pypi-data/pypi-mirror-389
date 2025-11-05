"""
Key caching for CSF-Crypto.

Caches Kyber key pairs to avoid regeneration overhead,
significantly improving performance for repeated operations.
"""

from typing import Dict, Tuple, Optional
from threading import Lock
from csf.core.fractal_hash import fractal_hash


class KeyCache:
    """
    Thread-safe cache for Kyber key pairs.
    
    Caches keys based on semantic key hash to avoid regeneration
    overhead. This can save 0.1-0.5s per encryption operation.
    """
    
    def __init__(self, max_size: int = 100):
        """
        Initialize key cache.
        
        Args:
            max_size: Maximum number of cached key pairs
        """
        self._cache: Dict[str, Tuple[bytes, bytes]] = {}
        self._max_size = max_size
        self._lock = Lock()
        self._hits = 0
        self._misses = 0
    
    def _get_cache_key(self, semantic_key: str, pqc_scheme: str) -> str:
        """
        Generate cache key from semantic key and PQC scheme.
        
        Uses fractal hash to maintain protocol alignment (100% fractal-based).
        
        Args:
            semantic_key: Semantic key text
            pqc_scheme: PQC scheme name
            
        Returns:
            Cache key (fractal hash hex)
        """
        key_data = f"{semantic_key}:{pqc_scheme}".encode('utf-8')
        # Use fractal hash instead of SHA-256 for protocol alignment
        return fractal_hash(key_data, output_length=32).hex()
    
    def get_or_generate(
        self, 
        semantic_key: str, 
        pqc_scheme: str,
        generate_func
    ) -> Tuple[bytes, bytes]:
        """
        Get cached keys or generate new ones.
        
        Args:
            semantic_key: Semantic key text
            pqc_scheme: PQC scheme name
            generate_func: Function to generate keys if not cached
                          Should return (public_key, private_key)
        
        Returns:
            Tuple of (public_key, private_key)
        """
        cache_key = self._get_cache_key(semantic_key, pqc_scheme)
        
        with self._lock:
            # Check cache
            if cache_key in self._cache:
                self._hits += 1
                return self._cache[cache_key]
            
            # Generate new keys
            self._misses += 1
            public_key, private_key = generate_func()
            
            # Cache if not full
            if len(self._cache) < self._max_size:
                self._cache[cache_key] = (public_key, private_key)
            else:
                # Evict oldest (FIFO) - simple eviction
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                self._cache[cache_key] = (public_key, private_key)
            
            return public_key, private_key
    
    def clear(self):
        """Clear the cache."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total > 0 else 0
            return {
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': hit_rate,
                'size': len(self._cache),
                'max_size': self._max_size
            }


# Global cache instance
_global_key_cache = KeyCache(max_size=100)


def get_global_cache() -> KeyCache:
    """Get the global key cache instance."""
    return _global_key_cache

