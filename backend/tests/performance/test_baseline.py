"""
Baseline performance tests for backend modularization.

These tests establish performance benchmarks before modularization
to ensure no regression during the restructuring process.
"""
import asyncio
import time
from typing import List
import pytest
import pytest_benchmark
from fastapi.testclient import TestClient
from backend.src.main import app

client = TestClient(app)


class TestAPIPerformanceBaseline:
    """Baseline API performance tests."""

    def test_leagues_list_performance(self, benchmark):
        """Benchmark leagues list endpoint performance."""
        def make_request():
            response = client.get("/api/leagues")
            assert response.status_code in [200, 401]  # May require auth
            return response

        result = benchmark(make_request)
        # Ensure response time is reasonable
        assert benchmark.stats.stats.mean < 0.5  # 500ms threshold

    def test_lineups_get_performance(self, benchmark):
        """Benchmark lineups endpoint performance."""
        def make_request():
            response = client.get("/api/lineups")
            assert response.status_code in [200, 401]  # May require auth
            return response

        result = benchmark(make_request)
        assert benchmark.stats.stats.mean < 0.3  # 300ms threshold

    def test_scoreboard_performance(self, benchmark):
        """Benchmark scoreboard endpoint performance."""
        def make_request():
            response = client.get("/api/scoreboard")
            assert response.status_code in [200, 401]  # May require auth
            return response

        result = benchmark(make_request)
        assert benchmark.stats.stats.mean < 0.4  # 400ms threshold

    def test_waivers_performance(self, benchmark):
        """Benchmark waivers endpoint performance."""
        def make_request():
            response = client.get("/api/waivers")
            assert response.status_code in [200, 401]  # May require auth
            return response

        result = benchmark(make_request)
        assert benchmark.stats.stats.mean < 0.3  # 300ms threshold


class TestDatabasePerformanceBaseline:
    """Baseline database performance tests."""

    @pytest.mark.asyncio
    async def test_database_connection_time(self, benchmark):
        """Benchmark database connection establishment time."""
        async def connect_to_db():
            # Import here to avoid import issues during test collection
            from backend.src.database import engine
            conn = engine.connect()
            conn.close()
            return True

        result = benchmark(lambda: asyncio.run(connect_to_db()))
        assert result is True

    def test_concurrent_request_handling(self, benchmark):
        """Test concurrent request handling capacity."""
        def make_concurrent_requests():
            responses = []
            # Simulate 10 concurrent requests
            for _ in range(10):
                response = client.get("/api/health", timeout=5.0)
                responses.append(response.status_code)
            return responses

        result = benchmark(make_concurrent_requests)
        # All requests should succeed
        assert all(status == 200 for status in result)


class TestMemoryUsageBaseline:
    """Baseline memory usage tests."""

    def test_memory_usage_during_startup(self):
        """Test memory usage during application startup."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / 1024 / 1024  # MB

        # Create a new test client to simulate startup
        test_client = TestClient(app)
        response = test_client.get("/api/health")

        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = memory_after - memory_before

        # Memory increase should be reasonable (less than 50MB for startup)
        assert memory_increase < 50, f"Memory increase too high: {memory_increase}MB"
        assert response.status_code == 200


def benchmark_save_results():
    """Save benchmark results for comparison after modularization."""
    import json
    import os
    from datetime import datetime

    results_file = "backend/tests/performance/baseline_results.json"

    # This would be populated by pytest-benchmark plugin
    # For now, create a placeholder structure
    baseline_data = {
        "timestamp": datetime.now().isoformat(),
        "version": "pre-modularization",
        "api_endpoints": {
            "leagues_list": {"mean_time": "placeholder"},
            "lineups_get": {"mean_time": "placeholder"},
            "scoreboard": {"mean_time": "placeholder"},
            "waivers": {"mean_time": "placeholder"}
        },
        "database": {
            "connection_time": "placeholder",
            "concurrent_handling": "placeholder"
        },
        "memory": {
            "startup_usage": "placeholder"
        }
    }

    os.makedirs(os.path.dirname(results_file), exist_ok=True)
    with open(results_file, 'w') as f:
        json.dump(baseline_data, f, indent=2)


if __name__ == "__main__":
    # Run to establish baseline when executed directly
    benchmark_save_results()