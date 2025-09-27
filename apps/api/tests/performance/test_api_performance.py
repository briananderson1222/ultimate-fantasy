"""
API performance testing to ensure 300ms/600ms response time targets.

Tests cover:
- Sports data API endpoints (300ms target)
- Fantasy management endpoints (300ms target)
- Complex analytics endpoints (600ms target)
- Real-time WebSocket connections
- Database query performance
- Concurrent request handling
"""

import pytest
import asyncio
import time
import statistics
from typing import List, Dict, Any
import aiohttp
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import psutil
import uvloop

# Performance test configuration
PERFORMANCE_CONFIG = {
    "sports_endpoints_target": 0.3,  # 300ms for sports data
    "fantasy_endpoints_target": 0.3,  # 300ms for fantasy operations
    "analytics_endpoints_target": 0.6,  # 600ms for complex analytics
    "concurrent_users": [1, 10, 50, 100],
    "test_duration": 30,  # seconds
    "warmup_requests": 5,
    "base_url": "http://localhost:8000",
}


class PerformanceMetrics:
    """Container for performance test metrics."""

    def __init__(self):
        self.response_times: List[float] = []
        self.error_count = 0
        self.success_count = 0
        self.total_requests = 0

    def add_result(self, response_time: float, success: bool):
        """Add a result to the metrics."""
        self.response_times.append(response_time)
        self.total_requests += 1
        if success:
            self.success_count += 1
        else:
            self.error_count += 1

    @property
    def average_response_time(self) -> float:
        """Calculate average response time."""
        return statistics.mean(self.response_times) if self.response_times else 0

    @property
    def p95_response_time(self) -> float:
        """Calculate 95th percentile response time."""
        if not self.response_times:
            return 0
        sorted_times = sorted(self.response_times)
        index = int(0.95 * len(sorted_times))
        return sorted_times[index]

    @property
    def p99_response_time(self) -> float:
        """Calculate 99th percentile response time."""
        if not self.response_times:
            return 0
        sorted_times = sorted(self.response_times)
        index = int(0.99 * len(sorted_times))
        return sorted_times[index]

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_requests == 0:
            return 0
        return (self.success_count / self.total_requests) * 100


class APIPerformanceTester:
    """Performance testing framework for API endpoints."""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = None

    async def setup_session(self):
        """Set up aiohttp session with optimal settings."""
        connector = aiohttp.TCPConnector(
            limit=100,  # Total connection pool size
            limit_per_host=50,  # Per-host connection limit
            keepalive_timeout=60,
            enable_cleanup_closed=True,
        )

        timeout = aiohttp.ClientTimeout(total=10)  # 10s timeout

        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={"User-Agent": "PerformanceTest/1.0"},
        )

    async def cleanup_session(self):
        """Clean up aiohttp session."""
        if self.session:
            await self.session.close()

    async def make_request(
        self, method: str, endpoint: str, **kwargs
    ) -> tuple[float, bool, int]:
        """Make a single HTTP request and measure performance."""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()

        try:
            async with self.session.request(method, url, **kwargs) as response:
                # Read response to ensure full request completion
                await response.read()
                end_time = time.time()
                response_time = end_time - start_time

                return response_time, response.status < 400, response.status

        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time
            return response_time, False, 0

    async def load_test_endpoint(
        self,
        method: str,
        endpoint: str,
        concurrent_users: int,
        duration: int,
        **request_kwargs,
    ) -> PerformanceMetrics:
        """Run load test against a specific endpoint."""
        metrics = PerformanceMetrics()
        start_time = time.time()

        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(concurrent_users)

        async def make_concurrent_request():
            async with semaphore:
                response_time, success, status = await self.make_request(
                    method, endpoint, **request_kwargs
                )
                metrics.add_result(response_time, success)
                return response_time, success, status

        # Run requests until duration is reached
        tasks = []
        while time.time() - start_time < duration:
            # Create batch of concurrent requests
            batch_size = min(concurrent_users, 10)  # Limit batch size
            batch_tasks = [make_concurrent_request() for _ in range(batch_size)]

            # Start tasks
            tasks.extend(batch_tasks)

            # Small delay to prevent overwhelming
            await asyncio.sleep(0.01)

        # Wait for all tasks to complete
        await asyncio.gather(*tasks, return_exceptions=True)

        return metrics


@pytest.fixture
async def performance_tester():
    """Create and setup performance tester."""
    tester = APIPerformanceTester(PERFORMANCE_CONFIG["base_url"])
    await tester.setup_session()
    yield tester
    await tester.cleanup_session()


@pytest.fixture
def auth_headers():
    """Mock authentication headers for testing."""
    return {"Authorization": "Bearer test-token"}


class TestSportsDataAPIPerformance:
    """Test performance of sports data API endpoints (300ms target)."""

    @pytest.mark.asyncio
    async def test_players_search_performance(self, performance_tester, auth_headers):
        """Test GET /api/v1/sports/players performance."""
        endpoint = "/api/v1/sports/players"
        params = {"sport": "nfl", "position": "QB", "limit": 20}

        # Warmup requests
        for _ in range(PERFORMANCE_CONFIG["warmup_requests"]):
            await performance_tester.make_request(
                "GET", endpoint, params=params, headers=auth_headers
            )

        # Performance test
        metrics = await performance_tester.load_test_endpoint(
            "GET",
            endpoint,
            concurrent_users=10,
            duration=10,
            params=params,
            headers=auth_headers,
        )

        # Assertions
        assert (
            metrics.average_response_time
            < PERFORMANCE_CONFIG["sports_endpoints_target"]
        ), f"Average response time {metrics.average_response_time:.3f}s exceeds 300ms target"

        assert (
            metrics.p95_response_time
            < PERFORMANCE_CONFIG["sports_endpoints_target"] * 1.5
        ), f"95th percentile {metrics.p95_response_time:.3f}s exceeds acceptable threshold"

        assert (
            metrics.success_rate > 99.0
        ), f"Success rate {metrics.success_rate:.1f}% below 99% requirement"

    @pytest.mark.asyncio
    async def test_player_details_performance(self, performance_tester, auth_headers):
        """Test GET /api/v1/sports/players/{playerId} performance."""
        endpoint = "/api/v1/sports/players/test-player-id"

        # Warmup
        for _ in range(PERFORMANCE_CONFIG["warmup_requests"]):
            await performance_tester.make_request("GET", endpoint, headers=auth_headers)

        # Performance test
        metrics = await performance_tester.load_test_endpoint(
            "GET", endpoint, concurrent_users=20, duration=10, headers=auth_headers
        )

        assert (
            metrics.average_response_time
            < PERFORMANCE_CONFIG["sports_endpoints_target"]
        )
        assert (
            metrics.p99_response_time
            < PERFORMANCE_CONFIG["sports_endpoints_target"] * 2
        )
        assert metrics.success_rate > 99.0

    @pytest.mark.asyncio
    async def test_teams_endpoint_performance(self, performance_tester, auth_headers):
        """Test GET /api/v1/sports/teams performance."""
        endpoint = "/api/v1/sports/teams"
        params = {"sport": "nfl"}

        metrics = await performance_tester.load_test_endpoint(
            "GET",
            endpoint,
            concurrent_users=15,
            duration=10,
            params=params,
            headers=auth_headers,
        )

        assert (
            metrics.average_response_time
            < PERFORMANCE_CONFIG["sports_endpoints_target"]
        )
        assert metrics.success_rate > 99.0

    @pytest.mark.asyncio
    async def test_scores_endpoint_performance(self, performance_tester, auth_headers):
        """Test GET /api/v1/sports/scores performance."""
        endpoint = "/api/v1/sports/scores"
        params = {"sport": "nfl", "week": 10, "season": 2024}

        metrics = await performance_tester.load_test_endpoint(
            "GET",
            endpoint,
            concurrent_users=25,
            duration=15,
            params=params,
            headers=auth_headers,
        )

        assert (
            metrics.average_response_time
            < PERFORMANCE_CONFIG["sports_endpoints_target"]
        )
        assert (
            metrics.p95_response_time
            < PERFORMANCE_CONFIG["sports_endpoints_target"] * 1.3
        )


class TestFantasyAPIPerformance:
    """Test performance of fantasy management endpoints (300ms target)."""

    @pytest.mark.asyncio
    async def test_draft_operations_performance(self, performance_tester, auth_headers):
        """Test draft-related endpoint performance."""
        # Test draft status
        draft_status_metrics = await performance_tester.load_test_endpoint(
            "GET",
            "/api/v1/draft/test-league-id",
            concurrent_users=10,
            duration=10,
            headers=auth_headers,
        )

        assert (
            draft_status_metrics.average_response_time
            < PERFORMANCE_CONFIG["fantasy_endpoints_target"]
        )

        # Test making picks (POST requests)
        pick_data = {"player_id": "test-player-id", "team_id": "test-team-id"}

        pick_metrics = await performance_tester.load_test_endpoint(
            "POST",
            "/api/v1/draft/test-league-id/pick",
            concurrent_users=5,  # Lower concurrency for writes
            duration=5,
            json=pick_data,
            headers=auth_headers,
        )

        assert (
            pick_metrics.average_response_time
            < PERFORMANCE_CONFIG["fantasy_endpoints_target"]
        )

    @pytest.mark.asyncio
    async def test_trades_performance(self, performance_tester, auth_headers):
        """Test trade-related endpoint performance."""
        # GET trades
        get_metrics = await performance_tester.load_test_endpoint(
            "GET",
            "/api/v1/trades",
            concurrent_users=15,
            duration=10,
            headers=auth_headers,
        )

        assert (
            get_metrics.average_response_time
            < PERFORMANCE_CONFIG["fantasy_endpoints_target"]
        )

        # POST new trade
        trade_data = {
            "proposing_team_id": "team1",
            "receiving_team_id": "team2",
            "proposed_players": ["player1", "player2"],
            "requested_players": ["player3"],
        }

        post_metrics = await performance_tester.load_test_endpoint(
            "POST",
            "/api/v1/trades",
            concurrent_users=3,
            duration=5,
            json=trade_data,
            headers=auth_headers,
        )

        assert (
            post_metrics.average_response_time
            < PERFORMANCE_CONFIG["fantasy_endpoints_target"]
        )

    @pytest.mark.asyncio
    async def test_lineup_operations_performance(
        self, performance_tester, auth_headers
    ):
        """Test lineup management performance."""
        # GET lineup
        get_metrics = await performance_tester.load_test_endpoint(
            "GET",
            "/api/v1/lineups/test-team-id",
            concurrent_users=20,
            duration=10,
            headers=auth_headers,
        )

        assert (
            get_metrics.average_response_time
            < PERFORMANCE_CONFIG["fantasy_endpoints_target"]
        )

        # PUT lineup update
        lineup_data = {
            "players": [
                {"player_id": "qb1", "position": "QB"},
                {"player_id": "rb1", "position": "RB"},
                {"player_id": "rb2", "position": "RB"},
                {"player_id": "wr1", "position": "WR"},
                {"player_id": "wr2", "position": "WR"},
                {"player_id": "te1", "position": "TE"},
                {"player_id": "k1", "position": "K"},
                {"player_id": "def1", "position": "DEF"},
            ]
        }

        put_metrics = await performance_tester.load_test_endpoint(
            "PUT",
            "/api/v1/lineups/test-team-id",
            concurrent_users=5,
            duration=5,
            json=lineup_data,
            headers=auth_headers,
        )

        assert (
            put_metrics.average_response_time
            < PERFORMANCE_CONFIG["fantasy_endpoints_target"]
        )


class TestAnalyticsAPIPerformance:
    """Test performance of analytics endpoints (600ms target)."""

    @pytest.mark.asyncio
    async def test_recommendations_performance(self, performance_tester, auth_headers):
        """Test GET /api/v1/analytics/recommendations performance."""
        endpoint = "/api/v1/analytics/recommendations"
        params = {"team_id": "test-team-id", "type": "lineup"}

        metrics = await performance_tester.load_test_endpoint(
            "GET",
            endpoint,
            concurrent_users=5,  # Lower concurrency for complex operations
            duration=15,
            params=params,
            headers=auth_headers,
        )

        assert (
            metrics.average_response_time
            < PERFORMANCE_CONFIG["analytics_endpoints_target"]
        ), f"Analytics recommendations average time {metrics.average_response_time:.3f}s exceeds 600ms target"

        assert (
            metrics.p95_response_time
            < PERFORMANCE_CONFIG["analytics_endpoints_target"] * 1.5
        )
        assert metrics.success_rate > 95.0  # Slightly lower for complex operations

    @pytest.mark.asyncio
    async def test_insights_performance(self, performance_tester, auth_headers):
        """Test GET /api/v1/analytics/insights performance."""
        endpoint = "/api/v1/analytics/insights"
        params = {"team_id": "test-team-id", "timeframe": "season"}

        metrics = await performance_tester.load_test_endpoint(
            "GET",
            endpoint,
            concurrent_users=3,
            duration=10,
            params=params,
            headers=auth_headers,
        )

        assert (
            metrics.average_response_time
            < PERFORMANCE_CONFIG["analytics_endpoints_target"]
        )
        assert metrics.success_rate > 95.0


class TestConcurrencyPerformance:
    """Test API performance under various concurrency levels."""

    @pytest.mark.asyncio
    async def test_scalability_under_load(self, performance_tester, auth_headers):
        """Test how performance scales with concurrent users."""
        endpoint = "/api/v1/sports/players"
        params = {"sport": "nfl", "limit": 10}
        results = {}

        for concurrent_users in PERFORMANCE_CONFIG["concurrent_users"]:
            metrics = await performance_tester.load_test_endpoint(
                "GET",
                endpoint,
                concurrent_users=concurrent_users,
                duration=10,
                params=params,
                headers=auth_headers,
            )

            results[concurrent_users] = {
                "avg_time": metrics.average_response_time,
                "p95_time": metrics.p95_response_time,
                "success_rate": metrics.success_rate,
            }

        # Verify performance doesn't degrade significantly
        baseline = results[1]["avg_time"]
        for users, result in results.items():
            if users > 1:
                # Response time shouldn't increase more than 3x baseline
                assert (
                    result["avg_time"] < baseline * 3
                ), f"Response time degraded too much at {users} users: {result['avg_time']:.3f}s"

                # Success rate should remain high
                assert (
                    result["success_rate"] > 95.0
                ), f"Success rate too low at {users} users: {result['success_rate']:.1f}%"

    @pytest.mark.asyncio
    async def test_mixed_workload_performance(self, performance_tester, auth_headers):
        """Test performance with mixed read/write operations."""
        # Define mixed workload
        operations = [
            ("GET", "/api/v1/sports/players", {"params": {"sport": "nfl"}}),
            ("GET", "/api/v1/trades", {}),
            (
                "POST",
                "/api/v1/trades",
                {
                    "json": {
                        "proposing_team_id": "team1",
                        "receiving_team_id": "team2",
                        "proposed_players": ["p1"],
                        "requested_players": ["p2"],
                    }
                },
            ),
            ("GET", "/api/v1/lineups/test-team", {}),
            (
                "GET",
                "/api/v1/analytics/recommendations",
                {"params": {"team_id": "test-team"}},
            ),
        ]

        async def run_mixed_operation():
            import random

            method, endpoint, kwargs = random.choice(operations)
            return await performance_tester.make_request(
                method, endpoint, headers=auth_headers, **kwargs
            )

        # Run mixed workload
        start_time = time.time()
        tasks = []

        while time.time() - start_time < 20:  # 20 second test
            # Launch 10 concurrent mixed operations
            batch_tasks = [run_mixed_operation() for _ in range(10)]
            tasks.extend(batch_tasks)
            await asyncio.sleep(0.1)  # Small delay between batches

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Analyze results
        successful_results = [r for r in results if isinstance(r, tuple) and r[1]]
        response_times = [r[0] for r in successful_results]

        if response_times:
            avg_time = statistics.mean(response_times)
            success_rate = (len(successful_results) / len(results)) * 100

            assert (
                avg_time < 0.8
            ), f"Mixed workload average time {avg_time:.3f}s too high"
            assert (
                success_rate > 95.0
            ), f"Mixed workload success rate {success_rate:.1f}% too low"


class TestResourceUtilization:
    """Test resource utilization during performance tests."""

    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self, performance_tester, auth_headers):
        """Monitor memory usage during load testing."""
        import psutil

        process = psutil.Process()

        # Get baseline memory
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Run load test
        await performance_tester.load_test_endpoint(
            "GET",
            "/api/v1/sports/players",
            concurrent_users=50,
            duration=15,
            params={"sport": "nfl"},
            headers=auth_headers,
        )

        # Check memory after load test
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - baseline_memory

        # Memory shouldn't increase by more than 100MB during test
        assert (
            memory_increase < 100
        ), f"Memory increased by {memory_increase:.1f}MB during load test"

    @pytest.mark.asyncio
    async def test_cpu_utilization(self, performance_tester, auth_headers):
        """Monitor CPU utilization during testing."""
        import psutil

        # Monitor CPU during load test
        cpu_samples = []

        async def monitor_cpu():
            for _ in range(15):  # 15 seconds of monitoring
                cpu_samples.append(psutil.cpu_percent(interval=1))

        # Run monitoring and load test concurrently
        monitor_task = asyncio.create_task(monitor_cpu())

        load_task = asyncio.create_task(
            performance_tester.load_test_endpoint(
                "GET",
                "/api/v1/sports/players",
                concurrent_users=30,
                duration=15,
                params={"sport": "nfl"},
                headers=auth_headers,
            )
        )

        await asyncio.gather(monitor_task, load_task)

        # Analyze CPU usage
        avg_cpu = statistics.mean(cpu_samples)
        max_cpu = max(cpu_samples)

        # CPU usage should be reasonable
        assert avg_cpu < 80.0, f"Average CPU usage {avg_cpu:.1f}% too high"
        assert max_cpu < 95.0, f"Peak CPU usage {max_cpu:.1f}% too high"


# Test configuration and utilities
@pytest.mark.asyncio
async def test_performance_test_environment():
    """Verify the performance test environment is properly configured."""
    # Check if uvloop is available for better async performance
    try:
        import uvloop

        uvloop.install()
    except ImportError:
        pytest.skip("uvloop not available - consider installing for better performance")

    # Check system resources
    import psutil

    # Verify sufficient memory
    memory = psutil.virtual_memory()
    assert (
        memory.available > 1024 * 1024 * 1024
    ), "Insufficient memory for performance testing"

    # Verify CPU cores
    cpu_count = psutil.cpu_count()
    assert cpu_count >= 2, "Insufficient CPU cores for concurrent testing"


if __name__ == "__main__":
    # Run performance tests with detailed output
    pytest.main(
        [
            __file__,
            "-v",
            "--tb=short",
            "--durations=10",
            "-m",
            "not slow",  # Skip slow tests in normal runs
        ]
    )
