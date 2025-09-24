"""
Query optimization utilities for improved database performance.
"""

import logging
import time
from typing import Any, Dict, List, Optional, Union
from functools import wraps
from dataclasses import dataclass
from sqlalchemy import text, Index
from sqlalchemy.orm import Query, Session
from sqlalchemy.sql import Select
import redis
import hashlib
import json

logger = logging.getLogger(__name__)

@dataclass
class QueryPerformanceMetrics:
    """Metrics for query performance analysis."""
    query_hash: str
    execution_time: float
    rows_returned: int
    cache_hit: bool
    optimization_applied: bool
    timestamp: float

class QueryCache:
    """Redis-based query result caching with intelligent invalidation."""

    def __init__(self, redis_client: redis.Redis, default_ttl: int = 300):
        self.redis = redis_client
        self.default_ttl = default_ttl
        self.cache_prefix = "query_cache:"
        self.invalidation_prefix = "query_invalidation:"

    def _generate_cache_key(self, query: str, params: Dict[str, Any] = None) -> str:
        """Generate a unique cache key for the query and parameters."""
        content = f"{query}:{json.dumps(params or {}, sort_keys=True)}"
        return f"{self.cache_prefix}{hashlib.md5(content.encode()).hexdigest()}"

    def get(self, query: str, params: Dict[str, Any] = None) -> Optional[Any]:
        """Retrieve cached query result."""
        cache_key = self._generate_cache_key(query, params)
        try:
            cached_data = self.redis.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
            return None
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {e}")
            return None

    def set(self, query: str, result: Any, params: Dict[str, Any] = None, ttl: Optional[int] = None) -> bool:
        """Cache query result with TTL."""
        cache_key = self._generate_cache_key(query, params)
        ttl = ttl or self.default_ttl
        try:
            serialized_result = json.dumps(result, default=str)
            return self.redis.setex(cache_key, ttl, serialized_result)
        except Exception as e:
            logger.warning(f"Cache storage failed: {e}")
            return False

    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate cache entries matching a pattern."""
        try:
            pattern_key = f"{self.cache_prefix}*{pattern}*"
            keys = self.redis.keys(pattern_key)
            if keys:
                return self.redis.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Cache invalidation failed: {e}")
            return 0

    def invalidate_table(self, table_name: str) -> int:
        """Invalidate all cache entries related to a table."""
        return self.invalidate_pattern(table_name)

class QueryOptimizer:
    """Advanced query optimization with performance monitoring."""

    def __init__(self, session: Session, cache: Optional[QueryCache] = None):
        self.session = session
        self.cache = cache
        self.metrics: List[QueryPerformanceMetrics] = []
        self.slow_query_threshold = 1.0  # seconds

    def optimize_query(self, query: Union[Query, Select], use_cache: bool = True) -> Any:
        """Execute query with optimizations applied."""
        start_time = time.time()
        query_str = str(query)
        query_hash = hashlib.md5(query_str.encode()).hexdigest()

        # Try cache first if enabled
        cached_result = None
        if use_cache and self.cache:
            cached_result = self.cache.get(query_str)
            if cached_result is not None:
                execution_time = time.time() - start_time
                self._record_metrics(
                    query_hash, execution_time, len(cached_result),
                    cache_hit=True, optimization_applied=False
                )
                return cached_result

        # Apply query optimizations
        optimized_query = self._apply_optimizations(query)
        optimization_applied = optimized_query != query

        # Execute query
        try:
            if hasattr(optimized_query, 'all'):
                result = optimized_query.all()
            else:
                result = self.session.execute(optimized_query).fetchall()

            execution_time = time.time() - start_time

            # Cache result if applicable
            if use_cache and self.cache and execution_time > 0.1:
                # Convert result to serializable format
                serializable_result = [dict(row._mapping) if hasattr(row, '_mapping') else row for row in result]
                self.cache.set(query_str, serializable_result)

            # Record metrics
            self._record_metrics(
                query_hash, execution_time, len(result),
                cache_hit=False, optimization_applied=optimization_applied
            )

            # Log slow queries
            if execution_time > self.slow_query_threshold:
                logger.warning(f"Slow query detected: {execution_time:.2f}s - {query_str[:200]}...")

            return result

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise

    def _apply_optimizations(self, query: Union[Query, Select]) -> Union[Query, Select]:
        """Apply various query optimizations."""
        try:
            # Add LIMIT if not present for potentially large result sets
            if hasattr(query, 'limit') and not self._has_limit(query):
                # Apply reasonable default limit for safety
                if self._is_potentially_large_query(query):
                    query = query.limit(10000)

            # Add appropriate ORDER BY for pagination queries
            if hasattr(query, 'order_by') and self._needs_ordering(query):
                # Add default ordering by primary key if no ordering exists
                query = self._add_default_ordering(query)

            return query

        except Exception as e:
            logger.warning(f"Query optimization failed: {e}")
            return query

    def _has_limit(self, query: Union[Query, Select]) -> bool:
        """Check if query already has a LIMIT clause."""
        query_str = str(query).lower()
        return 'limit' in query_str

    def _is_potentially_large_query(self, query: Union[Query, Select]) -> bool:
        """Determine if query might return large result set."""
        query_str = str(query).lower()
        # Check for absence of WHERE clauses that would limit results
        has_where = 'where' in query_str
        has_join_condition = 'on' in query_str and 'join' in query_str
        return not (has_where or has_join_condition)

    def _needs_ordering(self, query: Union[Query, Select]) -> bool:
        """Check if query would benefit from explicit ordering."""
        query_str = str(query).lower()
        return 'order by' not in query_str

    def _add_default_ordering(self, query: Union[Query, Select]) -> Union[Query, Select]:
        """Add default ordering by primary key."""
        try:
            # This is a simplified approach - in practice, you'd inspect the query
            # to determine the primary table and its primary key column
            if hasattr(query, 'order_by'):
                return query.order_by('id')
            return query
        except Exception:
            return query

    def _record_metrics(self, query_hash: str, execution_time: float,
                       rows_returned: int, cache_hit: bool, optimization_applied: bool):
        """Record query performance metrics."""
        metrics = QueryPerformanceMetrics(
            query_hash=query_hash,
            execution_time=execution_time,
            rows_returned=rows_returned,
            cache_hit=cache_hit,
            optimization_applied=optimization_applied,
            timestamp=time.time()
        )
        self.metrics.append(metrics)

        # Keep only recent metrics (last 1000)
        if len(self.metrics) > 1000:
            self.metrics = self.metrics[-1000:]

    def get_performance_report(self) -> Dict[str, Any]:
        """Generate performance report from collected metrics."""
        if not self.metrics:
            return {"message": "No metrics available"}

        total_queries = len(self.metrics)
        cache_hits = sum(1 for m in self.metrics if m.cache_hit)
        slow_queries = sum(1 for m in self.metrics if m.execution_time > self.slow_query_threshold)
        optimized_queries = sum(1 for m in self.metrics if m.optimization_applied)

        avg_execution_time = sum(m.execution_time for m in self.metrics) / total_queries
        avg_rows_returned = sum(m.rows_returned for m in self.metrics) / total_queries

        return {
            "total_queries": total_queries,
            "cache_hit_rate": cache_hits / total_queries * 100,
            "slow_query_count": slow_queries,
            "optimization_rate": optimized_queries / total_queries * 100,
            "average_execution_time": avg_execution_time,
            "average_rows_returned": avg_rows_returned,
            "performance_score": self._calculate_performance_score()
        }

    def _calculate_performance_score(self) -> float:
        """Calculate overall performance score (0-100)."""
        if not self.metrics:
            return 0.0

        cache_hit_rate = sum(1 for m in self.metrics if m.cache_hit) / len(self.metrics)
        slow_query_rate = sum(1 for m in self.metrics if m.execution_time > self.slow_query_threshold) / len(self.metrics)
        avg_execution_time = sum(m.execution_time for m in self.metrics) / len(self.metrics)

        # Score based on cache hits (40%), low slow query rate (40%), fast avg time (20%)
        cache_score = cache_hit_rate * 40
        speed_score = max(0, (1 - slow_query_rate)) * 40
        time_score = max(0, (1 - min(avg_execution_time, 1.0))) * 20

        return cache_score + speed_score + time_score

def query_performance_monitor(cache: Optional[QueryCache] = None):
    """Decorator for monitoring query performance."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time

                # Log performance metrics
                logger.info(f"Query function {func.__name__} executed in {execution_time:.3f}s")

                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"Query function {func.__name__} failed after {execution_time:.3f}s: {e}")
                raise
        return wrapper
    return decorator