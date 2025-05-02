"""
Caching utilities for performance optimization.
"""
import logging
import functools
import time
import hashlib
import json
import pickle
from typing import Dict, Any, Callable, Optional, Union, TypeVar, Tuple, cast
import numpy as np

logger = logging.getLogger(__name__)

# Type variables for function decorators
T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])

# In-memory cache storage
_mem_cache: Dict[str, Tuple[float, Any]] = {}
_vector_cache: Dict[str, Tuple[float, Any]] = {}


def memoize(ttl: int = 3600) -> Callable[[F], F]:
    """
    Memoize decorator with time-to-live (TTL).
    
    Args:
        ttl: Time-to-live in seconds
        
    Returns:
        Decorated function
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get cache key
            cache_key = _get_cache_key(func.__name__, args, kwargs)
            
            # Check if result is in cache and not expired
            if cache_key in _mem_cache:
                timestamp, result = _mem_cache[cache_key]
                if time.time() - timestamp < ttl:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return result
            
            # Call function
            result = func(*args, **kwargs)
            
            # Cache result
            _mem_cache[cache_key] = (time.time(), result)
            
            # Prune cache if it gets too large
            if len(_mem_cache) > 1000:
                _prune_cache(_mem_cache)
            
            return result
        
        return cast(F, wrapper)
    
    return decorator


def vector_cache(ttl: int = 3600) -> Callable[[F], F]:
    """
    Cache decorator for vector search results.
    
    Args:
        ttl: Time-to-live in seconds
        
    Returns:
        Decorated function
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Only cache if use_cache is True
            use_cache = kwargs.get('use_cache', True)
            if not use_cache:
                return func(*args, **kwargs)
            
            # Get cache key
            # For vector searches, we need a specialized hash function
            # that can handle numpy arrays
            query = None
            filters = None
            k = 5  # Default
            
            # Extract arguments
            if args and len(args) > 1:
                query = args[1]  # Assuming first arg is self, second is query
            
            if 'query' in kwargs:
                query = kwargs['query']
            
            if 'filters' in kwargs:
                filters = kwargs['filters']
            
            if 'k' in kwargs:
                k = kwargs['k']
            
            # Generate cache key from query, filters, and k
            cache_key = _get_vector_cache_key(query, filters, k)
            
            # Check if result is in cache and not expired
            if cache_key in _vector_cache:
                timestamp, result = _vector_cache[cache_key]
                if time.time() - timestamp < ttl:
                    logger.debug(f"Vector cache hit for {func.__name__}")
                    return result
            
            # Call function
            result = func(*args, **kwargs)
            
            # Cache result
            _vector_cache[cache_key] = (time.time(), result)
            
            # Prune cache if it gets too large
            if len(_vector_cache) > 1000:
                _prune_cache(_vector_cache)
            
            return result
        
        return cast(F, wrapper)
    
    return decorator


def _get_cache_key(func_name: str, args: Tuple[Any, ...], kwargs: Dict[str, Any]) -> str:
    """
    Generate cache key from function name and arguments.
    
    Args:
        func_name: Function name
        args: Function positional arguments
        kwargs: Function keyword arguments
        
    Returns:
        Cache key
    """
    # Ignore first argument if it's self (instance method)
    if args and hasattr(args[0], '__dict__'):
        args = args[1:]
    
    # Convert args and kwargs to JSON
    try:
        args_str = json.dumps(args, sort_keys=True)
        kwargs_str = json.dumps(kwargs, sort_keys=True)
    except TypeError:
        # If arguments are not JSON serializable,
        # use their string representation
        args_str = str(args)
        kwargs_str = str(kwargs)
    
    # Generate key
    key = f"{func_name}:{args_str}:{kwargs_str}"
    
    # Return hash
    return hashlib.md5(key.encode('utf-8')).hexdigest()


def _get_vector_cache_key(query: Any, filters: Optional[Dict[str, Any]], k: int) -> str:
    """
    Generate cache key for vector search.
    
    Args:
        query: Search query
        filters: Search filters
        k: Number of results
        
    Returns:
        Cache key
    """
    # Handle different query types
    if isinstance(query, np.ndarray):
        # Hash numpy array
        query_hash = hashlib.md5(query.tobytes()).hexdigest()
    elif isinstance(query, str):
        # Hash string
        query_hash = hashlib.md5(query.encode('utf-8')).hexdigest()
    else:
        # Hash other types
        query_hash = hashlib.md5(str(query).encode('utf-8')).hexdigest()
    
    # Hash filters
    if filters:
        try:
            filters_hash = hashlib.md5(json.dumps(filters, sort_keys=True).encode('utf-8')).hexdigest()
        except:
            filters_hash = hashlib.md5(str(filters).encode('utf-8')).hexdigest()
    else:
        filters_hash = "no_filters"
    
    # Generate key
    key = f"vector_search:{query_hash}:{filters_hash}:{k}"
    
    return key


def _prune_cache(cache: Dict[str, Tuple[float, Any]]) -> None:
    """
    Prune cache by removing oldest entries.
    
    Args:
        cache: Cache to prune
    """
    # Keep only the newest 80% of entries
    items = sorted(cache.items(), key=lambda x: x[1][0])
    
    # Number of items to keep
    keep_count = int(len(items) * 0.8)
    
    # Remove oldest items
    for key, _ in items[:-keep_count]:
        del cache[key]
    
    logger.debug(f"Pruned cache, kept {keep_count} of {len(items)} items")


def clear_cache() -> None:
    """Clear all caches."""
    global _mem_cache, _vector_cache
    _mem_cache.clear()
    _vector_cache.clear()
    logger.info("All caches cleared")