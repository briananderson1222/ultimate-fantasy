"""
Database query performance validation and optimization tests.

Tests cover:
- Query execution time benchmarks
- Index effectiveness validation
- Connection pool performance
- Complex query optimization
- Concurrent database load testing
- Memory usage during heavy operations
"""

import pytest
import asyncio
import time
import statistics
import psutil
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager
from sqlalchemy import create_engine, text, MetaData, Table, select, func
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
import asyncpg
from concurrent.futures import ThreadPoolExecutor
import json

# Database performance test configuration
DB_PERFORMANCE_CONFIG = {
    "query_timeout_ms": 300,  # 300ms for most queries
    "complex_query_timeout_ms": 600,  # 600ms for analytics
    "batch_size": 1000,
    "concurrent_connections": 50,
    "test_duration": 30,  # seconds
    "max_memory_increase_mb": 100,
    "connection_pool_size": 20,
    "max_overflow": 30,
}

class DatabasePerformanceMetrics:
    """Container for database performance metrics."""

    def __init__(self):
        self.query_times: List[float] = []
        self.connection_times: List[float] = []
        self.error_count = 0
        self.success_count = 0
        self.memory_samples: List[float] = []
        self.pool_stats: List[Dict[str, Any]] = []

    def add_query_result(self, execution_time: float, success: bool):
        """Add query execution result."""
        self.query_times.append(execution_time)
        if success:
            self.success_count += 1
        else:
            self.error_count += 1

    def add_connection_time(self, connection_time: float):
        """Add connection establishment time."""
        self.connection_times.append(connection_time)

    def add_memory_sample(self, memory_mb: float):
        """Add memory usage sample."""
        self.memory_samples.append(memory_mb)

    def add_pool_stats(self, stats: Dict[str, Any]):
        """Add connection pool statistics."""
        self.pool_stats.append(stats)

    @property
    def average_query_time(self) -> float:
        """Calculate average query execution time."""
        return statistics.mean(self.query_times) if self.query_times else 0

    @property
    def p95_query_time(self) -> float:
        """Calculate 95th percentile query time."""
        if not self.query_times:
            return 0
        sorted_times = sorted(self.query_times)
        index = int(0.95 * len(sorted_times))
        return sorted_times[index]

    @property
    def p99_query_time(self) -> float:
        """Calculate 99th percentile query time."""
        if not self.query_times:
            return 0
        sorted_times = sorted(self.query_times)
        index = int(0.99 * len(sorted_times))
        return sorted_times[index]

    @property
    def success_rate(self) -> float:
        """Calculate query success rate."""
        total = self.success_count + self.error_count
        return (self.success_count / total * 100) if total > 0 else 0

    @property
    def queries_per_second(self) -> float:
        """Calculate queries per second."""
        if not self.query_times:
            return 0
        total_time = sum(self.query_times)
        return len(self.query_times) / total_time if total_time > 0 else 0


class DatabasePerformanceTester:
    """Database performance testing framework."""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = None
        self.session_factory = None
        self.metrics = DatabasePerformanceMetrics()

    def setup_engine(self, pool_size: int = DB_PERFORMANCE_CONFIG["connection_pool_size"]):
        """Set up database engine with connection pooling."""
        self.engine = create_engine(
            self.database_url,
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=DB_PERFORMANCE_CONFIG["max_overflow"],
            pool_timeout=30,
            pool_recycle=3600,
            pool_pre_ping=True,
            echo=False  # Disable SQL logging for performance tests
        )

        self.session_factory = sessionmaker(bind=self.engine)

    def cleanup(self):
        """Clean up database connections."""
        if self.engine:
            self.engine.dispose()

    @asynccontextmanager
    async def get_async_connection(self):
        """Get async database connection for asyncpg tests."""
        conn = await asyncpg.connect(self.database_url)
        try:
            yield conn
        finally:
            await conn.close()

    def measure_query_execution(self, query: str, params: Optional[Dict] = None) -> tuple[float, bool, Any]:
        """Execute query and measure performance."""
        start_time = time.time()

        try:
            with self.session_factory() as session:
                if params:
                    result = session.execute(text(query), params)
                else:
                    result = session.execute(text(query))

                # Fetch all results to ensure complete execution
                rows = result.fetchall()

                execution_time = time.time() - start_time
                return execution_time, True, rows

        except Exception as e:
            execution_time = time.time() - start_time
            return execution_time, False, str(e)

    async def measure_async_query(self, query: str, params: Optional[List] = None) -> tuple[float, bool, Any]:
        """Execute async query and measure performance."""
        start_time = time.time()

        try:
            async with self.get_async_connection() as conn:
                if params:
                    result = await conn.fetch(query, *params)
                else:
                    result = await conn.fetch(query)

                execution_time = time.time() - start_time
                return execution_time, True, result

        except Exception as e:
            execution_time = time.time() - start_time
            return execution_time, False, str(e)

    def run_concurrent_queries(self, queries: List[tuple[str, Optional[Dict]]],
                             concurrent_connections: int) -> DatabasePerformanceMetrics:
        """Run queries concurrently to test database load."""
        metrics = DatabasePerformanceMetrics()

        def execute_query_batch(query_batch):
            batch_results = []
            for query, params in query_batch:
                execution_time, success, result = self.measure_query_execution(query, params)
                metrics.add_query_result(execution_time, success)
                batch_results.append((execution_time, success, result))
            return batch_results

        # Divide queries into batches for concurrent execution
        batch_size = max(1, len(queries) // concurrent_connections)
        query_batches = [
            queries[i:i + batch_size]
            for i in range(0, len(queries), batch_size)
        ]

        # Execute batches concurrently
        with ThreadPoolExecutor(max_workers=concurrent_connections) as executor:
            futures = [executor.submit(execute_query_batch, batch) for batch in query_batches]

            # Collect results
            for future in futures:
                try:
                    future.result(timeout=30)  # 30 second timeout
                except Exception as e:
                    print(f"Batch execution failed: {e}")

        return metrics

    def monitor_connection_pool(self, duration: int):
        """Monitor connection pool statistics."""
        start_time = time.time()

        while time.time() - start_time < duration:
            if self.engine and hasattr(self.engine.pool, 'status'):
                stats = {
                    'size': self.engine.pool.size(),
                    'checked_in': self.engine.pool.checkedin(),
                    'checked_out': self.engine.pool.checkedout(),
                    'overflow': self.engine.pool.overflow(),
                    'timestamp': time.time()
                }
                self.metrics.add_pool_stats(stats)

            time.sleep(1)  # Sample every second

    def benchmark_index_effectiveness(self, table_name: str, indexed_column: str,
                                    non_indexed_column: str) -> Dict[str, float]:
        """Compare query performance with and without indexes."""
        # Query using indexed column
        indexed_query = f"SELECT * FROM {table_name} WHERE {indexed_column} = %(value)s LIMIT 100"
        indexed_time, indexed_success, _ = self.measure_query_execution(
            indexed_query, {'value': 'test_value'}
        )

        # Query using non-indexed column
        non_indexed_query = f"SELECT * FROM {table_name} WHERE {non_indexed_column} = %(value)s LIMIT 100"
        non_indexed_time, non_indexed_success, _ = self.measure_query_execution(
            non_indexed_query, {'value': 'test_value'}
        )

        return {
            'indexed_time': indexed_time,
            'non_indexed_time': non_indexed_time,
            'performance_improvement': non_indexed_time / indexed_time if indexed_time > 0 else 0,
            'indexed_success': indexed_success,
            'non_indexed_success': non_indexed_success
        }


@pytest.fixture
def db_tester():
    """Create database performance tester."""
    # Use test database URL
    database_url = "postgresql://test_user:test_pass@localhost:5432/test_fantasy_db"
    tester = DatabasePerformanceTester(database_url)
    tester.setup_engine()
    yield tester
    tester.cleanup()


class TestBasicQueryPerformance:
    """Test basic database query performance."""

    def test_simple_select_performance(self, db_tester):
        """Test simple SELECT query performance."""
        query = "SELECT id, name FROM players WHERE sport = %(sport)s LIMIT 50"
        params = {'sport': 'nfl'}

        # Run query multiple times to get average
        execution_times = []
        for _ in range(10):
            execution_time, success, result = db_tester.measure_query_execution(query, params)
            execution_times.append(execution_time)
            assert success, "Query should execute successfully"

        avg_time = statistics.mean(execution_times)
        assert avg_time < DB_PERFORMANCE_CONFIG["query_timeout_ms"] / 1000, \
            f"Average query time {avg_time:.3f}s exceeds {DB_PERFORMANCE_CONFIG['query_timeout_ms']}ms target"

        # Verify result consistency
        assert len(execution_times) == 10, "All queries should complete"

    def test_player_search_query_performance(self, db_tester):
        """Test player search query performance."""
        query = """
        SELECT p.id, p.name, p.position, p.team, p.projected_points
        FROM players p
        WHERE p.sport = %(sport)s
          AND p.position = %(position)s
          AND p.projected_points > %(min_points)s
        ORDER BY p.projected_points DESC
        LIMIT %(limit)s
        """

        params = {
            'sport': 'nfl',
            'position': 'QB',
            'min_points': 15.0,
            'limit': 20
        }

        execution_time, success, result = db_tester.measure_query_execution(query, params)

        assert success, "Player search query should execute successfully"
        assert execution_time < DB_PERFORMANCE_CONFIG["query_timeout_ms"] / 1000, \
            f"Player search took {execution_time:.3f}s, exceeds {DB_PERFORMANCE_CONFIG['query_timeout_ms']}ms target"

    def test_league_data_query_performance(self, db_tester):
        """Test league data retrieval performance."""
        query = """
        SELECT l.id, l.name, l.settings,
               COUNT(t.id) as team_count,
               MAX(d.current_pick) as draft_progress
        FROM leagues l
        LEFT JOIN teams t ON l.id = t.league_id
        LEFT JOIN drafts d ON l.id = d.league_id
        WHERE l.status = %(status)s
        GROUP BY l.id, l.name, l.settings
        ORDER BY l.created_at DESC
        LIMIT %(limit)s
        """

        params = {'status': 'active', 'limit': 10}

        execution_time, success, result = db_tester.measure_query_execution(query, params)

        assert success, "League data query should execute successfully"
        assert execution_time < DB_PERFORMANCE_CONFIG["query_timeout_ms"] / 1000, \
            f"League query took {execution_time:.3f}s, exceeds {DB_PERFORMANCE_CONFIG['query_timeout_ms']}ms target"

    def test_trade_history_query_performance(self, db_tester):
        """Test trade history query performance."""
        query = """
        SELECT t.id, t.status, t.proposed_at, t.completed_at,
               tp.team_id as proposing_team, tr.team_id as receiving_team,
               t.proposed_players, t.requested_players
        FROM trades t
        JOIN teams tp ON t.proposing_team_id = tp.id
        JOIN teams tr ON t.receiving_team_id = tr.id
        WHERE tp.league_id = %(league_id)s
        ORDER BY t.proposed_at DESC
        LIMIT %(limit)s
        """

        params = {'league_id': 'test-league-id', 'limit': 50}

        execution_time, success, result = db_tester.measure_query_execution(query, params)

        assert success, "Trade history query should execute successfully"
        assert execution_time < DB_PERFORMANCE_CONFIG["query_timeout_ms"] / 1000, \
            f"Trade history took {execution_time:.3f}s, exceeds {DB_PERFORMANCE_CONFIG['query_timeout_ms']}ms target"


class TestComplexQueryPerformance:
    """Test complex query performance (analytics, aggregations)."""

    def test_player_analytics_query_performance(self, db_tester):
        """Test player analytics query performance."""
        query = """
        SELECT
            p.id,
            p.name,
            p.position,
            AVG(s.fantasy_points) as avg_points,
            STDDEV(s.fantasy_points) as points_variance,
            COUNT(s.id) as games_played,
            MAX(s.fantasy_points) as best_game,
            MIN(s.fantasy_points) as worst_game,
            COALESCE(
                LAG(AVG(s.fantasy_points)) OVER (
                    PARTITION BY p.id
                    ORDER BY s.week
                ),
                0
            ) as previous_avg
        FROM players p
        JOIN scores s ON p.id = s.player_id
        WHERE s.season = %(season)s
          AND s.week <= %(current_week)s
          AND p.sport = %(sport)s
        GROUP BY p.id, p.name, p.position, s.week
        HAVING COUNT(s.id) >= %(min_games)s
        ORDER BY avg_points DESC
        LIMIT %(limit)s
        """

        params = {
            'season': 2024,
            'current_week': 10,
            'sport': 'nfl',
            'min_games': 5,
            'limit': 100
        }

        execution_time, success, result = db_tester.measure_query_execution(query, params)

        assert success, "Player analytics query should execute successfully"
        assert execution_time < DB_PERFORMANCE_CONFIG["complex_query_timeout_ms"] / 1000, \
            f"Analytics query took {execution_time:.3f}s, exceeds {DB_PERFORMANCE_CONFIG['complex_query_timeout_ms']}ms target"

    def test_league_standings_query_performance(self, db_tester):
        """Test league standings calculation performance."""
        query = """
        WITH weekly_scores AS (
            SELECT
                t.id as team_id,
                t.name as team_name,
                s.week,
                SUM(s.fantasy_points) as weekly_total
            FROM teams t
            JOIN lineups l ON t.id = l.team_id
            JOIN scores s ON l.players::jsonb ? s.player_id::text
            WHERE t.league_id = %(league_id)s
              AND s.season = %(season)s
              AND s.week <= %(current_week)s
            GROUP BY t.id, t.name, s.week
        ),
        team_records AS (
            SELECT
                ws1.team_id,
                ws1.team_name,
                COUNT(*) as games_played,
                SUM(CASE WHEN ws1.weekly_total > ws2.weekly_total THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN ws1.weekly_total < ws2.weekly_total THEN 1 ELSE 0 END) as losses,
                SUM(CASE WHEN ws1.weekly_total = ws2.weekly_total THEN 1 ELSE 0 END) as ties,
                SUM(ws1.weekly_total) as total_points
            FROM weekly_scores ws1
            JOIN weekly_scores ws2 ON ws1.week = ws2.week AND ws1.team_id != ws2.team_id
            GROUP BY ws1.team_id, ws1.team_name
        )
        SELECT
            team_id,
            team_name,
            wins,
            losses,
            ties,
            total_points,
            ROUND(total_points / games_played, 2) as avg_points,
            RANK() OVER (ORDER BY wins DESC, total_points DESC) as standings_rank
        FROM team_records
        ORDER BY standings_rank
        """

        params = {
            'league_id': 'test-league-id',
            'season': 2024,
            'current_week': 10
        }

        execution_time, success, result = db_tester.measure_query_execution(query, params)

        assert success, "League standings query should execute successfully"
        assert execution_time < DB_PERFORMANCE_CONFIG["complex_query_timeout_ms"] / 1000, \
            f"Standings query took {execution_time:.3f}s, exceeds {DB_PERFORMANCE_CONFIG['complex_query_timeout_ms']}ms target"

    def test_draft_analytics_query_performance(self, db_tester):
        """Test draft analytics query performance."""
        query = """
        WITH pick_values AS (
            SELECT
                dp.pick_number,
                dp.round,
                dp.team_id,
                p.position,
                AVG(s.fantasy_points) as avg_performance,
                COUNT(s.id) as games_played,
                NTILE(4) OVER (ORDER BY AVG(s.fantasy_points) DESC) as performance_quartile
            FROM draft_picks dp
            JOIN players p ON dp.player_id = p.id
            LEFT JOIN scores s ON p.id = s.player_id AND s.season = %(season)s
            WHERE dp.draft_id = %(draft_id)s
            GROUP BY dp.pick_number, dp.round, dp.team_id, p.position
        ),
        team_draft_grades AS (
            SELECT
                team_id,
                COUNT(*) as total_picks,
                AVG(avg_performance) as avg_pick_performance,
                COUNT(CASE WHEN performance_quartile = 1 THEN 1 END) as top_quartile_picks,
                COUNT(CASE WHEN performance_quartile = 4 THEN 1 END) as bottom_quartile_picks
            FROM pick_values
            GROUP BY team_id
        )
        SELECT
            tdg.*,
            RANK() OVER (ORDER BY avg_pick_performance DESC) as draft_rank,
            ROUND(
                (top_quartile_picks::float / total_picks) * 100,
                1
            ) as hit_rate_percent
        FROM team_draft_grades tdg
        ORDER BY draft_rank
        """

        params = {
            'draft_id': 'test-draft-id',
            'season': 2024
        }

        execution_time, success, result = db_tester.measure_query_execution(query, params)

        assert success, "Draft analytics query should execute successfully"
        assert execution_time < DB_PERFORMANCE_CONFIG["complex_query_timeout_ms"] / 1000, \
            f"Draft analytics took {execution_time:.3f}s, exceeds {DB_PERFORMANCE_CONFIG['complex_query_timeout_ms']}ms target"


class TestConcurrentDatabaseLoad:
    """Test database performance under concurrent load."""

    def test_concurrent_player_queries(self, db_tester):
        """Test concurrent player data queries."""
        # Create multiple query variations
        queries = []
        positions = ['QB', 'RB', 'WR', 'TE', 'K', 'DEF']

        for i in range(100):
            position = positions[i % len(positions)]
            query = "SELECT * FROM players WHERE position = %(position)s AND sport = 'nfl' LIMIT 20"
            params = {'position': position}
            queries.append((query, params))

        # Execute queries concurrently
        metrics = db_tester.run_concurrent_queries(
            queries,
            DB_PERFORMANCE_CONFIG["concurrent_connections"]
        )

        # Validate performance
        assert metrics.success_rate > 99.0, f"Success rate {metrics.success_rate:.1f}% too low"
        assert metrics.average_query_time < DB_PERFORMANCE_CONFIG["query_timeout_ms"] / 1000, \
            f"Average query time {metrics.average_query_time:.3f}s under load exceeds target"
        assert metrics.p95_query_time < (DB_PERFORMANCE_CONFIG["query_timeout_ms"] * 1.5) / 1000, \
            f"P95 query time {metrics.p95_query_time:.3f}s under load too high"

    def test_concurrent_read_write_operations(self, db_tester):
        """Test mixed read/write operations under load."""
        read_queries = [
            ("SELECT COUNT(*) FROM players WHERE sport = 'nfl'", None),
            ("SELECT * FROM leagues WHERE status = 'active' LIMIT 10", None),
            ("SELECT * FROM teams WHERE league_id = %(league_id)s", {'league_id': 'test-league'}),
        ]

        write_queries = [
            ("UPDATE players SET last_updated = NOW() WHERE id = %(player_id)s", {'player_id': f'player_{i}'})
            for i in range(10)
        ]

        # Mix read and write queries
        all_queries = read_queries * 20 + write_queries

        metrics = db_tester.run_concurrent_queries(all_queries, 20)

        # Validate mixed workload performance
        assert metrics.success_rate > 95.0, f"Mixed workload success rate {metrics.success_rate:.1f}% too low"
        assert metrics.average_query_time < 0.5, \
            f"Mixed workload average time {metrics.average_query_time:.3f}s too high"

    @pytest.mark.asyncio
    async def test_async_query_performance(self, db_tester):
        """Test async query performance."""
        query = "SELECT id, name, position FROM players WHERE sport = $1 LIMIT $2"

        # Run multiple async queries
        tasks = []
        for i in range(50):
            task = db_tester.measure_async_query(query, ['nfl', 20])
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        # Analyze results
        execution_times = [result[0] for result in results if result[1]]  # Only successful queries
        success_count = sum(1 for result in results if result[1])

        assert success_count == 50, "All async queries should succeed"

        avg_time = statistics.mean(execution_times)
        assert avg_time < DB_PERFORMANCE_CONFIG["query_timeout_ms"] / 1000, \
            f"Async query average time {avg_time:.3f}s exceeds target"


class TestIndexEffectiveness:
    """Test database index effectiveness."""

    def test_player_search_index_effectiveness(self, db_tester):
        """Test effectiveness of player search indexes."""
        # Test indexed columns vs non-indexed
        results = db_tester.benchmark_index_effectiveness(
            'players',
            'sport',  # Should be indexed
            'name'    # Might not be indexed
        )

        assert results['indexed_success'], "Indexed query should succeed"
        assert results['indexed_time'] < DB_PERFORMANCE_CONFIG["query_timeout_ms"] / 1000, \
            f"Indexed query time {results['indexed_time']:.3f}s too high"

        # Index should provide significant performance improvement
        if results['performance_improvement'] > 1:
            assert results['performance_improvement'] > 2, \
                f"Index provides minimal improvement: {results['performance_improvement']:.1f}x"

    def test_composite_index_effectiveness(self, db_tester):
        """Test composite index performance."""
        # Query using composite index (sport + position)
        composite_query = """
        SELECT * FROM players
        WHERE sport = %(sport)s AND position = %(position)s
        LIMIT 50
        """

        params = {'sport': 'nfl', 'position': 'QB'}

        execution_time, success, result = db_tester.measure_query_execution(composite_query, params)

        assert success, "Composite index query should succeed"
        assert execution_time < DB_PERFORMANCE_CONFIG["query_timeout_ms"] / 1000, \
            f"Composite index query took {execution_time:.3f}s, too slow"

    def test_join_performance_with_indexes(self, db_tester):
        """Test join query performance with proper indexes."""
        join_query = """
        SELECT p.name, p.position, s.fantasy_points, s.week
        FROM players p
        JOIN scores s ON p.id = s.player_id
        WHERE p.sport = %(sport)s
          AND s.season = %(season)s
          AND s.week = %(week)s
        ORDER BY s.fantasy_points DESC
        LIMIT 100
        """

        params = {'sport': 'nfl', 'season': 2024, 'week': 10}

        execution_time, success, result = db_tester.measure_query_execution(join_query, params)

        assert success, "Join query should succeed"
        assert execution_time < DB_PERFORMANCE_CONFIG["query_timeout_ms"] / 1000, \
            f"Join query took {execution_time:.3f}s, indexes may be missing"


class TestConnectionPoolPerformance:
    """Test connection pool performance and efficiency."""

    def test_connection_pool_efficiency(self, db_tester):
        """Test connection pool efficiency under load."""
        # Monitor pool stats during concurrent operations
        import threading

        # Start pool monitoring
        monitor_thread = threading.Thread(
            target=db_tester.monitor_connection_pool,
            args=(20,)  # Monitor for 20 seconds
        )
        monitor_thread.daemon = True
        monitor_thread.start()

        # Generate concurrent load
        queries = [
            ("SELECT COUNT(*) FROM players WHERE sport = 'nfl'", None)
            for _ in range(200)
        ]

        metrics = db_tester.run_concurrent_queries(queries, 30)

        # Wait for monitoring to complete
        monitor_thread.join(timeout=25)

        # Analyze pool efficiency
        assert metrics.success_rate > 99.0, "Pool should handle concurrent load efficiently"

        if db_tester.metrics.pool_stats:
            max_checked_out = max(stat['checked_out'] for stat in db_tester.metrics.pool_stats)
            pool_size = DB_PERFORMANCE_CONFIG["connection_pool_size"]

            assert max_checked_out <= pool_size + DB_PERFORMANCE_CONFIG["max_overflow"], \
                f"Pool exceeded expected size: {max_checked_out}"

    def test_connection_acquisition_time(self, db_tester):
        """Test connection acquisition performance."""
        acquisition_times = []

        for _ in range(50):
            start_time = time.time()

            try:
                with db_tester.session_factory() as session:
                    # Simple query to ensure connection is active
                    session.execute(text("SELECT 1"))

                acquisition_time = time.time() - start_time
                acquisition_times.append(acquisition_time)

            except Exception as e:
                pytest.fail(f"Connection acquisition failed: {e}")

        avg_acquisition_time = statistics.mean(acquisition_times)
        max_acquisition_time = max(acquisition_times)

        assert avg_acquisition_time < 0.01, \
            f"Average connection acquisition time {avg_acquisition_time:.3f}s too high"
        assert max_acquisition_time < 0.05, \
            f"Max connection acquisition time {max_acquisition_time:.3f}s too high"


class TestMemoryUsage:
    """Test database operation memory usage."""

    def test_large_result_set_memory_usage(self, db_tester):
        """Test memory usage when handling large result sets."""
        process = psutil.Process()
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Query that returns large result set
        large_query = "SELECT * FROM players LIMIT 10000"

        execution_time, success, result = db_tester.measure_query_execution(large_query)

        current_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = current_memory - baseline_memory

        assert success, "Large result set query should succeed"
        assert memory_increase < DB_PERFORMANCE_CONFIG["max_memory_increase_mb"], \
            f"Memory increased by {memory_increase:.1f}MB, exceeds {DB_PERFORMANCE_CONFIG['max_memory_increase_mb']}MB limit"

    def test_concurrent_operations_memory_stability(self, db_tester):
        """Test memory stability during concurrent operations."""
        process = psutil.Process()
        memory_samples = []

        # Monitor memory during concurrent operations
        def monitor_memory():
            for _ in range(30):  # 30 samples over test
                memory_mb = process.memory_info().rss / 1024 / 1024
                memory_samples.append(memory_mb)
                time.sleep(1)

        import threading
        monitor_thread = threading.Thread(target=monitor_memory)
        monitor_thread.daemon = True
        monitor_thread.start()

        # Run concurrent database operations
        queries = [
            ("SELECT COUNT(*) FROM players", None),
            ("SELECT * FROM leagues LIMIT 100", None),
            ("SELECT * FROM teams LIMIT 200", None),
        ] * 50

        metrics = db_tester.run_concurrent_queries(queries, 25)

        monitor_thread.join(timeout=35)

        # Analyze memory stability
        if memory_samples:
            memory_variance = statistics.stdev(memory_samples)
            max_memory = max(memory_samples)
            min_memory = min(memory_samples)
            memory_range = max_memory - min_memory

            assert memory_range < DB_PERFORMANCE_CONFIG["max_memory_increase_mb"], \
                f"Memory range {memory_range:.1f}MB too high during concurrent operations"

            assert memory_variance < 20, \
                f"Memory variance {memory_variance:.1f}MB indicates instability"


if __name__ == "__main__":
    # Run database performance tests
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--durations=10",
        "-m", "not slow"
    ])