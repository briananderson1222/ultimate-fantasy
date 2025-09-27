"""
Database optimization utilities and configurations.

This module provides performance optimizations for database operations including:
- Query optimization strategies
- Index management
- Connection pooling
- Caching layers
"""

from .cache_layer import CacheStrategy, DatabaseCache
from .connection_pool import OptimizedConnectionPool
from .index_manager import IndexManager, IndexStrategy
from .query_optimizer import QueryCache, QueryOptimizer

__all__ = [
    "CacheStrategy",
    "DatabaseCache",
    "IndexManager",
    "IndexStrategy",
    "OptimizedConnectionPool",
    "QueryCache",
    "QueryOptimizer",
]
