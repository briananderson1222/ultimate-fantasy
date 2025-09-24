"""
WebSocket load testing to ensure 1000+ concurrent connections performance.

Tests cover:
- Connection establishment and teardown
- Message broadcasting performance
- Draft room real-time updates
- Trade notification delivery
- Memory usage under high load
- Connection stability over time
"""

import asyncio
import json
import time
import statistics
import websockets
import pytest
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
import psutil
import gc
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# WebSocket performance test configuration
WEBSOCKET_CONFIG = {
    "base_url": "ws://localhost:8000",
    "target_concurrent_connections": 1000,
    "connection_establishment_timeout": 5.0,
    "message_response_timeout": 2.0,
    "test_duration": 60,  # seconds
    "heartbeat_interval": 30,
    "max_memory_usage_mb": 500,
    "target_throughput_messages_per_second": 10000
}

@dataclass
class WebSocketMetrics:
    """Container for WebSocket performance metrics."""
    connection_times: List[float] = field(default_factory=list)
    message_latencies: List[float] = field(default_factory=list)
    failed_connections: int = 0
    successful_connections: int = 0
    messages_sent: int = 0
    messages_received: int = 0
    disconnections: int = 0
    memory_samples: List[float] = field(default_factory=list)

    @property
    def connection_success_rate(self) -> float:
        """Calculate connection success rate as percentage."""
        total = self.successful_connections + self.failed_connections
        if total == 0:
            return 0
        return (self.successful_connections / total) * 100

    @property
    def average_connection_time(self) -> float:
        """Calculate average connection establishment time."""
        return statistics.mean(self.connection_times) if self.connection_times else 0

    @property
    def average_message_latency(self) -> float:
        """Calculate average message latency."""
        return statistics.mean(self.message_latencies) if self.message_latencies else 0

    @property
    def p95_message_latency(self) -> float:
        """Calculate 95th percentile message latency."""
        if not self.message_latencies:
            return 0
        sorted_latencies = sorted(self.message_latencies)
        index = int(0.95 * len(sorted_latencies))
        return sorted_latencies[index]

    @property
    def throughput_messages_per_second(self) -> float:
        """Calculate message throughput."""
        if not self.message_latencies:
            return 0
        test_duration = max(self.message_latencies) - min(self.message_latencies)
        return self.messages_received / test_duration if test_duration > 0 else 0


class WebSocketLoadTester:
    """WebSocket load testing framework."""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.metrics = WebSocketMetrics()
        self.active_connections: List[websockets.WebSocketServerProtocol] = []
        self.running = False

    async def create_connection(self, endpoint: str, headers: Optional[Dict] = None) -> tuple[Optional[websockets.WebSocketServerProtocol], float]:
        """Create a single WebSocket connection and measure time."""
        uri = f"{self.base_url}{endpoint}"
        start_time = time.time()

        try:
            websocket = await websockets.connect(
                uri,
                extra_headers=headers or {},
                ping_interval=WEBSOCKET_CONFIG["heartbeat_interval"],
                ping_timeout=10,
                close_timeout=5,
                max_size=2**20,  # 1MB max message size
                max_queue=100    # Message queue size
            )

            connection_time = time.time() - start_time
            self.metrics.connection_times.append(connection_time)
            self.metrics.successful_connections += 1

            return websocket, connection_time

        except Exception as e:
            connection_time = time.time() - start_time
            self.metrics.connection_times.append(connection_time)
            self.metrics.failed_connections += 1
            logger.error(f"Connection failed: {e}")
            return None, connection_time

    async def send_message_and_measure(self, websocket: websockets.WebSocketServerProtocol, message: dict) -> float:
        """Send message and measure response latency."""
        start_time = time.time()

        try:
            await websocket.send(json.dumps(message))
            self.metrics.messages_sent += 1

            # Wait for response
            response = await asyncio.wait_for(
                websocket.recv(),
                timeout=WEBSOCKET_CONFIG["message_response_timeout"]
            )

            latency = time.time() - start_time
            self.metrics.message_latencies.append(latency)
            self.metrics.messages_received += 1

            return latency

        except asyncio.TimeoutError:
            latency = time.time() - start_time
            self.metrics.message_latencies.append(latency)
            logger.warning("Message response timeout")
            return latency

        except Exception as e:
            latency = time.time() - start_time
            self.metrics.message_latencies.append(latency)
            logger.error(f"Message send failed: {e}")
            return latency

    async def maintain_connection(self, websocket: websockets.WebSocketServerProtocol,
                                connection_id: int, duration: int):
        """Maintain a WebSocket connection and simulate realistic usage."""
        try:
            end_time = time.time() + duration

            while time.time() < end_time and self.running:
                # Simulate different types of messages
                message_types = [
                    {"type": "draft_update", "data": {"pick": connection_id, "player": f"player_{connection_id}"}},
                    {"type": "trade_notification", "data": {"trade_id": f"trade_{connection_id}"}},
                    {"type": "score_update", "data": {"player_id": f"player_{connection_id}", "points": 15.5}},
                    {"type": "heartbeat", "timestamp": time.time()}
                ]

                # Send a random message
                import random
                message = random.choice(message_types)
                await self.send_message_and_measure(websocket, message)

                # Wait between messages (simulate realistic usage)
                await asyncio.sleep(random.uniform(1.0, 5.0))

        except websockets.exceptions.ConnectionClosed:
            self.metrics.disconnections += 1
            logger.info(f"Connection {connection_id} closed")

        except Exception as e:
            self.metrics.disconnections += 1
            logger.error(f"Connection {connection_id} error: {e}")

        finally:
            if websocket and not websocket.closed:
                await websocket.close()

    async def monitor_system_resources(self, duration: int):
        """Monitor system resource usage during load test."""
        process = psutil.Process()
        end_time = time.time() + duration

        while time.time() < end_time and self.running:
            # Sample memory usage
            memory_mb = process.memory_info().rss / 1024 / 1024
            self.metrics.memory_samples.append(memory_mb)

            await asyncio.sleep(1)  # Sample every second

    async def run_connection_load_test(self, endpoint: str, target_connections: int,
                                     duration: int, headers: Optional[Dict] = None):
        """Run load test with specified number of concurrent connections."""
        logger.info(f"Starting WebSocket load test: {target_connections} connections for {duration}s")

        self.running = True
        tasks = []

        # Start resource monitoring
        monitor_task = asyncio.create_task(self.monitor_system_resources(duration))
        tasks.append(monitor_task)

        # Establish connections in batches to avoid overwhelming the server
        batch_size = 50
        connection_tasks = []

        for i in range(0, target_connections, batch_size):
            batch_end = min(i + batch_size, target_connections)
            batch_connections = []

            # Create batch of connections
            for conn_id in range(i, batch_end):
                websocket, _ = await self.create_connection(endpoint, headers)
                if websocket:
                    batch_connections.append(websocket)
                    # Start maintaining the connection
                    task = asyncio.create_task(
                        self.maintain_connection(websocket, conn_id, duration)
                    )
                    connection_tasks.append(task)

            # Small delay between batches
            await asyncio.sleep(0.1)

            logger.info(f"Established {len(batch_connections)} connections (total: {len(connection_tasks)})")

        # Wait for test duration
        await asyncio.sleep(duration)

        # Stop the test
        self.running = False

        # Cancel all connection tasks
        for task in connection_tasks:
            task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*connection_tasks, return_exceptions=True)
        await asyncio.gather(monitor_task, return_exceptions=True)

        logger.info("WebSocket load test completed")


@pytest.fixture
async def websocket_tester():
    """Create WebSocket load tester."""
    tester = WebSocketLoadTester(WEBSOCKET_CONFIG["base_url"])
    yield tester
    # Cleanup
    tester.running = False


class TestWebSocketConnectionLoad:
    """Test WebSocket connection establishment under load."""

    @pytest.mark.asyncio
    async def test_connection_establishment_performance(self, websocket_tester):
        """Test how quickly connections can be established."""
        endpoint = "/ws/draft/test-league"
        target_connections = 100

        start_time = time.time()

        # Establish connections rapidly
        tasks = []
        for i in range(target_connections):
            task = asyncio.create_task(
                websocket_tester.create_connection(endpoint)
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time

        # Analyze results
        successful_connections = sum(1 for result in results if isinstance(result, tuple) and result[0] is not None)
        connection_rate = successful_connections / total_time

        # Assertions
        assert websocket_tester.metrics.connection_success_rate > 95.0, \
            f"Connection success rate {websocket_tester.metrics.connection_success_rate:.1f}% too low"

        assert websocket_tester.metrics.average_connection_time < WEBSOCKET_CONFIG["connection_establishment_timeout"], \
            f"Average connection time {websocket_tester.metrics.average_connection_time:.3f}s too high"

        assert connection_rate > 20, \
            f"Connection establishment rate {connection_rate:.1f} connections/sec too low"

        # Close connections
        for result in results:
            if isinstance(result, tuple) and result[0] is not None:
                await result[0].close()

    @pytest.mark.asyncio
    async def test_concurrent_connection_limits(self, websocket_tester):
        """Test maximum concurrent connection capacity."""
        endpoint = "/ws/draft/test-league"
        target_connections = WEBSOCKET_CONFIG["target_concurrent_connections"]

        await websocket_tester.run_connection_load_test(
            endpoint, target_connections, duration=30
        )

        # Verify high connection success rate
        assert websocket_tester.metrics.connection_success_rate > 90.0, \
            f"Failed to maintain high success rate with {target_connections} connections"

        # Verify acceptable connection times
        assert websocket_tester.metrics.average_connection_time < 2.0, \
            f"Connection time {websocket_tester.metrics.average_connection_time:.3f}s too high under load"

        # Verify memory usage is reasonable
        if websocket_tester.metrics.memory_samples:
            max_memory = max(websocket_tester.metrics.memory_samples)
            assert max_memory < WEBSOCKET_CONFIG["max_memory_usage_mb"], \
                f"Memory usage {max_memory:.1f}MB exceeded limit"


class TestWebSocketMessageThroughput:
    """Test WebSocket message handling performance."""

    @pytest.mark.asyncio
    async def test_draft_room_broadcast_performance(self, websocket_tester):
        """Test performance of draft room message broadcasting."""
        endpoint = "/ws/draft/test-league"
        num_connections = 200

        # Establish connections
        connections = []
        for i in range(num_connections):
            websocket, _ = await websocket_tester.create_connection(endpoint)
            if websocket:
                connections.append(websocket)

        logger.info(f"Established {len(connections)} connections for broadcast test")

        # Test broadcast performance
        start_time = time.time()
        broadcast_message = {
            "type": "draft_pick",
            "data": {
                "pick_number": 42,
                "team_id": "team1",
                "player_id": "player123",
                "player_name": "Test Player",
                "timestamp": time.time()
            }
        }

        # Send broadcast message and measure response times
        send_tasks = []
        for websocket in connections:
            task = asyncio.create_task(
                websocket_tester.send_message_and_measure(websocket, broadcast_message)
            )
            send_tasks.append(task)

        latencies = await asyncio.gather(*send_tasks, return_exceptions=True)
        total_time = time.time() - start_time

        # Analyze performance
        successful_latencies = [l for l in latencies if isinstance(l, float)]
        throughput = len(successful_latencies) / total_time

        assert len(successful_latencies) > num_connections * 0.9, \
            f"Too many failed message deliveries: {len(successful_latencies)}/{num_connections}"

        assert statistics.mean(successful_latencies) < 1.0, \
            f"Average broadcast latency {statistics.mean(successful_latencies):.3f}s too high"

        assert throughput > 100, \
            f"Broadcast throughput {throughput:.1f} messages/sec too low"

        # Close connections
        for websocket in connections:
            await websocket.close()

    @pytest.mark.asyncio
    async def test_real_time_score_updates(self, websocket_tester):
        """Test real-time score update performance."""
        endpoint = "/ws/scores/live"
        num_connections = 500

        # Establish connections
        connections = []
        for i in range(num_connections):
            websocket, _ = await websocket_tester.create_connection(endpoint)
            if websocket:
                connections.append(websocket)

        # Simulate rapid score updates
        num_updates = 1000
        score_updates = []

        for i in range(num_updates):
            update = {
                "type": "score_update",
                "data": {
                    "player_id": f"player_{i % 100}",
                    "points": round(15.5 + (i % 20), 1),
                    "game_id": f"game_{i % 10}",
                    "timestamp": time.time()
                }
            }
            score_updates.append(update)

        # Send updates and measure performance
        start_time = time.time()
        update_tasks = []

        for update in score_updates:
            # Send to random subset of connections
            import random
            target_connections = random.sample(connections, min(50, len(connections)))

            for websocket in target_connections:
                task = asyncio.create_task(
                    websocket_tester.send_message_and_measure(websocket, update)
                )
                update_tasks.append(task)

        results = await asyncio.gather(*update_tasks, return_exceptions=True)
        total_time = time.time() - start_time

        # Analyze results
        successful_updates = sum(1 for r in results if isinstance(r, float))
        update_rate = successful_updates / total_time

        assert update_rate > WEBSOCKET_CONFIG["target_throughput_messages_per_second"] * 0.5, \
            f"Score update rate {update_rate:.1f} messages/sec below target"

        # Close connections
        for websocket in connections:
            await websocket.close()

    @pytest.mark.asyncio
    async def test_trade_notification_delivery(self, websocket_tester):
        """Test trade notification delivery performance."""
        endpoint = "/ws/notifications/test-user"

        # Test individual notification delivery speed
        websocket, _ = await websocket_tester.create_connection(endpoint)
        assert websocket is not None

        # Send multiple notifications and measure latency
        notifications = []
        for i in range(100):
            notification = {
                "type": "trade_proposal",
                "data": {
                    "trade_id": f"trade_{i}",
                    "from_team": "team1",
                    "to_team": "team2",
                    "proposed_players": [f"player_{i}"],
                    "requested_players": [f"player_{i+100}"],
                    "timestamp": time.time()
                }
            }
            notifications.append(notification)

        # Send notifications
        latencies = []
        for notification in notifications:
            latency = await websocket_tester.send_message_and_measure(websocket, notification)
            latencies.append(latency)

        # Verify notification delivery performance
        avg_latency = statistics.mean(latencies)
        p95_latency = sorted(latencies)[int(0.95 * len(latencies))]

        assert avg_latency < 0.1, f"Average notification latency {avg_latency:.3f}s too high"
        assert p95_latency < 0.2, f"P95 notification latency {p95_latency:.3f}s too high"

        await websocket.close()


class TestWebSocketStabilityAndResilience:
    """Test WebSocket connection stability and error handling."""

    @pytest.mark.asyncio
    async def test_connection_stability_over_time(self, websocket_tester):
        """Test WebSocket connections remain stable over extended periods."""
        endpoint = "/ws/draft/test-league"
        num_connections = 100
        test_duration = 120  # 2 minutes

        # Establish long-running connections
        await websocket_tester.run_connection_load_test(
            endpoint, num_connections, test_duration
        )

        # Verify connection stability
        disconnection_rate = websocket_tester.metrics.disconnections / websocket_tester.metrics.successful_connections

        assert disconnection_rate < 0.05, \
            f"Disconnection rate {disconnection_rate:.2%} too high for long-running test"

        assert websocket_tester.metrics.average_message_latency < 0.5, \
            f"Message latency degraded over time: {websocket_tester.metrics.average_message_latency:.3f}s"

    @pytest.mark.asyncio
    async def test_reconnection_handling(self, websocket_tester):
        """Test automatic reconnection behavior."""
        endpoint = "/ws/draft/test-league"

        # Establish connection
        websocket, _ = await websocket_tester.create_connection(endpoint)
        assert websocket is not None

        # Send initial message
        initial_message = {"type": "join_room", "room_id": "test-league"}
        await websocket_tester.send_message_and_measure(websocket, initial_message)

        # Force disconnect
        await websocket.close()

        # Attempt reconnection
        websocket2, reconnect_time = await websocket_tester.create_connection(endpoint)
        assert websocket2 is not None

        # Verify reconnection is fast
        assert reconnect_time < 2.0, f"Reconnection took too long: {reconnect_time:.3f}s"

        # Send message on new connection
        reconnect_message = {"type": "rejoin_room", "room_id": "test-league"}
        latency = await websocket_tester.send_message_and_measure(websocket2, reconnect_message)

        assert latency < 0.5, f"Post-reconnection message latency too high: {latency:.3f}s"

        await websocket2.close()

    @pytest.mark.asyncio
    async def test_malformed_message_handling(self, websocket_tester):
        """Test handling of malformed messages."""
        endpoint = "/ws/draft/test-league"

        websocket, _ = await websocket_tester.create_connection(endpoint)
        assert websocket is not None

        # Send malformed messages
        malformed_messages = [
            "not json",
            '{"incomplete": json',
            '{"type": "unknown_type"}',
            '{"data": "missing type"}',
            '{"type": null, "data": null}',
        ]

        for message in malformed_messages:
            try:
                await websocket.send(message)
                # Connection should remain stable
                response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                # Should receive error response
                assert "error" in response.lower()

            except Exception as e:
                # Connection shouldn't be terminated by malformed messages
                assert not isinstance(e, websockets.exceptions.ConnectionClosed)

        # Verify connection is still functional
        valid_message = {"type": "heartbeat", "timestamp": time.time()}
        latency = await websocket_tester.send_message_and_measure(websocket, valid_message)
        assert latency < 1.0, "Connection degraded after malformed messages"

        await websocket.close()


class TestWebSocketMemoryAndResourceUsage:
    """Test memory usage and resource management under load."""

    @pytest.mark.asyncio
    async def test_memory_usage_with_many_connections(self, websocket_tester):
        """Test memory usage remains reasonable with many connections."""
        endpoint = "/ws/draft/test-league"
        target_connections = 500

        # Run load test with memory monitoring
        await websocket_tester.run_connection_load_test(
            endpoint, target_connections, duration=60
        )

        # Analyze memory usage
        if websocket_tester.metrics.memory_samples:
            max_memory = max(websocket_tester.metrics.memory_samples)
            avg_memory = statistics.mean(websocket_tester.metrics.memory_samples)

            assert max_memory < WEBSOCKET_CONFIG["max_memory_usage_mb"], \
                f"Peak memory usage {max_memory:.1f}MB exceeded limit"

            # Memory usage should be relatively stable
            memory_variance = statistics.stdev(websocket_tester.metrics.memory_samples)
            assert memory_variance < 50, f"Memory usage too volatile: {memory_variance:.1f}MB variance"

    @pytest.mark.asyncio
    async def test_garbage_collection_effectiveness(self, websocket_tester):
        """Test that closed connections are properly garbage collected."""
        endpoint = "/ws/draft/test-league"

        # Get baseline memory
        gc.collect()
        baseline_memory = psutil.Process().memory_info().rss / 1024 / 1024

        # Create and close many connections
        for batch in range(5):
            connections = []

            # Create 100 connections
            for i in range(100):
                websocket, _ = await websocket_tester.create_connection(endpoint)
                if websocket:
                    connections.append(websocket)

            # Close all connections
            for websocket in connections:
                await websocket.close()

            # Force garbage collection
            gc.collect()
            await asyncio.sleep(1)  # Allow cleanup

        # Check final memory
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_increase = final_memory - baseline_memory

        # Memory increase should be minimal after cleanup
        assert memory_increase < 50, \
            f"Memory leaked {memory_increase:.1f}MB after connection cleanup"


if __name__ == "__main__":
    # Run WebSocket load tests
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--durations=10",
        "-s"  # Show output for monitoring
    ])