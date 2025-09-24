"""
Database optimization utilities and configurations.

This module provides performance optimizations for database operations including:
- Query optimization strategies
- Index management
- Connection pooling
- Caching layers
"""

from .query_optimizer import QueryOptimizer, QueryCache
from .index_manager import IndexManager, IndexStrategy
from .connection_pool import OptimizedConnectionPool
from .cache_layer import DatabaseCache, CacheStrategy

__all__ = [
    'QueryOptimizer',
    'QueryCache',
    'IndexManager',
    'IndexStrategy',
    'OptimizedConnectionPool',
    'DatabaseCache',
    'CacheStrategy'
]